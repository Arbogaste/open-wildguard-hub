# M1 — Hub Architecture, Interoperability & Governance

> Mission: a modular hub (field / operation-room / intelligence layers) with shared data contracts,
> not a monolith. Everything speaks the same Tactical Event schema so subsystems compose freely.

## 1. Goal
Define the spine of the platform: user roles & permissions, a single canonical event format,
escalation runbooks, and three field tiers that match real reserve budgets (phone-only →
Raspberry Pi → full server). Adopt SMART for standardized patrol reporting and EarthRanger as the
real-time operations view. The hub's job is to receive events from every sensor module, store them
reliably, serve them to the dashboard, and queue them for sync when the connection drops.

## 2. Field tiers
| Tier | Stack | Cost target |
|------|-------|-------------|
| Essential | Android + SMART Mobile or CyberTracker + static dashboard | near-zero |
| Intermediate | Raspberry Pi 4 + FastAPI + SQLite + Leaflet map | < $100 server |
| Advanced | Any Linux server + FastAPI + PostgreSQL + EarthRanger integration + role-based access | scales to multi-site |

## 3. Recommended repos
| Repo | Take this | Notes |
|------|-----------|-------|
| [FaunaScope](https://github.com/tanmaynikhare45/FaunaScope-Wildlife-Camera-Trap-Analysis-Platform) | FastAPI hub blueprint, SQLite→Postgres, Leaflet map, auth skeleton | **best starting point** for the Intermediate tier |
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | event ingestion service + WebSocket push pattern | wire to the hub's `/events` endpoint |
| [DSA Alert Engine](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | offline CSV sync pattern, Dijkstra nearest-ranger routing | good reference for store-and-forward |

External: **SMART** (smartconservationtools.org) — patrol data standard. **EarthRanger** (earthranger.com) — real-time ops. **CyberTracker** — offline field data collection.

## 4. Core API design (FastAPI + SQLite)
The hub is a central FastAPI service that:
- Receives Tactical Events from all sensor modules (M2–M10) via `POST /events`
- Stores them in SQLite (single file, trivial backup, runs on a Pi)
- Queues outbound events in a `sync_queue` table when upstream connectivity is down
- Flushes the queue opportunistically when connectivity returns (store-and-forward)
- Serves events to the dashboard via `GET /events?since=&zone=&type=`
- Exposes a WebSocket `/ws/alerts` for real-time push to the map

Minimal table layout:
```sql
CREATE TABLE events (
    id          TEXT PRIMARY KEY,   -- UUID from event_schema.json
    type        TEXT NOT NULL,       -- alert | track | observation | sync
    source_id   TEXT,               -- sensor / node / user ID
    lat         REAL,
    lon         REAL,
    ts          TEXT NOT NULL,       -- ISO-8601 UTC
    payload     TEXT,               -- full Tactical Event JSON
    evidence    TEXT,               -- SHA-256 hash list (see M9)
    synced      INTEGER DEFAULT 0   -- 0=pending, 1=sent upstream
);

CREATE TABLE sync_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT REFERENCES events(id),
    queued_at   TEXT,
    attempts    INTEGER DEFAULT 0
);
```

Key endpoints:
```
POST  /events            — ingest one Tactical Event (from any module)
GET   /events            — query with filters: since, zone, type, source_id
GET   /events/{id}       — single event + evidence manifest
GET   /zones             — GeoJSON zone definitions (patrol areas, red zones)
POST  /zones             — add / update zone
GET   /nodes             — registered sensor nodes + last-seen
GET   /sync/queue        — pending outbound events (for external sync agent)
POST  /sync/flush        — trigger opportunistic flush to upstream / EarthRanger
WS    /ws/alerts         — real-time event stream to dashboard
```

## 5. Scripts & toolkit
- Canonical event schema: [`../../toolkit/data/event_schema.json`](../../toolkit/data/event_schema.json) — all modules must emit this.
- All Python toolkit scripts (`train_camera_trap_classifier.py`, `edge_infer_camera.py`, `train_audio_classifier.py`, `tdoa_locate.py`) already produce valid Tactical Events and post them to `POST /events`.

Quickstart (Raspberry Pi / any Linux):
```bash
pip install fastapi uvicorn aiosqlite
uvicorn hub:app --host 0.0.0.0 --port 8000
# Open http://<pi-ip>:8000/docs for auto-generated API docs
```

## 6. Agent prompts
Paste into any LLM agent:

**Prompt A — build the hub:**
```
I am building a wildlife anti-poaching platform hub. Build a minimal FastAPI application
with a SQLite backend that:
1. Accepts POST /events with a JSON body matching this schema: [paste event_schema.json]
2. Stores events in a table with columns: id, type, source_id, lat, lon, ts, payload, synced
3. Adds unsynced events to a sync_queue table
4. Exposes GET /events with filters: since (ISO-8601), zone (optional bbox), type (optional)
5. Has a background task that flushes sync_queue when a connectivity check passes
6. Uses aiosqlite for async I/O, runs on Python 3.10+
Return the full hub.py file and a requirements.txt.
```

**Prompt B — add WebSocket real-time push:**
```
Extend the FastAPI hub above to add:
- WS /ws/alerts endpoint that broadcasts every new event to all connected dashboard clients
- On POST /events, after DB insert, publish the event JSON to all open WebSocket connections
- On reconnect, client receives the last 20 events as catch-up
Return only the changed sections of hub.py.
```

**Prompt C — EarthRanger integration:**
```
Add an integration module to the FastAPI hub that:
1. Reads EarthRanger_URL and EarthRanger_TOKEN from env vars
2. On sync/flush, POSTs unsynced events to EarthRanger's /api/v1.0/activity endpoint
3. Marks events as synced=1 on success; increments attempts and backs off on failure
4. Does not block the main event ingestion path
Return the integration module and how to wire it into hub.py.
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Choose tier: Essential (no server) or Intermediate/Advanced (FastAPI).
- [ ] If Intermediate+: clone FaunaScope, strip the React frontend, keep the FastAPI backend.
- [ ] Create the SQLite schema above. Run `POST /events` with a test payload.
- [ ] Wire at least one sensor module (M2 edge camera or M3 audio node) to `POST /events`.
- [ ] Add the sync_queue + flush background task. Simulate offline: disconnect, generate events, reconnect, confirm flush.
- [ ] Add role model: `ranger` (write events, read own zone), `analyst` (read all, no write), `authority` (read all + evidence packages).
- [ ] Optional: wire EarthRanger flush (Prompt C above).
- [ ] Test: 72h continuous run, confirm no DB corruption, no missed events on reconnect.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Small sanctuary (1–5 rangers) | Essential tier only — phones + SMART + dashboard, no server needed |
| Transfrontier park | multi-site sync: each site runs its own hub, syncs to a shared upstream; cross-border roles |
| Marine protected area | swap trail map for coastal + AIS vessel layers; events include vessel ID + bearing |
| High-corruption risk | air-gapped hub (no internet) + physical USB sync to secure off-site backup |
