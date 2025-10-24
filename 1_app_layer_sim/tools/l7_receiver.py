#!/usr/bin/env python3
"""
l7_receiver.py — CCSDS L7 Space-Packet receiver (UDP)

- Binds to UDP, receives datagrams from l7_sender.py (one L7 packet per datagram).
- Parses CCSDS primary header, optional secondary header (configurable), detects/validates MIC (CRC-32C).
- Logs per-packet fields to CSV; optionally saves bin+hex artifacts.

Optional profile-awareness:
  --config apps.json     (same schema as the sender) lets the receiver auto-apply
                         expected sec-hdr mode and MIC expectation using APID lookup.

Secondary header options (when not using --config):
  --sec-mode none|ns8|sec_us32|fixed:N|auto
    - none      : no secondary header
    - ns8       : 8-byte UNIX nanoseconds (big-endian)
    - sec_us32  : 4B seconds + 4B microseconds (big-endian)
    - fixed:N   : exactly N bytes of fixed secondary header
    - auto      : infer from --config if provided; else treat as none

MIC options:
  --mic auto|on|off
    - auto (default): if last 4 bytes of data-field equal CRC-32C(user), MIC=OK
    - on            : always assume last 4 bytes are MIC; verify it
    - off           : never attempt MIC verification

Artifacts:
  --write-dir ./runs/run_0001/packets   → writes packet_XXXX.bin and .hex (first 64B)
  --print                                → prints one-line summary to stdout per packet

CSV:
  --csv ./runs/run_0001/l7_receiver_log.csv (default) with fields:
    rx_ts_sec, src_ip, src_port, apid_hex, type, seq, total_bytes,
    shf, sec_mode, sec_len, mic_state, mic_value, user_len, note
"""

import argparse
import socket
import struct
import time
import csv
import os
import json
from pathlib import Path
from typing import Optional, Tuple

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

# ---------------- Hexdump ----------------
def hexdump_first_n(buf: bytes, n: int = 64) -> str:
    n = min(n, len(buf))
    out = []
    for off in range(0, n, 16):
        chunk = buf[off:off+16]
        hexes = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        out.append(f"{off:08x}  {hexes:<47}  |{ascii_part}|")
    return "\n".join(out)

# ---------------- CCSDS primary header ----------------
def parse_primary_header(hdr: bytes):
    if len(hdr) < 6:
        raise ValueError("Need at least 6 bytes for CCSDS primary header")
    w1, w2, w3 = struct.unpack(">HHH", hdr[:6])
    version = (w1 >> 13) & 0x7
    pkt_type = (w1 >> 12) & 0x1   # 0=TM, 1=TC
    shf =      (w1 >> 11) & 0x1   # secondary header flag
    apid =      w1 & 0x7FF

    seq_flags = (w2 >> 14) & 0x3
    seq_count =  w2 & 0x3FFF

    data_field_len = w3              # bytes after header minus 1
    total_len = 6 + (data_field_len + 1)
    return {
        "version": version, "type": pkt_type, "shf": shf, "apid": apid,
        "seq_flags": seq_flags, "seq_count": seq_count,
        "data_field_len": data_field_len, "total_len": total_len
    }

# ---------------- Secondary header helpers ----------------
def sec_len_from_mode(mode: str) -> int:
    if mode == "none" or mode == "auto":
        return 0
    if mode == "ns8":
        return 8
    if mode == "sec_us32":
        return 8
    if mode.startswith("fixed:"):
        try:
            return int(mode.split(":", 1)[1])
        except Exception:
            raise ValueError("fixed mode must be fixed:N (N integer)")
    raise ValueError(f"Unknown sec-mode: {mode}")

def parse_sec_hdr_bytes(mode: str, sec_hdr: bytes) -> dict:
    """Return a dict of decoded fields (best-effort) for display/logging."""
    info = {"mode": mode, "len": len(sec_hdr)}
    try:
        if mode == "ns8" and len(sec_hdr) == 8:
            ns = int.from_bytes(sec_hdr, "big")
            info["unix_ns"] = ns
            info["unix_s_float"] = ns / 1e9
        elif mode == "sec_us32" and len(sec_hdr) == 8:
            sec = int.from_bytes(sec_hdr[0:4], "big")
            usec = int.from_bytes(sec_hdr[4:8], "big")
            info["sec"] = sec
            info["usec"] = usec
            info["unix_s_float"] = sec + usec / 1e6
        # fixed/none → nothing more to parse
    except Exception:
        pass
    return info

