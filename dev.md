# WildGuard AI Technical Guide

This document is the technical master reference for `open-wildguard-hub`.
It defines the architecture, data contracts, implementation rules, and the documentation strategy for future use-case specific guides.

## 1. Design Principles

The platform must remain usable in remote conservation environments where power, bandwidth, and hardware are limited.

1. Simplicity
   - Prefer small, well-understood components.
   - Avoid unnecessary abstraction and orchestration.
   - Keep behavior easy to inspect and debug.

2. Offline-first operation
   - Local workflows must continue when the network is unavailable.
   - Synchronization is opportunistic and should never be a hard dependency.
   - Every critical action needs a local fallback.

3. Flat data structures
   - Prefer JSON, GeoJSON, CSV, and line-delimited logs.
   - Keep schemas explicit and versioned.
   - Avoid nested structures that make merging and auditing harder.

4. Field robustness
   - The system must fail gracefully.
   - Partial data, delayed sync, and missing telemetry are normal conditions.
   - The output should remain useful even if one subsystem is degraded.

5. Documentation-first development
   - Every major capability must be explained in writing.
   - The codebase should always have a matching operational guide.
   - New use cases should be documented as separate files when they become stable.

## 2. Project Scope

`open-wildguard-hub` is an orchestrator for anti-poaching capabilities, not a single monolithic application.
It should combine field operations, edge intelligence, data persistence, and evidence handling in a way that remains portable across deployments.

The repository is expected to grow along three layers:

- Field layer: ranger workflows, offline reporting, local sensors, and edge devices.
- Operations layer: command center UI, alerts, mapping, and coordination.
- Intelligence layer: OSINT, prediction, evidence packaging, and analytics.

## 3. Canonical Data Contracts

The system should revolve around a small set of stable records.

### Tactical Event

Every detected incident should normalize into a canonical event record.

```json
{
  "event_id": "uuid4",
  "timestamp": 1782046800,
  "source_type": "camera_trap",
  "source_id": "node_edge_42",
  "coordinates": {
    "latitude": -2.3333,
    "longitude": 34.8333,
    "elevation": 1420.5
  },
  "threat_class": "poacher",
  "confidence": 0.89,
  "evidence_hash": "sha256...",
  "evidence_url": "/media/...",
  "metadata": {
    "species_detected": "elephant",
    "suspect_count": 2,
    "schedule": "Schedule I"
  }
}
```

### Node Status

Field hardware should expose a compact health record.

```json
{
  "node_id": "node_edge_42",
  "battery_level": 78.5,
  "signal_dbm": -82,
  "uptime": 345600,
  "disk_free_bytes": 128493021,
  "model_version": "yolov8n-v2.1",
  "status": "healthy"
}
```

### Patrol Route

Route output should remain simple and auditable.

```json
{
  "route_id": "route_2026_06_20_01",
  "ranger_team_id": "team_alpha",
  "waypoints": [
    { "lat": -2.333, "lon": 34.833, "seq": 1, "dwell_time_seconds": 600 },
    { "lat": -2.345, "lon": 34.845, "seq": 2, "dwell_time_seconds": 1800 }
  ],
  "mst_length_meters": 4820,
  "risk_score_average": 0.72
}
```

## 4. Recommended Architecture

The repository should stay close to the following shape:

```text
open-wildguard-hub/
├── backend/
│   ├── main.py
│   ├── database.py
│   └── services/
│       ├── ml_pipeline.py
│       ├── audio_dsp.py
│       ├── osint.py
│       └── prediction.py
├── frontend/
│   └── index.html
├── scripts/
│   ├── edge_vision.py
│   └── sync_worker.py
├── goal.md
├── README.md
└── antirez.md
```

This structure is intentionally small.
The goal is to keep the field runtime understandable and to avoid a sprawling service graph.

## 5. Module Responsibilities

### M1. Governance and API

- Provide the canonical backend entry point.
- Own the event schema, local persistence, and synchronization rules.
- Expose a small, explicit API that can be used by the dashboard and field tools.

### M2. Edge Vision

- Detect humans, vehicles, and relevant anomalies on edge devices.
- Filter obvious false positives locally before escalating.
- Run on low-cost hardware where feasible.

### M3. Acoustic Monitoring

- Process low-bitrate audio streams locally.
- Detect signatures such as gunshots, chainsaws, and engines.
- Use time-difference-of-arrival logic where multiple sensors are available.

### M4. Geospatial Monitoring

- Represent coordinates and routes with simple geospatial structures.
- Render alerts, hotspots, and patrol paths on a map.
- Support offline tiles or cached map assets.

### M5. Species Intelligence

- Track collars, beacons, and other telemetry sources.
- Normalize geofencing violations and abnormal movement into alerts.
- Preserve a clean boundary between telemetry and derived inference.

