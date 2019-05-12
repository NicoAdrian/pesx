import struct
import sys

with open(sys.argv[1], "rb") as fd:
    while True:
        pkt = fd.read(188)
        if not pkt:
            break
        try:
            pkt_header = struct.unpack(">I", pkt[:4])[0]
        except:
            break
        sync = pkt_header >> 24 == 0x47
        afc = (pkt_header >> 4) & 0x3 == 0b10 or (pkt_header >> 4) & 0x3 == 0b11
        payload = (pkt_header >> 4) & 0x3 == 0b01 or (pkt_header >> 4) & 0x3 == 0b11
        dat = pkt[4:]
        if not sync:
            print("No sync byte !")
            break
        if not payload:
            pass
        elif not afc:
            print(dat)
        else:
            print(dat[dat[0] + 1 :])
