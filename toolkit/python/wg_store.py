#!/usr/bin/env python3
"""
WildGuard — single-file event store, query, and researcher-grade export.

A folder of JSON files is fine for one patrol. It does not scale: a reserve accumulating events
for a year cannot answer "every gunshot in the last 30 days within 2 km of the north gate" from
loose files. The antirez-clean answer is not a server — it is one SQLite file. Embedded, offline,
durable, queryable, zero-config, runs on a Raspberry Pi and opens in QGIS / DB Browser / R / pandas
unchanged. `sqlite3` ships with Python, so a cloned repo needs no install.

This module is the query + export layer over the canonical Tactical Events (event_schema.json):

    # load events (from wildguard.py output, or any detector's events/ folder) into the store
    python wg_store.py ingest report/events.json --db reserve.sqlite
    python wg_store.py ingest events/            --db reserve.sqlite   # a folder works too

    # ask questions (all filters optional, combine freely)
    python wg_store.py query --db reserve.sqlite --type gunshot --since 2026-06-01
    python wg_store.py query --db reserve.sqlite --near -2.34 34.82 --radius-km 2 --min-conf 0.7

    # hand a researcher a file they already know how to open
    python wg_store.py export --db reserve.sqlite --format csv         --out events.csv
    python wg_store.py export --db reserve.sqlite --format geojson     --out events.geojson
    python wg_store.py export --db reserve.sqlite --format darwincore  --out occurrence.csv

Idempotent: re-ingesting the same events (same event_id) updates in place, never duplicates.
Stdlib only. No ORM, no migrations framework — one table, one file, forever.
"""
import argparse
import csv
import json
import math
import os
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id     TEXT PRIMARY KEY,
    timestamp    INTEGER,
    source_type  TEXT,
    source_id    TEXT,
    latitude     REAL,
    longitude    REAL,
    threat_class TEXT,
    confidence   REAL,
    evidence_hash TEXT,
    payload      TEXT NOT NULL          -- full canonical event JSON, nothing lost
);
CREATE INDEX IF NOT EXISTS idx_events_ts    ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_type  ON events(threat_class);
"""


def connect(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


# --------------------------------------------------------------------------- ingest
def _iter_events(path):
    """Yield events from a JSON file (object or array) or a folder of such files."""
    if os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            if name.endswith(".json"):
                yield from _iter_events(os.path.join(path, name))
        return
    data = json.load(open(path, encoding="utf-8"))
    yield from (data if isinstance(data, list) else [data])


def ingest(db_path, src_path):
    con = connect(db_path)
    n = 0
    with con:
        for ev in _iter_events(src_path):
            eid = ev.get("event_id")
            if not eid:
                continue
            c = ev.get("coordinates", {}) or {}
            con.execute(
                """INSERT INTO events (event_id, timestamp, source_type, source_id,
                       latitude, longitude, threat_class, confidence, evidence_hash, payload)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(event_id) DO UPDATE SET
                       timestamp=excluded.timestamp, source_type=excluded.source_type,
                       source_id=excluded.source_id, latitude=excluded.latitude,
                       longitude=excluded.longitude, threat_class=excluded.threat_class,
                       confidence=excluded.confidence, evidence_hash=excluded.evidence_hash,
                       payload=excluded.payload""",
                (eid, ev.get("timestamp"), ev.get("source_type"), ev.get("source_id"),
                 c.get("latitude"), c.get("longitude"), ev.get("threat_class"),
                 ev.get("confidence"), ev.get("evidence_hash"),
                 json.dumps(ev, ensure_ascii=False)))
            n += 1
    con.close()
    return n


# --------------------------------------------------------------------------- query
def _iso_to_unix(s):
    """Accept unix seconds or ISO-8601 (date or datetime). Returns int seconds."""
    if s is None:
        return None
    try:
        return int(float(s))
    except ValueError:
        pass
    import datetime as dt
    s = s.replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        d = dt.datetime.fromisoformat(s + "T00:00:00")
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp())


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def query(db_path, threat_class=None, since=None, until=None, min_conf=None,
          near=None, radius_km=None, source_type=None, limit=None):
    con = connect(db_path)
    sql = "SELECT payload, latitude, longitude FROM events WHERE 1=1"
    args = []
    if threat_class:
        sql += " AND threat_class = ?"; args.append(threat_class)
    if source_type:
        sql += " AND source_type = ?"; args.append(source_type)
    if since is not None:
        sql += " AND timestamp >= ?"; args.append(_iso_to_unix(since))
    if until is not None:
        sql += " AND timestamp <= ?"; args.append(_iso_to_unix(until))
    if min_conf is not None:
        sql += " AND confidence >= ?"; args.append(min_conf)
    sql += " ORDER BY timestamp DESC"
    rows = con.execute(sql, args).fetchall()
    con.close()

    out = []
    for r in rows:
        if near and radius_km is not None:
            if r["latitude"] is None or r["longitude"] is None:
                continue
            if haversine_km(near[0], near[1], r["latitude"], r["longitude"]) > radius_km:
                continue
        out.append(json.loads(r["payload"]))
        if limit and len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- export
CSV_COLS = ["event_id", "timestamp", "source_type", "source_id", "latitude", "longitude",
            "threat_class", "confidence", "evidence_hash"]


def export_csv(events, out):
    w = csv.DictWriter(open(out, "w", newline="", encoding="utf-8"), fieldnames=CSV_COLS,
                       extrasaction="ignore")
    w.writeheader()
    for ev in events:
        row = dict(ev)
        c = ev.get("coordinates", {}) or {}
        row["latitude"], row["longitude"] = c.get("latitude"), c.get("longitude")
        w.writerow(row)


def export_geojson(events, out):
    feats = []
    for ev in events:
        c = ev.get("coordinates", {}) or {}
        if c.get("latitude") is None or c.get("longitude") is None:
            continue
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point",
                                   "coordinates": [c["longitude"], c["latitude"]]},
                      "properties": {k: ev.get(k) for k in
                                     ("event_id", "timestamp", "threat_class", "confidence",
                                      "source_type", "source_id")}})
    json.dump({"type": "FeatureCollection", "features": feats},
              open(out, "w", encoding="utf-8"), indent=2)


def export_darwincore(events, out):
    """Darwin Core Occurrence CSV — the GBIF/biodiversity standard researchers ingest directly.
    Maps our fields to DwC terms so a detection can enter a research dataset without rework."""
    cols = ["occurrenceID", "eventDate", "decimalLatitude", "decimalLongitude",
            "scientificName", "occurrenceRemarks", "basisOfRecord", "recordedBy"]
    w = csv.DictWriter(open(out, "w", newline="", encoding="utf-8"), fieldnames=cols)
    w.writeheader()
    import datetime as dt
    for ev in events:
        c = ev.get("coordinates", {}) or {}
        m = ev.get("metadata", {}) or {}
        tax = (m.get("taxonomy") or {})
        ts = ev.get("timestamp")
        date = (dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()
                if isinstance(ts, (int, float)) else "")
        w.writerow({
            "occurrenceID": ev.get("event_id"),
            "eventDate": date,
            "decimalLatitude": c.get("latitude"),
            "decimalLongitude": c.get("longitude"),
            "scientificName": tax.get("scientific_name") or m.get("species_suspected") or "",
            "occurrenceRemarks": f"{ev.get('threat_class')} (confidence {ev.get('confidence')})",
            "basisOfRecord": "MachineObservation",
            "recordedBy": ev.get("source_id") or ev.get("source_type") or "WildGuard",
        })


EXPORTERS = {"csv": export_csv, "geojson": export_geojson, "darwincore": export_darwincore}


# --------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description="WildGuard single-file SQLite store / query / export")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_in = sub.add_parser("ingest", help="load events JSON (file or folder) into the store")
    p_in.add_argument("src", help="events.json, a single event, or a folder of them")
    p_in.add_argument("--db", required=True)

    p_q = sub.add_parser("query", help="filter events (prints JSON array)")
    p_q.add_argument("--db", required=True)
    p_q.add_argument("--type", dest="threat_class", help="threat_class, e.g. gunshot")
    p_q.add_argument("--source-type")
    p_q.add_argument("--since", help="unix or ISO-8601 (inclusive)")
    p_q.add_argument("--until", help="unix or ISO-8601 (inclusive)")
    p_q.add_argument("--min-conf", type=float)
    p_q.add_argument("--near", nargs=2, type=float, metavar=("LAT", "LON"))
    p_q.add_argument("--radius-km", type=float)
    p_q.add_argument("--limit", type=int)

    p_e = sub.add_parser("export", help="export to a researcher-friendly file")
    p_e.add_argument("--db", required=True)
    p_e.add_argument("--format", required=True, choices=list(EXPORTERS))
    p_e.add_argument("--out", required=True)
    for a in ("threat_class", "since", "until"):
        p_e.add_argument("--" + a.replace("threat_class", "type"), dest=a)
    p_e.add_argument("--min-conf", type=float)

    args = ap.parse_args()

    if args.cmd == "ingest":
        n = ingest(args.db, args.src)
        print(f"[ok] {n} events -> {args.db}", file=sys.stderr)
        return 0
    if args.cmd == "query":
        evs = query(args.db, args.threat_class, args.since, args.until, args.min_conf,
                    args.near, args.radius_km, args.source_type, args.limit)
        print(json.dumps(evs, indent=2, ensure_ascii=False))
        print(f"[{len(evs)} events]", file=sys.stderr)
        return 0
    if args.cmd == "export":
        evs = query(args.db, getattr(args, "threat_class", None), getattr(args, "since", None),
                    getattr(args, "until", None), getattr(args, "min_conf", None))
        EXPORTERS[args.format](evs, args.out)
        print(f"[ok] {len(evs)} events -> {args.out} ({args.format})", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
