#!/usr/bin/env python3
# Truncate (empty) all .bin output files in data/art without deleting them.
# Safe to re-run; creates the file if missing.

import os
import glob
import sys

DIR = r"C:\Users\joshp\OneDrive\Desktop\qpsk\data\art"

def truncate(path: str) -> None:
    # Using wb recreates/truncates to 0 bytes
    with open(path, "wb"):
        pass

def main():
    # Let you optionally pass a specific folder: python clean_bins.py <folder>
    folder = sys.argv[1] if len(sys.argv) > 1 else DIR
    pattern = os.path.join(folder, "*.bin")
    paths = sorted(glob.glob(pattern))
    if not paths:
        print(f"No .bin files found in {folder}")
        return
    for p in paths:
        try:
            truncate(p)
            print(f"Truncated: {p}")
        except PermissionError:
            print(f"SKIPPED (in use): {p}")
        except OSError as e:
            print(f"ERROR on {p}: {e}")

if __name__ == "__main__":
    main()
