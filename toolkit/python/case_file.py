#!/usr/bin/env python3
"""
WildGuard M9 — evidence integrity check & court-ready case file generator.

A poacher on camera is worthless in court if the evidence can't be proven unaltered. This tool
re-hashes each evidence file, compares against the SHA-256 stored in the Tactical Event at capture
time (PASS/FAIL integrity), and writes a plain-text case file with the manifest and chain of custody
an officer can sign.

Offline, stdlib only. No reportlab — plain text is universally printable and tamper-evident via
hashes. (Swap to PDF later if a jurisdiction requires it.)

Input: a Tactical Event JSON (or array). Each event may carry:
    evidence_url / evidence_hash, or
    metadata.evidence = [{"filename","sha256","captured_at","captured_by", ...}]
    metadata.custody_log = [{"ts","action","actor"}]

Run
---
    python case_file.py --demo
    python case_file.py --event evt.json --files-dir ./vault --out case.txt

Exit code is non-zero if any evidence file FAILS the integrity check.
"""
import argparse
import hashlib
import json
import os
import sys
import time


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_items(ev):
    items = list(ev.get("metadata", {}).get("evidence", []) or [])
    if ev.get("evidence_hash") and ev.get("evidence_url"):
        items.append({"filename": os.path.basename(ev["evidence_url"]),
                      "sha256": ev["evidence_hash"], "captured_by": ev.get("source_id")})
    return items


def build_case(ev, files_dir):
    cid = ev.get("event_id", "unknown")[:18]
    lines, all_pass = [], True
    lines.append("=" * 64)
    lines.append(f"FORENSIC INCIDENT REPORT — CASE {cid}")
    lines.append(f"GENERATED: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    lines.append("=" * 64)
    c = ev.get("coordinates", {})
    lines.append(f"EVENT TYPE : {ev.get('threat_class')}")
    lines.append(f"SOURCE     : {ev.get('source_type')} / {ev.get('source_id')}")
    lines.append(f"TIMESTAMP  : {ev.get('timestamp')}")
    lines.append(f"LOCATION   : {c.get('latitude')}, {c.get('longitude')}")
    lines.append(f"CONFIDENCE : {ev.get('confidence')}")
    lines.append("")
    lines.append("EVIDENCE MANIFEST (integrity):")
    items = evidence_items(ev)
    if not items:
        lines.append("  (no evidence files referenced)")
    for it in items:
        stored = it.get("sha256")
        fn = it.get("filename", "?")
        status = "NO FILE"
        if files_dir:
            path = os.path.join(files_dir, os.path.basename(fn))
            if os.path.isfile(path):
                actual = sha256_file(path)
                ok = (actual == stored)
                all_pass = all_pass and ok
                status = "PASS" if ok else "FAIL (hash mismatch — possible tampering)"
            else:
                status = "MISSING FILE (cannot verify)"
        lines.append(f"  - {fn}")
        lines.append(f"      sha256(stored): {stored}")
        lines.append(f"      integrity     : {status}")
        if it.get("captured_by"):
            lines.append(f"      captured_by   : {it['captured_by']}")
    lines.append("")
    lines.append("CHAIN OF CUSTODY:")
    log = ev.get("metadata", {}).get("custody_log", [])
    if not log:
        lines.append("  (no custody entries — add capture/transfer/archive records)")
    for e in log:
        lines.append(f"  {e.get('ts')}  {e.get('action'):<12} {e.get('actor')}")
    lines.append("")
    lines.append("REPORTING OFFICER: ____________________   SIGNATURE: ____________   DATE: ________")
    lines.append("=" * 64)
    return "\n".join(lines), all_pass


DEMO_EVENT = {
    "event_id": "evt-2026-001-cam04",
    "timestamp": 1782046931,
    "source_type": "camera_trap", "source_id": "CAM_TRAP_04",
    "coordinates": {"latitude": -2.341, "longitude": 34.842},
    "threat_class": "poacher", "confidence": 0.93,
    "metadata": {
        "evidence": [{"filename": "CAM04_demo.jpg", "sha256": "PLACEHOLDER",
                      "captured_by": "CAM_TRAP_04"}],
        "custody_log": [
            {"ts": "2026-06-20T03:42:11Z", "action": "captured", "actor": "CAM_TRAP_04"},
            {"ts": "2026-06-20T08:00:00Z", "action": "transferred", "actor": "ranger_007"},
            {"ts": "2026-06-20T09:15:00Z", "action": "archived", "actor": "analyst_002"},
        ],
    },
}


def main():
    ap = argparse.ArgumentParser(description="WildGuard M9 case file / integrity check")
    ap.add_argument("--event", help="Tactical Event JSON (object or array)")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--files-dir", help="directory holding the evidence files to verify")
    ap.add_argument("--out", help="write the case file here (else stdout)")
    args = ap.parse_args()

    if args.demo:
        # build a real evidence file + correct hash so the demo verifies end to end
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "CAM04_demo.jpg")
        open(p, "wb").write(b"\xff\xd8\xff demo image bytes for WildGuard M9")
        DEMO_EVENT["metadata"]["evidence"][0]["sha256"] = sha256_file(p)
        events = [DEMO_EVENT]
        args.files_dir = d
        print(f"[demo] synthetic evidence in {d}\n", file=sys.stderr)
    elif args.event:
        data = json.load(open(args.event, encoding="utf-8"))
        events = data if isinstance(data, list) else [data]
    else:
        print("Need --event FILE or --demo.", file=sys.stderr)
        return 2

    overall = True
    out_parts = []
    for ev in events:
        text, ok = build_case(ev, args.files_dir)
        overall = overall and ok
        out_parts.append(text)
    report = "\n\n".join(out_parts)

    if args.out:
        open(args.out, "w", encoding="utf-8").write(report)
        print(f"[ok] case file -> {args.out}", file=sys.stderr)
    else:
        print(report)

    print(f"\nINTEGRITY: {'ALL PASS' if overall else 'FAILURES PRESENT'}", file=sys.stderr)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
