#!/usr/bin/env python3
import sys, os, math

ASM = bytes((0x1A, 0xCF, 0xFC, 0x1D))

def hexdump(b, start=0, count=64, width=16):
    s = b[start:start+count]
    for off in range(0, len(s), width):
        line = s[off:off+width]
        hexs = " ".join(f"{x:02x}" for x in line)
        print(f"{start+off:08x}  {hexs}")

def analyze_one(path, stage_name, frame_len=None, asm=ASM):
    data = open(path, "rb").read()
    n = len(data)
    print(f"\n[{stage_name}]")
    print(f"  file: {path}")
    print(f"  size: {n} bytes")

    if frame_len:
        frames = n / frame_len
        rem = n % frame_len
        print(f"  frame_len={frame_len}, frames={frames:.3f} (remainder {rem})")
        if rem != 0:
            print("  WARNING: file size is not an integer multiple of frame_len")

    # Show first 64 bytes
    print("  first 64 bytes:")
    hexdump(data, 0, 64)

    # Find ASM occurrences (if we expect them)
    if asm and len(asm) > 0:
        idxs = []
        i = 0
        while True:
            j = data.find(asm, i)
            if j < 0: break
            idxs.append(j)
            i = j + 1
        if idxs:
            print(f"  ASM occurrences: {len(idxs)}")
            if frame_len:
                misaligned = [j for j in idxs if (j % frame_len) != 0]
                print(f"  ASM @ offsets (first 5): {idxs[:5]}")
                if misaligned:
                    print("  WARNING: some ASM positions are not on frame boundaries.")
            # Show a context around the first ASM
            j0 = idxs[0]
            print("  bytes around first ASM (-8..+16):")
            start = max(0, j0-8)
            hexdump(data, start, 24)
        else:
            print("  ASM not found.")

def bitcount(x):
    # count set bits in 0..255
    return bin(x).count("1")

def compare_pair(path_a, path_b, count=2048):
    a = open(path_a, "rb").read()
    b = open(path_b, "rb").read()
    n = min(len(a), len(b), count)
    diff_bytes = sum(1 for i in range(n) if a[i] != b[i])
    diff_bits  = sum(bitcount(a[i] ^ b[i]) for i in range(n))
    print(f"\n[COMPARE] {os.path.basename(path_a)} vs {os.path.basename(path_b)} (first {n} bytes)")
    print(f"  byte diffs : {diff_bytes}/{n}")
    print(f"  bit diffs  : {diff_bits} bits")
    print("  A first 64:")
    hexdump(a, 0, 64)
    print("  B first 64:")
    hexdump(b, 0, 64)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python analyze_cadu.py <file> [frame_len]  # analyze one")
        print("  python analyze_cadu.py cmp <fileA> <fileB> # compare two")
        sys.exit(0)

    if sys.argv[1] == "cmp":
        compare_pair(sys.argv[2], sys.argv[3])
        sys.exit(0)

    path = sys.argv[1]
    frame_len = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    # If caller passes frame_len that corresponds to a post-ASM frame, ASM should align at multiples of frame_len.
    analyze_one(path, "stage", frame_len=frame_len, asm=ASM if frame_len and frame_len >= 4 else None)
