#!/usr/bin/env python3
# dump_l7.py — Hexdump CCSDS Space Packets (L7 only, no L2 frame length needed)
import sys, argparse

def parse_primary_header(hdr: bytes):
    if len(hdr) < 6:
        raise ValueError("Need at least 6 bytes for CCSDS primary header")
    w1 = (hdr[0] << 8) | hdr[1]
    w2 = (hdr[2] << 8) | hdr[3]
    w3 = (hdr[4] << 8) | hdr[5]

    version = (w1 >> 13) & 0x7
    pkt_type = (w1 >> 12) & 0x1           # 0=TM, 1=TC
    sec_hdr_flag = (w1 >> 11) & 0x1
    apid = w1 & 0x7FF

    seq_flags = (w2 >> 14) & 0x3          # 11=standalone
    seq_count = w2 & 0x3FFF

    data_field_len = w3                    # value = (data_field_bytes - 1)
    total_len = 6 + (data_field_len + 1)  # full packet bytes, including 6B hdr

    return {
        "version": version,
        "type": pkt_type,
        "sec_hdr": sec_hdr_flag,
        "apid": apid,
        "seq_flags": seq_flags,
        "seq_count": seq_count,
        "data_field_len": data_field_len,
        "total_len": total_len,
    }

def fmt_ascii(bs: bytes) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in bs)

def hexdump(buf: bytes, annotate=False, prim_len=6, sec_len=0, with_ascii=True):
    width = 16
    n = len(buf)
    for off in range(0, n, width):
        chunk = buf[off:off+width]
        cells = []
        for i, b in enumerate(chunk):
            gi = off + i
            tok = f"{b:02x}"
            if annotate:
                if gi < prim_len:
                    tok = f"[{tok}]"
                elif prim_len <= gi < prim_len + sec_len:
                    tok = f"{{{tok}}}"
            cells.append(tok)
        hex_part = " ".join(cells)
        if with_ascii:
            print(f"{off:08x}  {hex_part:<{width*4-1}}  |{fmt_ascii(chunk)}|")
        else:
            print(f"{off:08x}  {hex_part}")

def iter_packets(blob: bytes):
    """Yield (offset, header_dict, packet_bytes) for back-to-back L7 packets."""
    i = 0
    n = len(blob)
    while i + 6 <= n:
        try:
            ph = parse_primary_header(blob[i:i+6])
        except Exception:
            return
        end = i + ph["total_len"]
        if end > n:
            # truncated last packet
            return
        yield i, ph, blob[i:end]
        i = end

def main():
    ap = argparse.ArgumentParser(
        description="L7-only CCSDS Space Packet hexdump (auto-length from header)."
    )
    ap.add_argument("path", help="Path to file containing one or more L7 packets")
    ap.add_argument("--index", type=int, default=0,
                    help="Which packet to dump if multiple are concatenated (0-based)")
    ap.add_argument("--ascii", action="store_true",
                    help="Show ASCII gutter")
    ap.add_argument("--annotate", action="store_true",
                    help="Annotate headers: [..]=primary, {..}=secondary")
    ap.add_argument("--sec-len", type=int, default=0,
                    help="Secondary header length (bytes) to highlight when --annotate is set")
    ap.add_argument("--summary", action="store_true",
                    help="Print parsed header fields before the hexdump")
    args = ap.parse_args()

    with open(args.path, "rb") as f:
        data = f.read()

    # Walk packets and pick the requested index
    for idx, (off, ph, pkt) in enumerate(iter_packets(data)):
        if idx == args.index:
            if args.summary:
                t = "TC" if ph["type"] == 1 else "TM"
                print(
                    f"Packet #{idx} @ offset {off}:\n"
                    f"  Version={ph['version']}  Type={t}  SHF={ph['sec_hdr']}  "
                    f"APID=0x{ph['apid']:03x}\n"
                    f"  SeqFlags={ph['seq_flags']:02b}  SeqCount={ph['seq_count']}\n"
                    f"  DataFieldLen={ph['data_field_len']}  TotalBytes={ph['total_len']}\n"
                )
            hexdump(pkt,
                    annotate=args.annotate,
                    prim_len=6,
                    sec_len=(args.sec_len if args.annotate else 0),
                    with_ascii=args.ascii)
            break
    else:
        print("No packet at that index (file empty or index too large).", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()

