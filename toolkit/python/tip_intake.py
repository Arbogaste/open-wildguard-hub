#!/usr/bin/env python3
"""
WildGuard M6 — community tip intake & normalizer.

Turn raw community/informant tips (CSV or free-text lines) into canonical Tactical Events, dedupe
near-duplicates, and strip personal identifiers from the reporter so the protected-channel promise
is kept. Output flows into the same event store as sensors.

Offline, stdlib only.

Input
-----
CSV with header (any subset): ts, text, lat, lon, reporter
  -- or -- a plain .txt file, one tip per line (then lat/lon/ts unknown).

PII protection: the `reporter` column is never written to the event; it is hashed to a stable
anonymous id so repeat reporters can be correlated without storing who they are.

Run
---
    python tip_intake.py --demo
    python tip_intake.py --csv tips.csv --events tips_events.json
    python tip_intake.py --txt tips.txt --events tips_events.json

Output: Tactical Events (source_type=ranger_report) + briefing.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import uuid

# keyword → threat_class for quick triage of free text
TRIAGE = [
    (re.compile(r"\b(spar|shot|gunshot|colpo|fucil)", re.I), "gunshot"),
    (re.compile(r"\b(trappol|snare|laccio|cappio)", re.I), "snare"),
    (re.compile(r"\b(camion|truck|veicolo|vehicle|plate|targa)", re.I), "vehicle"),
    (re.compile(r"\b(bracconier|poacher|armed|armato)", re.I), "poacher"),
    (re.compile(r"\b(motoseg|chainsaw|taglio|logging)", re.I), "chainsaw"),
]


def triage(text):
    for rx, cls in TRIAGE:
        if rx.search(text):
            return cls
    return "intrusion"


def anon_id(reporter):
    if not reporter:
        return None
    return "rep_" + hashlib.sha256(reporter.strip().lower().encode()).hexdigest()[:12]


def to_event(row, now):
    text = (row.get("text") or "").strip()
    lat = row.get("lat")
    lon = row.get("lon")
    ts = row.get("ts")
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": int(float(ts)) if ts else now,
        "source_type": "ranger_report",
        "source_id": anon_id(row.get("reporter")) or "anonymous_tip",
        "coordinates": {
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None, "elevation": None,
        },
        "threat_class": triage(text),
        "confidence": 0.5,
        "evidence_hash": None, "evidence_url": None,
        "metadata": {"tip_text": text, "needs_human_review": True},
    }


def dedup_key(ev):
    c = ev["coordinates"]
    norm = re.sub(r"\s+", " ", ev["metadata"]["tip_text"].lower())[:80]
    return hashlib.sha256(f"{ev['threat_class']}|{c['latitude']}|{c['longitude']}|{norm}".encode()).hexdigest()


DEMO_CSV = """ts,text,lat,lon,reporter
1782046800,Sentito un colpo di fucile vicino al fiume,-2.34,34.82,Maria R.
1782046900,Sentito sparo vicino al fiume,-2.34,34.82,Anon
1782050000,Visto camion sospetto con targa coperta,-2.31,34.88,Giuseppe
1782051000,Trappole metalliche lungo il sentiero nord,,,scout12
"""


def main():
    ap = argparse.ArgumentParser(description="WildGuard M6 tip intake")
    ap.add_argument("--csv")
    ap.add_argument("--txt")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--events")
    args = ap.parse_args()

    now = int(time.time())
    rows = []
    if args.demo:
        rows = list(csv.DictReader(io.StringIO(DEMO_CSV)))
    elif args.csv:
        rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    elif args.txt:
        rows = [{"text": ln.strip()} for ln in open(args.txt, encoding="utf-8")
                if ln.strip() and not ln.startswith("#")]
    else:
        print("Need --csv, --txt, or --demo.", file=sys.stderr)
        return 2

    events, seen = [], set()
    for row in rows:
        ev = to_event(row, now)
        k = dedup_key(ev)
        if k in seen:
            continue
        seen.add(k)
        events.append(ev)

    if args.events:
        json.dump(events, open(args.events, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"[ok] {len(events)} events -> {args.events}", file=sys.stderr)

    print("=" * 56)
    print(f"COMMUNITY TIPS — {len(rows)} raw, {len(events)} after dedupe (reporter PII hashed)")
    print("=" * 56)
    for e in events:
        c = e["coordinates"]
        print(f"  [{e['threat_class']}] {e['source_id']} @ {c['latitude']},{c['longitude']}")
        print(f"      \"{e['metadata']['tip_text']}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
