#!/usr/bin/env python3
"""
metrics.py — L7 Space-Packet run metrics (pairs with l7_sender.py & l7_receiver.py)

Reads:
  - Receiver CSV (required): columns produced by l7_receiver.py
      rx_ts_sec, src_ip, src_port, apid_hex, type, seq, total_bytes,
      shf, sec_mode, sec_len, mic_state, mic_value, user_len, note
  - Sender CSV (optional): columns produced by l7_sender.py
      profile, apid_hex, type, seq, len_total, mic, sent_bytes
  - apps.json (optional): to map APIDs to profile names / expectations

Outputs:
  - Prints a human-readable summary to stdout
  - Writes JSON metrics to:   <out_dir>/metrics_summary.json
  - Writes CSV table to:      <out_dir>/metrics_table.csv

Example:
  python3 metrics.py \
    --rx ./runs/run_0001/l7_receiver_log.csv \
    --tx ./runs/run_0001/l7_sender_log.csv \
    --apps ./apps.json \
    --out ./runs/run_0001

Notes:
  - All metrics are L7 only (pure Space-Packet view).
  - Loss is computed by comparing TX vs RX sequence sets per APID when TX CSV is provided.
    If TX CSV is omitted, loss cannot be computed (we still give RX-only stats).
  - Inter-arrival is computed from receiver timestamps (rx_ts_sec).
"""

import argparse
import csv
import json
import math
import os
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev

# --------- helpers ---------
def parse_apid(apid_hex_or_int):
    if isinstance(apid_hex_or_int, int):
        return apid_hex_or_int
    s = str(apid_hex_or_int).strip()
    try:
        return int(s, 0)  # handles "0x0B3" or "179"
    except Exception:
        # best-effort: strip "0x" if present and parse hex
        s2 = s.lower().replace("0x", "")
        return int(s2, 16)

def safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def percentile(sorted_vals, p):
    """p in [0,100]"""
    if not sorted_vals:
        return None
    if p <= 0:
        return float(sorted_vals[0])
    if p >= 100:
        return float(sorted_vals[-1])
    k = (len(sorted_vals)-1) * (p/100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[f] * (c-k)
    d1 = sorted_vals[c] * (k-f)
    return float(d0 + d1)

def fmt_pct(x):
    return f"{100.0*x:.2f}%" if x is not None else "n/a"

# --------- data containers ---------
@dataclass
class RxRow:
    t: float
    apid: int
    type_str: str
    seq: int
    total_bytes: int
    mic_state: str  # OK/BAD/none/OFF/SHORT/N/A
    user_len: int

@dataclass
class TxRow:
    apid: int
    type_str: str
    seq: int
    total_bytes: int
    profile: str

# --------- loading ---------
def load_apps(apps_path):
    if not apps_path:
        return {}, {}
    with open(apps_path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    apid_to_name = {}
    name_to_apid = {}
    for prof in arr:
        nm = prof.get("name") or ""
        apid_v = prof.get("apid")
        apid = parse_apid(apid_v)
        apid_to_name[apid] = nm
        if nm:
            name_to_apid[nm] = apid
    return apid_to_name, name_to_apid

def load_rx_csv(path):
    out = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            t = safe_float(row.get("rx_ts_sec"), None)
            apid = parse_apid(row.get("apid_hex"))
            type_str = (row.get("type") or "").upper()
            seq = int(row.get("seq"))
            total_bytes = int(row.get("total_bytes"))
            mic_state = row.get("mic_state") or "N/A"
            user_len = int(row.get("user_len") or 0)
            out.append(RxRow(t, apid, type_str, seq, total_bytes, mic_state, user_len))
    # sort by time if available
    out.sort(key=lambda x: (x.t is None, x.t))
    return out

def load_tx_csv(path):
    if not path:
        return []
    out = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            apid = parse_apid(row.get("apid_hex"))
            type_str = (row.get("type") or "").upper()
            seq = int(row.get("seq"))
            total_bytes = int(row.get("len_total"))
            profile = row.get("profile") or ""
            out.append(TxRow(apid, type_str, seq, total_bytes, profile))
    return out

# --------- metrics computation ---------
def compute_interarrival(ts_list):
    """Return dict with p50/p95/p99/mean/std and pps."""
    ts = [t for t in ts_list if t is not None]
    if len(ts) < 2:
        return {"pps": None, "count": len(ts), "p50_ms": None, "p95_ms": None, "p99_ms": None,
                "mean_ms": None, "std_ms": None, "duration_s": 0.0}
    diffs = [ts[i]-ts[i-1] for i in range(1, len(ts))]
    diffs_ms = [d*1000.0 for d in diffs]
    diffs_ms_sorted = sorted(diffs_ms)
    duration = ts[-1]-ts[0]
    pps = (len(ts)-1)/duration if duration > 0 else None
    return {
        "pps": pps,
        "count": len(ts),
        "p50_ms": percentile(diffs_ms_sorted, 50),
        "p95_ms": percentile(diffs_ms_sorted, 95),
        "p99_ms": percentile(diffs_ms_sorted, 99),
        "mean_ms": mean(diffs_ms) if diffs_ms else None,
        "std_ms": pstdev(diffs_ms) if len(diffs_ms) > 1 else 0.0,
        "duration_s": duration
    }

def analyze_seq_sets(tx_seqs, rx_seqs, modulo=16384):
    """
    Given sets (or Counters) of sequence numbers, estimate loss/dupes.
    tx_seqs: set of sent seq values
    rx_seqs: Counter of received seq values (to detect duplicates)
    """
    if not tx_seqs:
        # RX-only mode: we cannot estimate loss (no ground truth)
        # We can still report dupes and unique counts.
        uniq = set(rx_seqs.keys())
        dup_count = sum(c-1 for c in rx_seqs.values() if c > 1)
        return {
            "tx_known": False,
            "sent": None,
            "recv_unique": len(uniq),
            "duplicates": dup_count,
            "loss_count": None,
            "loss_rate": None,
            "missing_seqs": [],
        }
    # TX known
    sent = len(tx_seqs)
    uniq_rx = set(rx_seqs.keys())
    missing = sorted(list(tx_seqs - uniq_rx))
    dup_count = sum(c-1 for c in rx_seqs.values() if c > 1)
    recv_unique = len(uniq_rx)
    loss_count = max(0, sent - recv_unique)
    loss_rate = (loss_count / sent) if sent > 0 else 0.0
    return {
        "tx_known": True,
        "sent": sent,
        "recv_unique": recv_unique,
        "duplicates": dup_count,
        "loss_count": loss_count,
        "loss_rate": loss_rate,
        "missing_seqs": missing[:50],  # cap list for brevity
    }

def compute_metrics(rx_rows, tx_rows, apid_to_name):
    # Organize data per APID
    rx_by_apid = defaultdict(list)
    for r in rx_rows:
        rx_by_apid[r.apid].append(r)

    tx_by_apid = defaultdict(list)
    for t in tx_rows:
        tx_by_apid[t.apid].append(t)

    # Global metrics
    global_mic = Counter()
    global_sizes = []
    global_ts = []
    for r in rx_rows:
        global_mic[r.mic_state] += 1
        global_sizes.append(r.total_bytes)
        if r.t is not None:
            global_ts.append(r.t)

    inter_global = compute_interarrival(global_ts)

    # Per APID/profile metrics
    table = []
    summary = {
        "overall": {
            "rx_packets": len(rx_rows),
            "rx_bytes_total": sum(x.total_bytes for x in rx_rows),
            "mic_counts": dict(global_mic),
            "size_avg_bytes": (mean(global_sizes) if global_sizes else None),
            "size_min_bytes": (min(global_sizes) if global_sizes else None),
            "size_max_bytes": (max(global_sizes) if global_sizes else None),
            "pps": inter_global["pps"],
            "interarrival_ms": {
                "p50": inter_global["p50_ms"],
                "p95": inter_global["p95_ms"],
                "p99": inter_global["p99_ms"],
                "mean": inter_global["mean_ms"],
                "std": inter_global["std_ms"],
                "duration_s": inter_global["duration_s"],
                "count": inter_global["count"],
            },
        },
        "per_apid": {}
    }

    for apid, rxs in rx_by_apid.items():
        name = apid_to_name.get(apid, "")
        mic_ctr = Counter([r.mic_state for r in rxs])
        sizes = [r.total_bytes for r in rxs]
        ts = [r.t for r in rxs if r.t is not None]
        inter = compute_interarrival(ts)

        # seq tracking
        rx_counter = Counter([r.seq for r in rxs])
        tx_set = set(t.seq for t in tx_by_apid.get(apid, []))
        seq_info = analyze_seq_sets(tx_set, rx_counter)

        row = {
            "apid": apid,
            "name": name,
            "rx_packets": len(rxs),
            "rx_bytes_total": sum(sizes),
            "size_avg": mean(sizes) if sizes else None,
            "size_min": min(sizes) if sizes else None,
            "size_max": max(sizes) if sizes else None,
            "pps": inter["pps"],
            "p50_ms": inter["p50_ms"],
            "p95_ms": inter["p95_ms"],
            "p99_ms": inter["p99_ms"],
            "mic_ok": mic_ctr.get("OK", 0),
            "mic_bad": mic_ctr.get("BAD", 0),
            "mic_none": mic_ctr.get("none", 0),
            "mic_off": mic_ctr.get("OFF", 0),
            "mic_short": mic_ctr.get("SHORT", 0),
            "duplicates": seq_info["duplicates"],
            "loss_count": seq_info["loss_count"],
            "loss_rate": seq_info["loss_rate"],
            "tx_sent": seq_info["sent"],
            "rx_unique": seq_info["recv_unique"],
        }
        table.append(row)

        summary["per_apid"][f"{apid:03x}"] = {
            "name": name,
            "rx_packets": row["rx_packets"],
            "rx_bytes_total": row["rx_bytes_total"],
            "size": {"avg": row["size_avg"], "min": row["size_min"], "max": row["size_max"]},
            "pps": row["pps"],
            "interarrival_ms": {"p50": row["p50_ms"], "p95": row["p95_ms"], "p99": row["p99_ms"]},
            "mic": {"OK": row["mic_ok"], "BAD": row["mic_bad"], "none": row["mic_none"],
                    "OFF": row["mic_off"], "SHORT": row["mic_short"]},
            "seq": {
                "tx_sent": row["tx_sent"],
                "rx_unique": row["rx_unique"],
                "duplicates": row["duplicates"],
                "loss_count": row["loss_count"],
                "loss_rate": row["loss_rate"]
            }
        }

    # Sort table by APID
    table.sort(key=lambda r: r["apid"])
    return summary, table

# --------- printing ---------
def print_report(summary, table):
    o = summary["overall"]
    print("\n=== L7 Metrics Summary ===\n")
    print(f"Total RX packets      : {o['rx_packets']}")
    print(f"Total RX bytes        : {o['rx_bytes_total']}")
    print(f"Avg/Min/Max size (B)  : {o['size_avg_bytes']:.1f} / {o['size_min_bytes']} / {o['size_max_bytes']}" if o['size_avg_bytes'] else "Avg/Min/Max size (B)  : n/a")
    print(f"MIC counts            : {o['mic_counts']}")
    if o["pps"] is not None:
        print(f"Achieved PPS          : {o['pps']:.2f}")
        ia = o["interarrival_ms"]
        print(f"Inter-arrival (ms)    : p50={ia['p50']:.3f}, p95={ia['p95']:.3f}, p99={ia['p99']:.3f}, mean={ia['mean']:.3f}, std={ia['std']:.3f}")
        print(f"RX duration (s)       : {ia['duration_s']:.3f}")
    else:
        print("Achieved PPS          : n/a (insufficient timestamps)")

    print("\n--- Per-APID / Profile ---")
    hdr = ("APID  Name                 RX  Bytes      sz_avg  pps    MIC_OK  MIC_BAD  "
           "Dupes  Loss  Loss%")
    print(hdr)
    print("-"*len(hdr))
    for r in table:
        loss_pct = (r["loss_rate"]*100.0) if r["loss_rate"] is not None else None
        name = (r["name"] or "")[:20]
        print(f"{r['apid']:03x}  {name:20s}  {r['rx_packets']:4d}  {r['rx_bytes_total']:9d}  "
              f"{(r['size_avg'] or 0):6.1f}  "
              f"{(r['pps'] or 0):5.1f}  "
              f"{r['mic_ok']:6d}  {r['mic_bad']:7d}  "
              f"{r['duplicates']:5d}  "
              f"{(r['loss_count'] or 0):4d}  "
              f"{(loss_pct if loss_pct is not None else 0):5.1f}")

# --------- main ---------
def main():
    ap = argparse.ArgumentParser(description="Compute L7 Space-Packet metrics from sender/receiver CSVs")
    ap.add_argument("--rx", required=True, help="Receiver CSV path (from l7_receiver.py)")
    ap.add_argument("--tx", default="", help="Sender CSV path (from l7_sender.py)")
    ap.add_argument("--apps", default="", help="apps.json to map APIDs to profile names")
    ap.add_argument("--out", default="./runs/run_0001", help="Output directory for metrics files")
    args = ap.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)

    apid_to_name, _ = load_apps(args.apps)
    rx_rows = load_rx_csv(args.rx)
    tx_rows = load_tx_csv(args.tx) if args.tx else []

    summary, table = compute_metrics(rx_rows, tx_rows, apid_to_name)

    # Print to console
    print_report(summary, table)

    # Write JSON + CSV
    json_path = os.path.join(args.out, "metrics_summary.json")
    csv_path = os.path.join(args.out, "metrics_table.csv")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(summary, jf, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        w.writerow(["apid_hex","name","rx_packets","rx_bytes_total","size_avg","size_min","size_max",
                    "pps","p50_ms","p95_ms","p99_ms","mic_ok","mic_bad","mic_none","mic_off","mic_short",
                    "duplicates","loss_count","loss_rate","tx_sent","rx_unique"])
        for r in table:
            w.writerow([
                f"0x{r['apid']:03x}", r["name"], r["rx_packets"], r["rx_bytes_total"],
                r["size_avg"], r["size_min"], r["size_max"],
                r["pps"], r["p50_ms"], r["p95_ms"], r["p99_ms"],
                r["mic_ok"], r["mic_bad"], r["mic_none"], r["mic_off"], r["mic_short"],
                r["duplicates"], r["loss_count"], r["loss_rate"], r["tx_sent"], r["rx_unique"]
            ])

    print(f"\nWrote: {json_path}\nWrote: {csv_path}")

if __name__ == "__main__":
    main()

