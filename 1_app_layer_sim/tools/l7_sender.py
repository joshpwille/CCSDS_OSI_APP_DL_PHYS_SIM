#!/usr/bin/env python3
"""
l7_sender.py — Multi-profile CCSDS L7 Space-Packet sender (UDP → GRC Socket PDU Source)

Reads a JSON array of app profiles (see apps.json), builds CCSDS Space Packets:
  Primary header (6B) + optional Secondary header + User data [+ optional MIC (CRC-32C over USER ONLY)],
and sends each as a single UDP datagram. Round-robin across profiles, with per-app 14-bit seq counters.

apps.json fields expected (per profile):
  {
    "name": "CFDP_META",
    "apid": "0x0B3",                 # hex or int
    "type": "TC",                    # "TM" or "TC"
    "sec_hdr": { "mode": "ns8" },    # "none" | "ns8" | "sec_us32" | "fixed"
                                     # if fixed: { "mode":"fixed", "hex":"010203..." }
    "body": {                        # one of:
      "mode": "ascii", "text": "0.21/data/", "pad_byte": "00"
      # or
      # "mode": "pattern", "pattern16": true, "extra_bytes": 16
      # or
      # "mode": "file", "path": "/path/to/payload.bin"
    },
    "use_mic": true,                 # CRC-32C appended big-endian, computed over USER DATA ONLY
    "data_field_len": 138            # bytes after 6B header (sec_hdr + user [+ MIC])
  }

Golden artifacts:
  For each profile, the FIRST emitted packet is saved to:
    golden/<name>_golden_packed_space_packet.bin
    golden/<name>_golden_packed_space_packet.hex (first 64 bytes pretty)
    golden/<name>_golden_expected_crc32c.txt (if MIC enabled)

Usage (examples):
  python3 l7_sender.py --config apps.json --count-per 1000 --pps 1000 \
    --host 127.0.0.1 --port 52001 --golden-dir ./golden \
    --csv-log ./runs/run_0001/l7_sender_log.csv

  # Run only specific profiles by name (comma-separated)
  python3 l7_sender.py --config apps.json --profiles CFDP_META,HK_TLM_TINY --count-per 500

Notes:
  - SeqFlags = 0b11 (standalone). You generally do NOT set L7 segmentation—L2 does spanning.
  - Primary Length = (len(sec_hdr) + len(user [+ MIC])) - 1  (bytes AFTER 6B header).
  - If data_field_len is given, we pad/truncate the USER portion so that MIC (if used) stays LAST.
"""

import argparse
import socket
import struct
import time
import os
import csv
import json
from pathlib import Path

# ---------------- CRC-32C (Castagnoli) ----------------
_CRC32C_POLY = 0x82F63B78
_crc32c_table = [0] * 256
for i in range(256):
    crc = i
    for _ in range(8):
        crc = (crc >> 1) ^ _CRC32C_POLY if (crc & 1) else (crc >> 1)
    _crc32c_table[i] = crc

