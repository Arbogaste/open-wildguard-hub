# M6 — Field Collection & Community Intelligence

> Mission: structural channels for patrol data, citizen reporting, informant intel and opportunistic
> observations — each with its own anonymity, risk and verification level. Offline-first.

## 1. Goal
Most poaching intelligence comes from people, not sensors. A community member who sees a suspicious
truck, or a ranger who finds a snare, holds information that no camera trap will ever capture.
This module builds the human-intelligence layer: offline patrol logging, anonymous community tip
portals, and a protected informant channel. Every report flows into the same Tactical Event store
as sensor alerts, so analysts see the full picture in one place. The module also tracks program
effectiveness: are community patrols actually working, are tip-offs leading to arrests, is the
local community benefiting enough to keep participating?

## 2. Field tiers
| Tier | Tooling | What you get |
|------|---------|--------------|
| Essential | SMART Mobile or CyberTracker on Android (no connectivity needed) | offline patrol forms, sighting records, sync when back at base |
| Intermediate | + anonymous web tip portal (LimeSurvey hosted locally or on a cheap VPS) | community members report via SMS or web, no name required |
| Advanced | + compartmented informant ledger, MEL dashboard, multi-language support | structured human intelligence program with accountability metrics |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| SMART Mobile / CyberTracker | fully offline patrol data collection; SMART exports to CSV/JSON | free; gold standard in conservation field data |
| LimeSurvey | anonymous web/SMS survey for community tips; self-hosted | open-source; runs on cheap VPS or Pi; no report links to IP |
| Typebot | conversational tip form (chatbot-style, friendlier than a survey) | easier for non-literate reporters; WhatsApp integration possible |
| OpenRefine | deduplicate and normalize amateur sighting reports before they hit the DB | free; run locally; no cloud needed |
| [DSA Alert Engine](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | offline CSV sync pattern + patrol log schema | adapt for ranger patrol export |

## 4. Privacy & source protection
- **Community tips:** never log the submitter's IP, phone number or identity. LimeSurvey and Typebot can be configured to strip all identifying metadata before storing. Make this default, not optional.
- **Informant ledger:** store informant identity in a separate encrypted database, accessible only to the intelligence officer. Never link a tip record to an informant ID in the main event store — only a compartmented case number.
- **Transmission security:** if tips arrive via SMS/WhatsApp, move to a Signal-based reporting number as soon as possible. WhatsApp is owned by a company with law-enforcement cooperation history in many jurisdictions.
- **Retaliation risk:** design your tip portal assuming poachers may attempt to identify informants. Enforce response secrecy, vary response timing, never confirm or deny whether a tip led to action.

## 5. Scripts & workflow
**Patrol sync (SMART → hub):**
```bash
# SMART exports patrol data as CSV or SMART-JSON
# Run this script after each patrol sync session at base
python patrol_sync.py \
  --input smart_export.csv \
  --hub-url http://localhost:8000 \
  --token $RANGER_TOKEN

# patrol_sync.py converts each row to a Tactical Event and POSTs to /events
# type: patrol_observation | sighting | snare_found | fence_breach
```

**Anonymous tip ingestion:**
```python
# LimeSurvey webhook → hub
# LimeSurvey sends a JSON payload on survey submit. This handler strips identity fields:
from fastapi import Request
import hashlib

@app.post("/tips/ingest")
async def ingest_tip(req: Request):
    data = await req.json()
    # Strip any identity fields before storing
    safe_fields = {k: v for k, v in data.items()
                   if k not in ('ipaddr', 'phone', 'email', 'name', 'submitdate')}
    event = {
        'type': 'community_tip',
        'source_id': 'community_' + hashlib.sha256(str(data).encode()).hexdigest()[:8],
        'lat': safe_fields.get('lat'), 'lon': safe_fields.get('lon'),
        'ts': safe_fields.get('ts'),
        'payload': safe_fields
    }
    # POST to main event store
    await post_event(event)
```

**MEL dashboard (basic):**
```
Track monthly:
- Tips received vs. tips verified (verification rate)
- Tips that led to ranger action vs. arrests
- Patrol hours per zone vs. incident rate in that zone (coverage effectiveness)
- Community program participation trend (are locals engaging more or less?)
Export as CSV monthly; review in spreadsheet or QGIS.
```

## 6. Agent prompts
**Prompt A — build the tip portal:**
```
I need a minimal anonymous wildlife tip reporting system. Build:
1. A LimeSurvey survey with fields: [date, location (lat/lon or landmark), what did you see,
   how many people, which direction were they going, optional photo upload]
2. A webhook handler in Python (FastAPI) that receives the LimeSurvey submission,
   strips all IP/time/identity metadata, converts to a Tactical Event JSON, and POSTs
   to the hub /events endpoint
3. Configure LimeSurvey to NOT log IP addresses (Anonymize responses = Yes)
The system must work without any identity logging end-to-end.
```

**Prompt B — patrol data converter:**
```
SMART Mobile exports patrol data as a CSV with columns: [patrol_id, ranger_id, date, lat, lon,
observation_type, species, count, notes, snare_type]. Write a Python script that:
1. Reads the CSV
2. Converts each row to a Tactical Event JSON matching event_schema.json
3. POSTs each event to the hub via POST /events
4. Outputs a summary: N events ingested, M errors with details
```

**Prompt C — MEL report generator:**
```
I have a SQLite database with a table 'events' (id, type, ts, lat, lon, payload).
Write a Python script that generates a monthly MEL report:
1. Count events by type (patrol_observation, community_tip, alert, geofence_breach)
2. Tips verified (payload contains 'verified': true) vs total tips
3. Tips that led to ranger dispatch (tip event_id appears in a dispatch event's payload)
4. Patrol coverage: total area covered (convex hull of patrol waypoints) vs reserve area
5. Output as a text report and a CSV summary
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Install SMART and CyberTracker on ranger devices. Run a test patrol; confirm export works.
- [ ] Build patrol_sync.py. Do a dry-run import of a SMART export into the hub. Verify event format.
- [ ] Set up LimeSurvey (self-hosted). Configure anonymization. Test a tip submission end-to-end.
- [ ] Wire LimeSurvey webhook to hub /tips/ingest. Verify tip arrives as Tactical Event without identity.
- [ ] Brief community scouts in local language. Explain what information helps, what happens to their reports, why it's safe.
- [ ] Define compartmented informant handling SOP. Separate DB. Restricted access. Audit log.
- [ ] After 30 days: run first MEL report. Review coverage gaps. Adjust patrol schedules.
- [ ] Add Typebot (chatbot tip form) if literacy is a barrier. Test on WhatsApp or SMS.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Indigenous-comanaged land | data sovereignty: community owns their sighting data; exports on request; local language forms |
| High-corruption environment | strict source compartmentation; tip portal server hosted outside country; VPN access only |
| Marine protected area | tips about illegal fishing vessels; include vessel description, heading, time; cross-check AIS |
| Urban wildlife corridor | residents report sightings via QR code poster → web form; no app required |
| Low-literacy community | Typebot voice message support; local radio announcements for tip hotline |
