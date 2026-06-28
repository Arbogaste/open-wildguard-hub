# WildGuard AI — Goal & Milestone Plan

## Objective

Build a production-ready, offline-first anti-poaching platform that runs on constrained hardware,
works without connectivity, and generates court-ready evidence. The repo is both a deployable product
and a technical reference so any conservation team can fork one module at a time.

## Non-Negotiable Constraints

- No always-on connectivity required.
- No heavyweight orchestration (no Kubernetes, no managed cloud required).
- Every event produces a verifiable hash chain at capture time.
- No use-case logic that can't be explained and maintained by two people.

## Repo Layout

```
docs/modules/M01–M10.md   capability playbooks (what to deploy + recommended repos)
docs/prompts/             per-module agent prompts (implementation, testing, ops)
toolkit/python/           runnable Python scripts (edge inference, audio, risk model)
toolkit/arduino/          embedded firmware (PIR camera node, acoustic node)
toolkit/data/             canonical schemas (event_schema.json, patrol_schema.json)
index.html                static demo command center (offline HTML, no backend required)
```

---

## State of the Art (2026-06-28)

| Layer | Status | Gap |
|-------|--------|-----|
| Static dashboard (`index.html`) | ✅ demo works offline | No live data — reads hardcoded JSON |
| Event schema (`event_schema.json`) | ✅ canonical | Not enforced at ingestion yet |
| M2 toolkit (`edge_infer_camera.py`) | ✅ runnable on Pi/Jetson | No hub POST wiring |
| M3 toolkit (`tdoa_locate.py`, `train_audio_classifier.py`) | ✅ runnable | No hub POST wiring |
| M1 hub server (FastAPI + SQLite) | ❌ documented, not built | Core blocker for live data |
| M1 sync queue (store-and-forward) | ❌ schema only | Needed for offline-first |
| M1 WebSocket `/ws/alerts` | ❌ not built | Needed for real-time dashboard |
| Dashboard live data binding | ❌ reads `window.__MOCK__` only | Needs `/events` + WebSocket |
| M8 toolkit (`risk_model.py`) | ✅ runnable, stdlib-only, `--demo` works offline | No hub `/zones` POST wiring |
| M7 toolkit (`osint_scrape.py`, `ebay_adapter.py`, `osint_sites.json` 104 sites, `slang_dict.json`) | ✅ runnable, stdlib-only, rule-based (no LLM), `--demo`/`--sites` work; `skills/wildlife-osint` skill | No hub POST wiring |
| M5 toolkit (`gps_geofence.py`, `species_lookup.py`) | ✅ runnable, stdlib-only; species_lookup hooks GBIF/IUCN/Nominatim (live tested) | No hub POST wiring |
| Dashboard `index.html` | ✅ OSINT Leads tab (masked) + Toolkit Status tab (mock vision); **no external API calls** | reads local sample JSON only |
| `scriptplay.html` | ✅ YT metadata = real videos.insert body; Google-API setup note + example code; footer with Ollama/OpenRouter config | external calls only to user-configured OpenRouter/Ollama |
| `docs/INTEGRATION-MAP.md` | ✅ per-module: tool/why/repo-that-uses-it/how-to-start + free public APIs | activist-friendly index |
| `docs/ACCESSIBILITY.md` | ✅ WCAG 2.1 (W3C) AA checklist + patterns + self-audit | skip-link/reduced-motion applied to index+scriptplay |
| `readme.html` + footer links | ✅ accessible mission/README page (renders README.md) | linked from index + scriptplay footers |
| SEO/sitemap | ✅ `sitemap.xml` + `robots.txt`; scriptplay meta/og added | — |
| M6 toolkit (`tip_intake.py`) | ✅ runnable, stdlib-only, PII-hashed, `--demo` works | No hub POST wiring |
| M9 toolkit (`case_file.py`) | ✅ runnable, stdlib-only, integrity PASS/FAIL + case file | PDF output optional |
| M10 toolkit (`node_health.py`) | ✅ runnable, stdlib-only, `--demo` works | No hub POST wiring |
| M4 aerial-geo module | ◐ scaffolded docs | No code (needs Sentinel-2/NDVI — heavy deps) |
| M11–M20 pollution tier | ◐ design only (`docs/modules/M11-M20-pollution-tier.md`) | Optional separate tier; no code; reuses core (hub, schema, M9) |
| `docs/use-cases/` | ❌ empty | Needed for operator onboarding |
| Per-module agent prompts | ◐ partial | M2/M3 done; rest missing |

