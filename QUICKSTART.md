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
# node health     (which sensor died before a poacher walks the gap)
python3 node_health.py  --demo --events events/nodes.json
# camera edge inference writes events/<id>.json itself (needs a model — see toolkit/python/requirements.txt)

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

## Verify it works on your machine

```bash
cd toolkit && python3 -m pytest tests/ -q
```
