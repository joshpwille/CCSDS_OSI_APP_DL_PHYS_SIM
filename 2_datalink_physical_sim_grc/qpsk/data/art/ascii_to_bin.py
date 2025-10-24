#!/usr/bin/env python3
# Purpose: Read a text file (ASCII art) and write its bytes verbatim to a .bin file
# Usage:   python3 tools/ascii_to_bin.py data/art/ascii_art.txt data/payload/art.bin
import sys, pathlib
if len(sys.argv) != 3:
    print("Usage: python3 tools/ascii_to_bin.py <in.txt> <out.bin>")
    sys.exit(1)
inp = pathlib.Path(sys.argv[1]).read_bytes()  # bytes, exactly as in file
pathlib.Path(sys.argv[2]).write_bytes(inp)
print(f"Wrote {len(inp)} bytes to {sys.argv[2]}")