# ---------------- apps.json (optional) ----------------
def load_profiles(config_path: Optional[str]):
    """Return dict apid(int)->profile dict, or {}."""
    if not config_path:
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    apid_map = {}
    for prof in arr:
        apid_v = prof.get("apid")
        if isinstance(apid_v, str):
            apid_int = int(apid_v, 0)
        else:
            apid_int = int(apid_v)
        apid_map[apid_int] = prof
    return apid_map

def expected_sec_mode_and_mic_for_apid(apid: int, apid_map: dict) -> Tuple[str, Optional[bool]]:
    """
    Return (sec_mode_str, mic_bool_or_None) using apps.json, or ("auto", None) if unknown.
    """
    prof = apid_map.get(apid)
    if not prof:
        return "auto", None
    # Translate profile's sec_hdr record to receiver mode
    sh = prof.get("sec_hdr", {}) or {}
    mode = sh.get("mode", "none")
    if mode == "fixed":
        hx = sh.get("hex", "") or ""
        return f"fixed:{len(bytes.fromhex(hx))}", bool(prof.get("use_mic", False))
    if mode in ("none", "ns8", "sec_us32"):
        return mode, bool(prof.get("use_mic", False))
    # Unknown: fall back
    return "auto", bool(prof.get("use_mic", False))

# ---------------- Packet splitting ----------------
def iter_packets(blob: bytes):
    """
    Yield contiguous L7 packets inside 'blob'.
    Stops on truncation or parse error.
    """
    i = 0
    n = len(blob)
    while i + 6 <= n:
        try:
            ph = parse_primary_header(blob[i:i+6])
        except Exception:
            return
        end = i + ph["total_len"]
        if end > n:
            return
        yield blob[i:end], ph
        i = end

# ---------------- Receiver core ----------------
def process_packet(pkt: bytes,
                   ph: dict,
                   sec_mode_cli: str,
                   mic_mode: str,
                   apid_map: dict,
                   write_dir: Optional[str],
                   csv_writer,
                   src_addr: Tuple[str, int],
                   print_line: bool,
                   counter: int):
    """
    Parse one packet, attempt MIC check, log, and optionally write artifacts.
    """
    rx_ts = time.time()
    apid = ph["apid"]
    pkt_type = "TC" if ph["type"] == 1 else "TM"
    shf = ph["shf"]

    # Decide sec-mode for this APID
    sec_mode = sec_mode_cli
    mic_expect = None
    if sec_mode_cli == "auto":
        sec_mode, mic_expect = expected_sec_mode_and_mic_for_apid(apid, apid_map)

    # Determine sec-hdr length
    sec_len = 0
    if shf == 1:
        try:
            sec_len = sec_len_from_mode(sec_mode)
        except Exception:
            sec_len = 0

    # Split fields
    data_field = pkt[6:]                          # bytes after primary header
    if sec_len > len(data_field):
        sec_len = 0                                # avoid crash if malformed
    sec_hdr = data_field[:sec_len]
    user_and_maybe_mic = data_field[sec_len:]

    # MIC detection / verification
    mic_state = "N/A"
    mic_hex = ""
    user = user_and_maybe_mic
    if mic_mode == "off":
        mic_state = "OFF"
    else:
        # If expecting MIC, or auto-detect
        if len(user_and_maybe_mic) >= 4:
            # Try treat last 4 bytes as MIC
            candidate_user = user_and_maybe_mic[:-4]
            candidate_mic = int.from_bytes(user_and_maybe_mic[-4:], "big")
            calc = crc32c(candidate_user)
            if candidate_mic == calc:
                mic_state = "OK"
                mic_hex = f"0x{candidate_mic:08x}"
                user = candidate_user
            else:
                if mic_mode == "on" or mic_expect is True:
                    mic_state = "BAD"
                    mic_hex = f"0x{candidate_mic:08x}"
                else:
                    mic_state = "none"  # looks like there wasn't a MIC
        else:
            if mic_mode == "on" or mic_expect is True:
                mic_state = "SHORT"     # not enough bytes for MIC
            else:
                mic_state = "none"

    # Optional decode of secondary header for logging
    sec_info = parse_sec_hdr_bytes(sec_mode, sec_hdr) if sec_len > 0 else {"mode": sec_mode, "len": 0}

    # Write artifacts
    if write_dir:
        Path(write_dir).mkdir(parents=True, exist_ok=True)
        base = os.path.join(write_dir, f"packet_{counter:06d}")
        with open(base + ".bin", "wb") as w:
            w.write(pkt)
        with open(base + ".hex", "w", encoding="utf-8") as w:
            w.write(hexdump_first_n(pkt, 64) + "\n")

    # CSV log
    if csv_writer:
        csv_writer.writerow([
            f"{rx_ts:.6f}",
            src_addr[0], src_addr[1],
            f"0x{apid:03x}", pkt_type, ph["seq_count"], len(pkt),
            shf, sec_mode, sec_len,
            mic_state, mic_hex, len(user),
            ""  # note placeholder
        ])

    # Optional print
    if print_line:
        print(
            f"{time.strftime('%H:%M:%S', time.localtime(rx_ts))} "
            f"{src_addr[0]}:{src_addr[1]}  "
            f"APID=0x{apid:03x} {pkt_type} "
            f"Seq={ph['seq_count']:5d} Len={len(pkt):4d} "
            f"SHF={shf} Sec={sec_mode}/{sec_len}  MIC={mic_state}"
        )

# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser(description="CCSDS L7 Space-Packet receiver (UDP)")
    ap.add_argument("--host", default="0.0.0.0", help="Bind address")
    ap.add_argument("--port", type=int, default=52001, help="UDP port to listen on")
    ap.add_argument("--max", type=int, default=0, help="Stop after N packets (0 = run forever)")
    ap.add_argument("--print", dest="do_print", action="store_true", help="Print one-line summary per packet")
    ap.add_argument("--write-dir", default="", help="Write packet_{NNNNNN}.bin/.hex to this dir")
    ap.add_argument("--csv", default="./runs/run_0001/l7_receiver_log.csv", help="CSV log path ('' to disable)")

    # Secondary header & MIC handling
    ap.add_argument("--sec-mode", default="auto",
                    help="none|ns8|sec_us32|fixed:N|auto (default auto; uses --config if provided)")
    ap.add_argument("--mic", choices=["auto", "on", "off"], default="auto",
                    help="MIC (CRC-32C) detection: auto|on|off (default auto)")

    # Optional profile awareness
    ap.add_argument("--config", default="", help="apps.json (same schema as sender) for APID expectations")
    args = ap.parse_args()

    apid_map = load_profiles(args.config if args.config else None)

    # Prepare IO
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

    logf = None
    writer = None
    if args.csv:
        Path(os.path.dirname(args.csv)).mkdir(parents=True, exist_ok=True)
        logf = open(args.csv, "w", newline="", encoding="utf-8")
        writer = csv.writer(logf)
        writer.writerow([
            "rx_ts_sec", "src_ip", "src_port",
            "apid_hex", "type", "seq", "total_bytes",
            "shf", "sec_mode", "sec_len",
            "mic_state", "mic_value", "user_len",
            "note"
        ])

    print(f"Listening on {args.host}:{args.port} (sec-mode={args.sec_mode}, mic={args.mic})")

    count = 0
    try:
        while True:
            data, addr = sock.recvfrom(65535)
            # Could be 1 packet per datagram (sender behavior) or multiple.
            for pkt, ph in iter_packets(data):
                count += 1
                process_packet(pkt, ph,
                               sec_mode_cli=args.sec_mode,
                               mic_mode=args.mic,
                               apid_map=apid_map,
                               write_dir=(args.write_dir if args.write_dir else None),
                               csv_writer=writer,
                               src_addr=addr,
                               print_line=args.do_print,
                               counter=count)
                if args.max and count >= args.max:
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    finally:
        if logf:
            logf.flush()
            logf.close()
        sock.close()
        print(f"Stopped after {count} packet(s).")

if __name__ == "__main__":
    main()

