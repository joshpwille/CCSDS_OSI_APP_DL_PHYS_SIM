#!/usr/bin/env python3
import sys, textwrap

if len(sys.argv) != 3:
    print("Usage: dump_frame.py <path> <frame_len_bytes>", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]
n    = int(sys.argv[2])

with open(path, "rb") as f:
    frame = f.read(n)

# Pretty hex dump (16 bytes per line with offset)
for off in range(0, len(frame), 16):
    chunk = frame[off:off+16]
    hexes = " ".join(f"{b:02x}" for b in chunk)
    print(f"{off:08x}  {hexes}")