### M6. Field Reporting

- Support offline field notes, sightings, and structured reports.
- Synchronize submissions when connectivity returns.
- Keep forms stable and easy to reuse across use cases.

### M7. OSINT Intake

- Ingest open sources, feeds, and documents that are relevant to conservation intelligence.
- Normalize extracted signals into searchable records.
- Keep legally sensitive workflows isolated when necessary.

### M8. Prediction and Patrol Planning

- Estimate risk from history, habitat, and field observations.
- Generate route suggestions and hotspot views.
- Favor explainable logic over opaque automation.

### M9. Evidence and Compliance

- Hash and timestamp media as soon as it is captured.
- Keep original media, derived artifacts, and metadata separate.
- Maintain an auditable chain of custody.

### M10. Resilience and Federation

- Track health, versioning, and maintenance state.
- Support controlled model and dataset updates.
- Allow future multi-site collaboration without breaking the local-first model.

## 6. Runtime Rules

- Direct SQL is acceptable when it keeps the system simpler and more auditable.
- Synchronization workers must never block local capture or local response.
- Data should be stored in forms that are easy to export, review, and back up.
- Every automated action must have a clear trigger and a clear fallback.
- Any feature that depends on the network must degrade into a useful local mode.

## 7. Edge Hardware Guidance

The platform should support low-cost and rugged field devices:

- Raspberry Pi class systems.
- Old laptops and rugged mini PCs.
- Arduino or ESP32-class sensor nodes for very small workloads.
- Solar-powered deployments with intermittent connectivity.

The preferred behavior is:

- Sleep when idle.
- Wake on signal.
- Capture only when needed.
- Transmit compact payloads.

## 8. Frontend and Operator UX

The HTML dashboard should behave like an operator guide, not only a visual demo.

Requirements:

- Show the current system status clearly.
- Present the roadmap in terms of real implementation steps.
- Explain how to respond to field scenarios.
- Provide practical documentation for deployment and maintenance.
- Keep the UI usable on small screens and low-power devices.

## 9. Documentation Strategy

The current `dev.md` is the master technical document. The operator-facing, capability-specific
content now lives in **`docs/`** — this is the heart of the project (the "repo of repos").

Current structure (live):

- `docs/README.md` — master index: recommended-repo catalog (the 16 upstream projects), use-case
  matrix, and how to use the playbooks.
- `docs/modules/M01..M10.md` — one **playbook per capability module** (Section 5 here). Each lists
  recommended repos, hardware, runnable scripts, agent prompts, milestones, and international use
  cases. M2 (edge vision) and M3 (bioacoustics) are fully fleshed; M1, M4–M10 are scaffolds being
  filled to the same depth.
- `docs/modules/_TEMPLATE.md` — the playbook structure every module follows.
- `docs/prompts/` — paste-into-any-agent prompt packs to drive an LLM agent through each milestone.
- `toolkit/python/` — runnable training/inference scripts (camera-trap classifier, edge inference,
  audio classifier, TDoA localizer) + `requirements.txt`.
- `toolkit/arduino/` — edge node firmware (PIR camera node, acoustic node).
- `toolkit/data/` — canonical `event_schema.json` (the Tactical Event) + open-dataset pointers.

Still planned (deployment guides, one file per scenario):

- `docs/use-cases/*.md` (camera-trap-intrusion, gunshot-response, offline-field-reporting,
  evidence-handling, osint-intake, patrol-planning)
- `docs/deployment/edge-node.md`, `docs/deployment/command-center.md`

The rule is simple:

- Keep `dev.md` as the technical map.
- Move repeated operational instructions into dedicated documents.
- Keep each document focused on one workflow or deployment mode.

## 10. Internationalization

Localization must stay flat, explicit, and resource-based.

Rules:

- Use flat JSON locale files.
- Keep translation keys stable.
- Avoid nested locale trees.
- Use a deterministic fallback chain:
  1. External locale file
  2. Bundled offline fallback
  3. Raw key

This avoids blocking the UI when a translation is missing.

## 11. Production Readiness Checklist

The project is moving toward production readiness when:

- The data model is stable.
- The local backend runs reliably.
- The UI explains real workflows.
- The system still works offline.
- Evidence is preserved correctly.
- Documentation covers both operation and extension.
- New use cases can be added without rewriting the core.

## 12. Writing Standard for Future Docs

Use technical English, keep the tone direct, and document actual behavior rather than intentions.

Prefer:

- explicit constraints
- clear fallback behavior
- concrete steps
- stable file names
- predictable interfaces

Avoid:

- vague marketing language
- hidden assumptions
- undocumented state
- one-off instructions that cannot be reused
