#!/usr/bin/env python3
from sys import argv, stdout
from struct import unpack


class TSPacket:
    def __init__(self, pkt):
        self.header = pkt[:4]
        _header = unpack(">I", self.header)[0]
        assert (_header >> 24) == 0x47, "no sync byte"
        self.pusi = (_header >> 22) & 1
        self.has_afc = (_header >> 4) & 0x3 == 2 or (_header >> 4) & 0x3 == 3
        self.has_payload = (_header >> 4) & 0x3 == 1 or (_header >> 4) & 0x3 == 3
        self.cc = _header & 0xF
        self.afc = b""
        self.payload = b""
        _data = pkt[4:]
        if self.has_afc:
            self.afc = _data[: _data[0] + 1]
        if self.has_payload:
            if not self.has_afc:
                self.payload = _data
            else:
                self.payload = _data[_data[0] + 1 :]

    @property
    def content(self):
        return self.header + self.afc + self.payload


class PESPacket:
    def __init__(self, ts_pkt):
        self.ts_pkt = ts_pkt
        self.specified_length = unpack(">H", ts_pkt.payload[4:6])[0]
        self.length = len(ts_pkt.payload) if self.specified_length == 0 else self.specified_length + 6
        self.header = b""
        self.data = b""
        self.bytes = b""

    @property
    def content(self):
        return self.header + self.data


def main():
    assert len(argv) > 1, "missing path to ts file"
    buffer = 0
    ts_pkts = []
    pes_pkts = []
    with open(argv[1], "rb") as fd:
        while True:
            pkt = fd.read(188)
            if not pkt or len(pkt) < 4:
                break
            ts_pkt = TSPacket(pkt)
            ts_pkts.append(ts_pkt)
            if ts_pkt.has_payload:
                if ts_pkt.pusi and ts_pkt.payload[:3] == b"\x00\x00\x01":
                    pes_pkt = PESPacket(ts_pkt)
                    pes_pkts.append(pes_pkt)
                    buffer = pes_pkt.length
                if buffer > 0:
                    to_write = ts_pkt.payload[:buffer]
                    if pes_pkt.specified_length != 0:
                        buffer -= len(to_write)
                    pes_pkt.bytes += to_write
    for pes in pes_pkts:
        base_header = pes.bytes[:9]
        pes.header = base_header + pes.bytes[9 : 9 + base_header[-1]]
        pes.data = pes.bytes[len(pes.header) :]
        stdout.buffer.write(pes.content)


if __name__ == "__main__":
    main()