---

## Milestones

Each milestone is independent and can be assigned to a separate agent.
Each section states: what to build, exact files to create/edit, and what the dashboard gains.

---

### M0 — Hub Server (FastAPI + SQLite) ← **critical path**

**Why first:** all other modules POST events to the hub. Without this, everything stays offline mock.

**What to build:**

`hub/main.py` — FastAPI app:
```
POST /events           # ingest Tactical Event JSON → validate schema → insert events table
GET  /events           # query: ?since=ISO8601&zone=&type=&limit=100
GET  /events/{id}      # single event + evidence hashes
WS   /ws/alerts        # push new events to dashboard in real-time
GET  /health           # {status, event_count, queue_depth, uptime}
GET  /sync/status      # pending queue items + last_sync_at
POST /sync/flush       # manually trigger store-and-forward retry
```

`hub/db.py` — SQLite via `aiosqlite`:
```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,         -- alert|track|observation|evidence|sync
  source_id TEXT,
  lat REAL, lon REAL,
  ts TEXT NOT NULL,           -- ISO-8601 UTC
  payload TEXT NOT NULL,      -- full event JSON
  evidence TEXT,              -- JSON array of SHA-256 hashes
  synced INTEGER DEFAULT 0
);
CREATE TABLE sync_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT REFERENCES events(id),
  queued_at TEXT,
  attempts INTEGER DEFAULT 0
);
CREATE INDEX idx_events_ts ON events(ts DESC);
CREATE INDEX idx_events_type ON events(type);
```

`hub/sync.py` — background flush task (asyncio, every 60s):
- If upstream URL configured: POST pending events to `UPSTREAM_URL/events`.
- On success: `UPDATE events SET synced=1`.
- On failure: increment attempts (max 10), then dead-letter.

`hub/requirements.txt`:
```
fastapi>=0.111
uvicorn[standard]>=0.29
aiosqlite>=0.20
python-dotenv
```