def crc32c(data: bytes, init: int = 0) -> int:
    crc = init ^ 0xFFFFFFFF
    for b in data:
        crc = _crc32c_table[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF

def be_u64(x: int) -> bytes: return struct.pack(">Q", x)
def be_u32(x: int) -> bytes: return struct.pack(">I", x)

# ---------------- CCSDS primary header ----------------
def pack_primary_header(version: int, pkt_type: int, shf: int,
                        apid: int, seq_flags: int, seq_count: int, length: int) -> bytes:
    assert 0 <= version <= 7
    assert pkt_type in (0, 1)
    assert shf in (0, 1)
    assert 0 <= apid <= 0x7FF
    assert 0 <= seq_flags <= 0b11
    assert 0 <= seq_count <= 0x3FFF
    assert 0 <= length <= 0xFFFF
    w1 = (version << 13) | (pkt_type << 12) | (shf << 11) | apid
    w2 = (seq_flags << 14) | seq_count
    w3 = length
    return struct.pack(">HHH", w1, w2, w3)

# ---------------- Secondary header builders ----------------
def make_time_tag_ns8() -> bytes:
    return be_u64(time.time_ns())

def make_sec_hdr(spec: dict) -> bytes:
    if not spec or spec.get("mode", "none") == "none":
        return b""
    mode = spec["mode"]
    if mode == "ns8":
        return make_time_tag_ns8()
    if mode == "sec_us32":
        t = time.time()
        sec = int(t)
        usec = int((t - sec) * 1_000_000)
        return be_u32(sec) + be_u32(usec)
    if mode == "fixed":
        hx = spec.get("hex", "")
        if len(hx) % 2 != 0:
            raise ValueError("sec_hdr.fixed.hex must have even number of hex chars")
        return bytes.fromhex(hx)
    raise ValueError(f"Unknown sec_hdr.mode: {mode}")

# ---------------- Body / user-data builders ----------------
def body_from_spec(spec: dict, counter: int) -> bytes:
    """
    Supported:
      - ascii: {"mode":"ascii","text":"...","pad_byte":"00"(optional)}
      - pattern: {"mode":"pattern","pattern16":true,"extra_bytes":N}
      - file: {"mode":"file","path":"/path/to.bin"}
    Counter is available if you want to embed it (not used by default here).
    """
    mode = (spec or {}).get("mode", "pattern")
    if mode == "ascii":
        text = spec.get("text", "")
        return text.encode("ascii", errors="replace")
    elif mode == "pattern":
        chunks = []
        if spec.get("pattern16", True):
            chunks.append(bytes(range(16)))  # 0x00..0x0F
        extra = int(spec.get("extra_bytes", 0))
        if extra > 0:
            chunks.append(bytes((i & 0xFF for i in range(extra))))
        return b"".join(chunks)
    elif mode == "file":
        p = spec.get("path", "")
        if not p:
            raise ValueError("body.mode=file requires 'path'")
        with open(p, "rb") as f:
            return f.read()
    else:
        raise ValueError(f"Unknown body.mode: {mode}")

def pad_or_truncate_to_len(user_no_mic: bytes, desired_len_without_mic: int, pad_byte: int = 0x00) -> bytes:
    """Return USER (without MIC) padded/truncated to exactly 'desired_len_without_mic' bytes."""
    cur = len(user_no_mic)
    if cur == desired_len_without_mic:
        return user_no_mic
    if cur < desired_len_without_mic:
        return user_no_mic + bytes([pad_byte]) * (desired_len_without_mic - cur)
    # truncate
    return user_no_mic[:desired_len_without_mic]

def hexdump_first_n(buf: bytes, n: int = 64) -> str:
    n = min(n, len(buf))
    out = []
    for off in range(0, n, 16):
        chunk = buf[off:off+16]
        hexes = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        out.append(f"{off:08x}  {hexes:<47}  |{ascii_part}|")
    return "\n".join(out)

# ---------------- Profile + send loop ----------------
class ProfileState:
    def __init__(self, prof: dict):
        self.prof = prof
        self.seq = 0  # 14-bit wraps in send loop
        self.golden_written = False

def parse_apid(v) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 0)  # handles "0x0B3" or "179"
    raise ValueError("apid must be int or string")

def build_packet_for_profile(pstate: ProfileState, counter: int) -> tuple[bytes, int, str]:
    """
    Build one CCSDS Space Packet for a profile.
    Returns (packet_bytes, total_len, mic_hex_or_empty).
    """
    prof = pstate.prof
    name = prof.get("name", "NONAME")
    apid = parse_apid(prof["apid"])
    pkt_type_bit = 1 if prof.get("type", "TC").upper() == "TC" else 0

    sec_hdr = make_sec_hdr(prof.get("sec_hdr", {}))
    user_no_mic = body_from_spec(prof.get("body", {}), counter=counter)

    # If ascii mode defines pad_byte, use it for padding; else default 0x00
    pad_byte = 0x00
    bspec = prof.get("body", {})
    if bspec.get("mode") == "ascii":
        pad_hex = bspec.get("pad_byte", "00")
        try:
            pad_byte = int(pad_hex, 16)
        except Exception:
            pad_byte = 0x00

    use_mic = bool(prof.get("use_mic", False))
    data_field_len = int(prof.get("data_field_len", len(sec_hdr) + len(user_no_mic) + (4 if use_mic else 0)))

    # We want MIC (if present) to be the LAST 4 bytes of the data field.
    # So: determine the desired USER length *excluding* MIC:
    desired_user_len_wo_mic = data_field_len - len(sec_hdr) - (4 if use_mic else 0)
    if desired_user_len_wo_mic < 0:
        raise ValueError(f"[{name}] data_field_len too small for sec_hdr+MIC")

    user_wo_mic_padded = pad_or_truncate_to_len(user_no_mic, desired_user_len_wo_mic, pad_byte=pad_byte)

    mic_hex = ""
    if use_mic:
        mic_val = crc32c(user_wo_mic_padded)
        mic_hex = f"0x{mic_val:08x}"
        user = user_wo_mic_padded + be_u32(mic_val)
    else:
        user = user_wo_mic_padded

    # SHF bit reflects presence of secondary header bytes
    shf = 1 if len(sec_hdr) > 0 else 0

    # Primary header
    version = 0
    seq_flags = 0b11  # standalone
    seq_count = pstate.seq & 0x3FFF
    prim_len = (len(sec_hdr) + len(user)) - 1
    hdr = pack_primary_header(version, pkt_type_bit, shf, apid, seq_flags, seq_count, prim_len)
    pkt = hdr + sec_hdr + user
    total_len = len(pkt)
    return pkt, total_len, mic_hex

