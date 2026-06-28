# Integration Map — what to plug in, per module

> For the people in the field. This is **not** a dense spec. For each module it answers four things:
> **what tool to use · why · which real project already uses it · how to start.**
> Pick one row, get it working, move on. Everything here is free and most of it runs offline.

How to read a row: **Tool** (the thing) → **Use it for** (the job) → **Seen in** (a repo/project that
proves it works) → **Start** (the one command or link to begin). Reliability tags: 🟢 official ·
🟦 academic · 🟡 community.

---

## M1 — Hub (the command center)
The hub is the spine: every detection becomes one event on one map. Build this first.

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| FastAPI + SQLite | the hub server itself (offline, tiny) | FaunaScope, Wildlife-News | `pip install fastapi uvicorn aiosqlite`; see `goal.md` M0 |
| Leaflet 🟡 | the live map (already in `index.html`) | FaunaScope | already wired in the dashboard |
| **SMART** 🟢 | the *standard* rangers already use for patrol data | conservation field standard | export your patrol CSV in SMART format → ingest |
| **EarthRanger** 🟢 | if a park already runs ops software, sync to it | many parks | optional upstream the hub posts to |

**Strategy:** don't invent a new patrol format — speak SMART/CyberTracker so rangers can adopt you.
**Extend:** add `event.domain` if you also do the pollution tier (M11–M20).

## M2 — Edge vision (camera traps)
Don't train from zero. Stand on MegaDetector.

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| **MegaDetector** 🟢 | find animal/person/vehicle in any camera-trap photo | Pytorch-Wildlife, Biodiversity | download `md_v5a.pt`, run on a folder |
| **Pytorch-Wildlife** 🟢 | one library wrapping detector + species classifier | Biodiversity | `pip install PytorchWildlife` |
| Blank-frame filter | drop empty photos (wind, leaves) before running AI → saves battery | FaunaScope `ml.py` | two-stage: blank? → then detect |
| **OpenVINO** 🟢 | run the model on a cheap CPU / Pi, no GPU | M10 edge | export model → OpenVINO IR |

**Strategy:** filter blanks first, detect second — the single biggest power saving in the field.
**Configure:** confidence threshold per site (start 0.8); retrain the *classifier* (not the detector)
for your local species.

## M3 — Bioacoustics (gunshots, chainsaws, birds)
| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| **OpenSoundscape** 🟦 | detect/classify/localize sounds | RFCx reference | `pip install opensoundscape` |
| **BirdNET** 🟢 | identify bird species from audio (anti-trapping) | birda-gui | drop in BirdNET model |
| **xeno-canto** 🟢 / **ESC-50** 🟡 | training audio: real bird calls / gunshot+chainsaw negatives | greenwood | free dataset downloads |
| **SPARROW** 🟢 | edge audio device deployment | Biodiversity | reference hardware |

**Strategy:** your three priority sounds are usually **gunshot, chainsaw, vehicle** — train those as
positives, use ESC-50 as the "everything else" negatives.

## M4 — Aerial & geo (satellite, drones) — *not built yet, here's the path*
| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| **Sentinel-1 SAR** 🟢 | see through clouds; water + land-change | surface_water_mapping | Copernicus / Earth Engine free tier |
| **Sentinel-2 / NDVI** 🟢 | vegetation loss = illegal clearing | EUDR work | NDVI change on a parcel watchlist |
| **OpenDroneMap** 🟢 | turn drone photos into a map/orthophoto | — | `docker run opendronemap/odm` |
| **opentopodata** 🟢 | elevation for any lat/lon (terrain risk) | audtheia | `GET api.opentopodata.org/v1/...` |
| **QGIS** 🟢 | look at all of it offline | — | desktop GIS |

**Strategy:** M4 needs heavier tools — adopt it only when a park has the imagery need. Start with
NDVI-change alerts on a small parcel list, not "process all of Sentinel".

## M5 — Species & individual intelligence
**We ship a working tool here:** `toolkit/python/species_lookup.py` (no key needed for the main calls).

| Tool / API | Use it for | Seen in | Start |
|------------|-----------|---------|-------|
| **GBIF API** 🟢 | messy name → accepted scientific name + taxonomy | audtheia | `species_lookup.py --name "African elephant"` |
| **IUCN Red List API** 🟢 | conservation status (EN/CR/VU…) → prioritize | audtheia | free token, `IUCN_TOKEN=… species_lookup.py --name …` |
| **Nominatim (OSM)** 🟢 | place text → coordinates (puts OSINT tips on the map) | audtheia | `species_lookup.py --place "Napoli"` |
| **Movebank / Wildbook** 🟢 | open collar tracking / individual photo-ID | — | data sources for collars + re-ID |
| **CITES MIKE** 🟢 | elephant poaching baseline stats | Illegal_Elephant_Poaching_App | historical data for M8 |
| `gps_geofence.py` (ours) | alert when a collared animal leaves the safe zone | — | `--demo` |

**Concrete hook (already live):**
```bash
python species_lookup.py --enrich osint_leads.json --out enriched.json   # adds taxonomy+status+coords
```
**Strategy:** enrich *once* at ingestion so every downstream view (map, report, court file) gets the
clean name and status for free.