`hub/Dockerfile` (Raspberry Pi compatible, linux/arm64):
```
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Validation:** `pytest hub/tests/` — test ingest, query pagination, WebSocket push, sync queue increment.

**Dashboard gains once M0 is live:**
- Live event feed panel (replace hardcoded `window.__MOCK__` with `GET /events`)
- Real-time alert badge via WebSocket (`/ws/alerts`)
- Sync status widget: "12 events pending upload / last sync 4m ago"
- Node health via `/health` (event_count, uptime)

---

### M1 — Toolkit Hub Wiring (M2 + M3 → hub POST)

**What to build:**

Wire existing toolkit scripts to the hub server. One env var `HUB_URL` controls whether events go local (file) or remote (POST).

Edit `toolkit/python/edge_infer_camera.py`:
- Add `--hub-url` CLI arg (default: `""` = write to `events/` folder only)
- On detection: `POST {hub_url}/events` with canonical Tactical Event JSON (already built — just add the POST call)
- Retry 3× with 2s backoff; if all fail, store to local `events/` folder (offline-first preserved)

Edit `toolkit/python/tdoa_locate.py`:
- Same `--hub-url` arg
- On triangulation result: POST event type `alert`, payload includes `{event_type:"gunshot", coords:{lat,lon}, confidence, node_ids}`

**No new files needed.** ~30 lines each.

**Dashboard gains:**
- Camera detection events appear live on map (M2 pins)
- Gunshot triangulation appears as map cluster with radius uncertainty circle (M3)
- Evidence gallery: thumbnail grid of `evidence/*.jpg` served from hub `GET /evidence/{hash}`

---

### M2 — Dashboard Live Data Binding

**What to build:**

Edit `index.html` (or extract to `js/dashboard.js`):

```javascript
// Replace window.__MOCK__ with real fetch + WebSocket
const HUB = localStorage.getItem('hub_url') || '';

async function loadEvents() {
  if (!HUB) { useDemo(); return; }
  const res = await fetch(`${HUB}/events?limit=200`);
  const { events } = await res.json();
  renderMap(events);
  renderFeed(events);
}

// WebSocket for real-time push
function connectWS() {
  const ws = new WebSocket(`${HUB.replace('http','ws')}/ws/alerts`);
  ws.onmessage = e => {
    const ev = JSON.parse(e.data);
    addPinToMap(ev);
    prependToFeed(ev);
    flashAlertBadge();
  };
  ws.onclose = () => setTimeout(connectWS, 5000); // reconnect
}
```

Add "Hub URL" settings panel (bottom-right gear icon): input field, `localStorage.setItem('hub_url', val)`, test connection button (`GET /health`).

Falls back to demo mode if `hub_url` empty or unreachable — preserves standalone demo.

**Dashboard gains:**
- Live map pins from real events
- Real-time alert badge
- "Hub connected / offline demo" status chip
- Event detail drawer (click pin → show full event JSON + evidence hashes)

---

### M3 — Evidence Package & Chain of Custody Viewer

**What to build:**

`hub/evidence.py` — FastAPI router:
```
GET  /evidence/{sha256}     # serve raw file (image/audio) by hash — hash IS the filename
POST /evidence/upload       # multipart upload: file → compute SHA-256 → store → return hash
GET  /evidence/{sha256}/verify  # recompute hash, return {ok: bool, stored_at, size}
GET  /cases/{event_id}/package  # zip: event JSON + all evidence files + custody_log.txt
```

`custody_log.txt` format (append-only, inside the zip):
```
[ISO-8601] CAPTURED   node_edge_42  sha256=abc123  lat=-2.33 lon=34.83
[ISO-8601] UPLOADED   hub_v1.0      sha256=abc123  ip=192.168.1.10
[ISO-8601] VERIFIED   analyst_007   sha256=abc123  result=OK
[ISO-8601] EXPORTED   case_2026_001 sha256=abc123  format=zip
```

**Dashboard gains:**
- Evidence gallery tab: grid of captured frames with hash labels
- Chain of custody timeline per event (vertical stepper UI)
- "Download case package" button → triggers `GET /cases/{id}/package`
- Hash verify badge (green checkmark / red X) per evidence item

---

### M4 — Risk Heatmap (M8 Prediction Tier 1)

**What to build:**

`toolkit/python/risk_model.py` — standalone script, no ML required for tier 1:

Inputs (all optional, degrades gracefully):
- `events.sqlite` (or `GET /events` from hub) — past incident locations + timestamps
- `patrol_log.csv` — coverage history (optional)
- `moon_phase` — computed locally (ephem or hardcoded table)
- `hour_of_day`, `day_of_week`

Algorithm (tier 1, no training needed):
```python
# Grid: 0.01° cells over bounding box
# Score each cell:
#   base_score = incident_count_last_30d / area_km2
#   recency_weight = sum(exp(-days_ago / 7) for each incident)
#   moon_multiplier = 1.3 if moon_phase > 0.7 else 1.0  # poachers prefer dark
#   patrol_discount = 0.5 if cell_patrolled_last_7d else 1.0
#   final_score = base_score * recency_weight * moon_multiplier * patrol_discount
```

Output: `risk_grid.json` — GeoJSON FeatureCollection, each cell has `score` + `hex_color`.

Add `GET /risk/grid` to hub that serves latest `risk_grid.json` (recomputed on each call or cached 1h).

**Dashboard gains:**
- Risk heatmap layer toggle on map (choropleth via Leaflet `L.geoJSON`)
- Daily briefing panel: "Top 3 risk zones today" with recommended patrol time window
- Trend chip: "Risk in sector B +18% vs last week"

---

### M5 — Node Health Monitor (M10 Resilience Tier 2)

**What to build:**

`hub/nodes.py` — FastAPI router:
```
POST /nodes/heartbeat   # body: {node_id, battery_pct, lat, lon, fw_version, ts}
GET  /nodes             # list all nodes + last_seen + battery + status
GET  /nodes/{id}        # single node history
```

`hub/db.py` additions:
```sql
CREATE TABLE node_heartbeats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  battery_pct INTEGER,
  lat REAL, lon REAL,
  fw_version TEXT,
  payload TEXT
);
CREATE VIEW node_latest AS
  SELECT node_id, MAX(ts) as last_seen, battery_pct, lat, lon, fw_version
  FROM node_heartbeats GROUP BY node_id;
```

Node status rules (computed at query time):
- `online` = last_seen < 15 min ago
- `warning` = last_seen 15–60 min OR battery_pct < 20
- `offline` = last_seen > 60 min
- `critical` = battery_pct < 10

Edit `toolkit/arduino/pir_camera_node.ino`: send heartbeat to `HUB_URL/nodes/heartbeat` every 10 min via Wi-Fi/LoRa.

**Dashboard gains:**
- Node status grid: colored circles (green/yellow/red) per node on sidebar
- Battery gauge per node (progress bar)
- "2 nodes offline" alert badge
- Node map layer (click node pin → show battery history sparkline)

---

### M6 — Docs: use-cases/ (Operator Onboarding)

**What to build (docs only, no code):**

`docs/use-cases/UC01-small-sanctuary.md`
- Scenario: 1 ranger, 1 Pi, 1 camera, no connectivity. What to deploy, step by step.
- Covers: M1 (Pi hub), M2 (edge_infer_camera.py), M9 (offline evidence).

`docs/use-cases/UC02-community-reserve.md`
- Scenario: 5 rangers, GSM coverage, community tip channel.
- Covers: M1 hub on VPS (€5/mo), M6 tip portal (LimeSurvey), M3 audio nodes.

`docs/use-cases/UC03-transfrontier.md`
- Scenario: 3 parks, shared EarthRanger, satellite uplink.
- Covers: M1 multi-site sync, M4 drones, M5 GPS collars, M9 cross-border legal.

Each use-case doc must include:
- Hardware BOM with price estimate
- Software setup commands (copy-paste)
- First-day checklist
- What to do when the hub goes offline

**Dashboard gains:**
- "Deploy Guide" link in hub sidebar (links to relevant UC doc based on detected tier)
- Onboarding wizard (3-step): "How many rangers? Connectivity? Budget?" → recommends UC doc

---

## Dashboard Expansion Map

Summary of what each milestone unlocks in `index.html`:

| Milestone | Dashboard Feature |
|-----------|-------------------|
| M0 hub | Live event feed, real-time WS alerts, sync status widget |
| M1 toolkit wiring | Map pins from real detections, evidence thumbnail on click |
| M2 live binding | Hub connect/disconnect, event detail drawer, offline fallback |
| M3 evidence viewer | Evidence gallery, chain of custody timeline, case zip download |
| M4 risk heatmap | Risk layer toggle, daily briefing panel, zone trend chip |
| M5 node monitor | Node status grid, battery gauges, offline node alert |
| M6 use-cases | Deploy guide link, onboarding wizard |

---

## Agent Handoff Instructions

When an agent picks up a milestone:

1. Read `dev.md` for architecture rules and coding conventions.
2. Read the relevant `docs/modules/M0N-*.md` for design context and recommended repos.
3. Build the code in the exact files specified above. Do not create additional abstractions.
4. Add tests in `hub/tests/test_MN_*.py` or `toolkit/tests/`.
5. Update this file: mark milestone ✅ and fill in "State of the Art" table.
6. Do NOT commit/push — user manages git.

Priority order: **M0 → M2 → M1 → M3 → M4 → M5 → M6**
(Hub first, live dashboard second, wiring third, then advanced features.)

---

## Definition of Done

Platform is done when:
- A ranger on a Raspberry Pi Zero 2W can run `python hub/main.py` and have `edge_infer_camera.py` posting real detections to it.
- The dashboard at `index.html` shows those detections live.
- Every detection produces a SHA-256-verified evidence package downloadable as a zip.
- A new reserve can be onboarded in one day using a UC doc.