def main():
    ap = argparse.ArgumentParser(description="CCSDS L7 multi-profile packet sender (UDP → GRC)")
    ap.add_argument("--config", required=True, help="Path to apps.json")
    ap.add_argument("--profiles", default="", help="Comma-separated names to include (default: all)")
    ap.add_argument("--count-per", type=int, default=1000, help="Packets per profile")
    ap.add_argument("--pps", type=float, default=1000.0, help="Packets per second (0 = as fast as possible)")
    ap.add_argument("--host", default="127.0.0.1", help="UDP host")
    ap.add_argument("--port", type=int, default=52001, help="UDP port")
    ap.add_argument("--golden-dir", default="./golden", help="Where to write first-packet goldens per profile")
    ap.add_argument("--csv-log", default="./runs/run_0001/l7_sender_log.csv", help="CSV log path ('' to disable)")
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    if not isinstance(profiles, list) or len(profiles) == 0:
        raise SystemExit("config must be a non-empty JSON array of profiles")

    # Filter by names if requested
    wanted = set(n.strip() for n in args.profiles.split(",")) if args.profiles else None
    selected = []
    for prof in profiles:
        if wanted and prof.get("name") not in wanted:
            continue
        selected.append(ProfileState(prof))
    if not selected:
        raise SystemExit("No profiles selected after filtering by --profiles")

    # Prepare IO
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (args.host, args.port)

    golden_dir = args.golden_dir
    Path(golden_dir).mkdir(parents=True, exist_ok=True)

    logw = None
    logf = None
    if args.csv_log:
        Path(os.path.dirname(args.csv_log)).mkdir(parents=True, exist_ok=True)
        logf = open(args.csv_log, "w", newline="", encoding="utf-8")
        logw = csv.writer(logf)
        logw.writerow(["profile", "apid_hex", "type", "seq", "len_total", "mic", "sent_bytes"])

    interval = (1.0 / args.pps) if args.pps > 0 else 0.0
    total_packets = len(selected) * args.count_per

    counter = 0
    for round_idx in range(args.count_per):
        for ps in selected:
            # Build
            pkt, tot_len, mic_hex = build_packet_for_profile(ps, counter=counter)
            # Send
            sock.sendto(pkt, target)
            # Golden for the first packet of this profile
            if not ps.golden_written:
                name = ps.prof.get("name", f"profile_{id(ps)}")
                with open(os.path.join(golden_dir, f"{name}_golden_packed_space_packet.bin"), "wb") as w:
                    w.write(pkt)
                with open(os.path.join(golden_dir, f"{name}_golden_packed_space_packet.hex"), "w", encoding="utf-8") as w:
                    w.write(hexdump_first_n(pkt, 64) + "\n")
                if ps.prof.get("use_mic", False):
                    with open(os.path.join(golden_dir, f"{name}_golden_expected_crc32c.txt"), "w", encoding="utf-8") as w:
                        w.write(mic_hex + "\n")
                ps.golden_written = True
            # CSV
            if logw:
                apid_hex = ps.prof.get("apid")
                tstr = ps.prof.get("type", "TC").upper()
                logw.writerow([ps.prof.get("name", ""),
                               apid_hex, tstr,
                               ps.seq & 0x3FFF, tot_len, mic_hex, len(pkt)])
            # Next seq (mod 14 bits)
            ps.seq = (ps.seq + 1) & 0x3FFF
            counter += 1
            # Pace
            if interval > 0:
                time.sleep(interval)

    if logf:
        logf.flush()
        logf.close()

if __name__ == "__main__":
    main()

