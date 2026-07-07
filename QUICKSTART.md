# WildGuard — Offline Quickstart

For a field team that just cloned this repo onto a laptop or Raspberry Pi. **No internet, no
server, no pip install** for the core workflow — Python 3 standard library only.

```bash
git clone <this-repo>
cd open-wildguard-hub/toolkit/python
```

## 1. See the whole pipeline in 5 seconds

```bash
python3 wildguard.py --demo --out /tmp/report
cat /tmp/report/SUMMARY.txt
```

You get a field briefing: top risk zones to patrol, unpredictable patrol routes, and a
court-ready case file per threat — built from synthetic events, entirely offline.

## 2. Run it on real detector output

Every detector in `toolkit/python/` writes the **same** canonical event
(`toolkit/data/event_schema.json`). Point them all at one folder, then run the pipeline over it.

```bash
mkdir events

# community tips  (reporter identity is hashed — protected channel)
python3 tip_intake.py   --demo --events events/tips.json
# collar geofence (alert when a tracked animal leaves the safe zone)
python3 gps_geofence.py --demo --events events/geo.json
# gunshot triangulation from >=3 synced acoustic nodes (TDoA)
python3 tdoa_locate.py  --demo --events events/gunshot.json
# node health     (which sensor died before a poacher walks the gap)
python3 node_health.py  --demo --events events/nodes.json
# camera edge inference writes events/<id>.json itself. Zero-training start:
#   pip install ultralytics opencv-python   (one-time, needs network)
#   python3 edge_infer_camera.py --source 0 --lat -2.33 --lon 34.83
# default weights (yolov8n, COCO) auto-download once, then run offline forever;
# person/car/truck detections map to canonical threat classes automatically

python3 wildguard.py --events-dir events/ --files-dir evidence/ --out report/
cat report/SUMMARY.txt
```

## What the runner does (the hub's job, without a hub)

```
events/*.json  →  VALIDATE (schema)  →  ENRICH (opt)  →  RISK  →  CASE FILES  →  report/
                  rejects.json          M5 taxonomy      M8       M9 + SHA-256
```

- **VALIDATE** — anything that doesn't match the canonical schema goes to `report/rejects.json`,
  never silently into a case. (`--enrich` adds live GBIF/IUCN species data; needs network.)
- **RISK** — `report/risk.geojson` (heatmap) + `report/routes.json` (patrol routes with a random
  component so no pattern is detectable).
- **CASE** — `report/cases/*.txt`, one signable forensic report per threat event, with a SHA-256
  integrity check. **If any evidence file was altered, the run exits non-zero** — a tamper signal
  you can wire into an alert.

## The output bundle (`report/`)

| File | Use |
|------|-----|
| `SUMMARY.txt` | Print it. Hand it to the ranger going out tonight. |
| `events.json` | All validated events, merged. |
| `risk.geojson` | Load as a heatmap layer (Leaflet, QGIS). |
| `routes.json` | Tonight's patrol waypoints per ranger. |
| `cases/*.txt` | Court-ready, signable, hash-verified. |
| `rejects.json` | Malformed detector output — fix the sensor. |
| `manifest.json` | Machine-readable run record. |

## 3. Query history + hand data to a researcher

The runner also writes a single **SQLite file** (`report/wildguard.sqlite`) — no server, opens in
QGIS / DB Browser / R / pandas. Ask it questions, or export standard formats:

```bash
# every gunshot in the last 30 days within 2 km of the north gate
python3 wg_store.py query --db report/wildguard.sqlite \
    --type gunshot --since 2026-06-01 --near -2.34 34.82 --radius-km 2

# exports a researcher already knows how to open
python3 wg_store.py export --db report/wildguard.sqlite --format geojson    --out events.geojson  # QGIS/Leaflet
python3 wg_store.py export --db report/wildguard.sqlite --format csv        --out events.csv      # R/pandas/Excel
python3 wg_store.py export --db report/wildguard.sqlite --format darwincore --out occurrence.csv  # GBIF standard
```

Ingest is idempotent — re-run detectors and re-ingest; the same incident never duplicates.

## Verify it works on your machine

```bash
cd toolkit && python3 -m pytest tests/ -q
```
