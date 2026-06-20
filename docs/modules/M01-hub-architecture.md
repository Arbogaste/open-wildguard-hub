# M1 — Hub, Interoperability & Governance

> Mission: a modular hub (field / operation-room / intelligence layers) with shared data contracts,
> not a monolith. Everything speaks the same event schema so subsystems compose.

## 1. Goal
Define the spine: roles & permissions, common formats (GeoJSON/GPX, Tactical Event), escalation
runbooks, and three reusable tiers (Essential phone-only → Intermediate → Advanced). Adopt **SMART**
for standardized patrol/biodiversity reporting and **EarthRanger** as the real-time operational view.

## 2. Field tiers
| Tier | Stack |
|------|-------|
| Essential | Android + SMART Mobile/CyberTracker + this hub's static dashboard |
| Intermediate | + FastAPI hub (FaunaScope blueprint) + SQLite + Leaflet map |
| Advanced | + EarthRanger integration, multi-site sync, role-based access |

## 3. Recommended repos
| Repo | Take this |
|------|-----------|
| [FaunaScope](https://github.com/tanmaynikhare45/FaunaScope-Wildlife-Camera-Trap-Analysis-Platform) | React+FastAPI hub blueprint, SQLite→Postgres, Leaflet |
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | event ingestion + websockets pattern |

External: **SMART** (smartconservationtools.org), **EarthRanger** (earthranger.com), **CyberTracker**.

## 4-5. Schema & scripts
Canonical event: [`../../toolkit/data/event_schema.json`](../../toolkit/data/event_schema.json). All
modules emit it. Build the hub API around storing + querying these.

## 7. Milestones
- [ ] Adopt the Tactical Event schema across all detectors.
- [ ] Stand up FaunaScope-style FastAPI + SQLite event store.
- [ ] Role/permission model (ranger / analyst / authority).
- [ ] Map view consuming events; offline cache.
- [ ] Optional: push to SMART / EarthRanger.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Small sanctuary | Essential tier only — phones + dashboard, no server |
| Transfrontier park | multi-site sync, shared taxonomy, cross-border roles |
| Marine protected area | swap trail map for coastal/AIS layers |