## M6 — Field & community
| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| `tip_intake.py` (ours) | turn raw tips → events, hash the reporter (protect informants) | — | `--demo` |
| **CyberTracker** 🟢 | offline field data collection on a phone | field standard | export → ingest |
| **SMART** 🟢 | patrol/encounter standard | field standard | speak its schema |
| **Airtable / n8n** 🟡 | quick tip portal + automation if you have connectivity | audtheia | optional cloud intake |

**Strategy:** protect the source first — `tip_intake.py` already hashes the reporter. Move SMS tips to
Signal as soon as possible (see M6 doc).

## M7 — OSINT (online wildlife trade)
**Fully working** (`osint_scrape.py`, `ebay_adapter.py`, `osint_sites.json` = 104 sites, skill).

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| Slang dictionary (ours) | catch coded ads ("white gold" = ivory) | Wildlife-News | edit `slang_dict.json` |
| Canonical-URL + title dedupe (ours) | one listing = one lead across sites/runs | **Wildlife-News** `dedupe.py` | already wired |
| **Nominatim** 🟢 | seller location text → coordinates | audtheia | via `species_lookup.py` |
| **anti-poaching-platform** dataset 🟦 | past verdicts → price & precedent | that repo's seizure DB | feeds M9 |

**Strategy & guardrail:** generic site list = fine; **never publicly name one shop next to a crime**
(defamation). Masked store + ref on the dashboard; real URL only in the M9 case file.

## M8 — Prediction & patrol planning
**Working tool:** `risk_model.py` (risk heatmap + unpredictable routes).

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| Risk model (ours) | score every grid cell, plan 70/30 routes | inspired by PAWS | `risk_model.py --demo` |
| **PAWS-public** 🟦 | game-theory optimal patrols, handles biased data | that repo | advanced upgrade |
| **poaching_occupancy** 🟦 | de-bias "we find more where we patrol more" | that repo | run before training |
| **DSA Dijkstra + R-tree** 🟡 | real shortest-path routing + nearest-ranger dispatch | Tracking-Alert-Engine | upgrade our greedy router |
| **Open-Meteo** 🟢 | rain/moon as risk features | audtheia | `GET api.open-meteo.com/...` |

**Strategy:** keep patrols **unpredictable** — the random 30% is the point, don't "optimize it away".

## M9 — Evidence & legal
**Working tool:** `case_file.py` (integrity PASS/FAIL + signable case file).

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| `case_file.py` (ours) | re-hash evidence, prove unaltered, build the file | — | `--demo` |
| **anti-poaching-platform** seizure DB 🟦 | precedent library: species → typical sentence | that repo (`db/_DATA_*.csv`) | parse → reference table |
| **genetic-forensic-portal** 🟦 | trace ivory/horn DNA to a population | uw-cefs repo | sample submission API |
| **NIST SP 800-101** 🟢 / **CITES** 🟢 | the standards your evidence must meet | — | reference, not code |

**Strategy:** a photo means nothing in court without an unbroken hash + custody chain — that's exactly
what `case_file.py` enforces. Have a local lawyer review the first real chargesheet.

## M10 — Resilience & maintenance
**Working tool:** `node_health.py` (battery/offline/signal alerts).

| Tool | Use it for | Seen in | Start |
|------|-----------|---------|-------|
| `node_health.py` (ours) | catch a dead/flat node before it's a blind spot | — | `--demo` |
| **Flower** 🟢 | train across sites without moving raw data (privacy) | WildlifeFL | `pip install flwr` |
| **DVC** 🟢 | version your datasets & models | — | `dvc init` |
| **OpenVINO** 🟢 | keep inference cheap on old CPUs | — | shared with M2 |
| **Poaching-Hunting** scripts 🟡 | audit your sensor network for leaks (SSID/GPS) | that repo | run before deploying nodes |

**Strategy:** a sensor that leaks its own location helps the poacher — run the opsec audit *before*
you deploy, not after.

---

## The free APIs, in one place (copy-paste)
All plain HTTPS GET. Identify yourself in `User-Agent`. Be polite (≤1 req/s on Nominatim).

| API | Key? | One-liner |
|-----|------|-----------|
| GBIF taxonomy | no | `https://api.gbif.org/v1/species/match?name=African%20elephant` |
| IUCN Red List | free token | `https://apiv3.iucnredlist.org/api/v3/species/Panthera%20tigris?token=…` |
| iNaturalist | no | `https://api.inaturalist.org/v1/observations?q=…` |
| Nominatim geocode | no | `https://nominatim.openstreetmap.org/search?q=Napoli&format=json` |
| Open-Meteo | no | `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&daily=precipitation_sum` |
| opentopodata (elevation) | no | `https://api.opentopodata.org/v1/test-dataset?locations=..,..` |

`toolkit/python/species_lookup.py` already wires GBIF + IUCN + Nominatim — read it as the worked
example, then copy the pattern for the others.

> Rule for all of this: take what works, keep it simple, write it down so the next volunteer can run
> it. A tool nobody can start is worse than no tool.
