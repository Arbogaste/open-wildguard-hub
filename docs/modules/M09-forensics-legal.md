# M9 — Evidence Chain & Legal Compliance

> Mission: every event produces a court-ready, digitally-native evidence package — synced timestamp,
> coordinates, original media, hashes, sensor logs, operators, transformations, decisions.
> Continuous chain of custody so cases aren't thrown out on technical grounds.

## 1. Goal
A poacher caught on camera is worthless if the evidence is inadmissible. Digital evidence fails in
court when: there is no proof the file is unaltered, the timestamp is wrong or missing, the chain
of custody is broken, or the person who collected the data isn't properly identified. This module
solves all of those problems. Every photo, audio clip and event JSON is hashed at the point of
capture, the hash is stored alongside the file, and every transfer is logged. Analysts can generate
a chargesheet (see the live demo in the hub dashboard) citing the correct articles of wildlife law
for the jurisdiction. The genetic forensics integration (M9 advanced) links physical evidence like
ivory or horn to population databases to prove the crime crosses borders.

## 2. Field tiers
| Tier | Tooling | What you get |
|------|---------|--------------|
| Essential | SHA-256 hash of evidence files + written custody log | basic integrity proof; sufficient for many national courts |
| Intermediate | Automated chargesheet generator + hash-manifest per case | full case file ready for prosecution; digital delivery to authority |
| Advanced | + Genetic forensics portal + GDPR/AI-Act compliance sublayer + cross-border INTERPOL workflow | transnational case-building; evidence survives jurisdictional challenges |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | chargesheet generator citing WPA articles (the hub demo `generateChargesheet()` is already based on this pattern) | adapt to your jurisdiction's wildlife law |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | structured parsing of seizure records and court verdicts → searchable case database | build your precedent library |
| [genetic-forensic-portal](https://github.com/uw-cefs/genetic-forensic-portal) | secure genotype submission to trace ivory/horn to population of origin | links seized material to known poaching hotspots; admissible in many courts |

Standards: **U.S. FWS evidence management policy** + **NIST SP 800-101** digital evidence guidelines. **CITES** seizure reporting templates.

Generalize M9 around evidentiary integrity: if a source can be hashed, timestamped, and linked to a chain-of-custody record, it belongs here even when it starts as a photo, a genotype, a legal filing, or a structured OSINT artifact.

## 4. Evidence package format
Every Tactical Event that results in a physical evidence item must carry an evidence manifest:

```json
{
  "event_id": "evt-2024-001-cam04",
  "type": "alert",
  "source_id": "CAM_TRAP_04",
  "ts": "2024-11-15T03:42:11Z",
  "lat": -2.341, "lon": 34.842,
  "evidence": [
    {
      "filename": "CAM04_20241115_034211.jpg",
      "sha256": "a3f1c...8b2e",
      "captured_at": "2024-11-15T03:42:11Z",
      "captured_by": "CAM_TRAP_04",
      "transferred_at": "2024-11-15T08:00:00Z",
      "transferred_by": "ranger_id_007",
      "storage_location": "local_vault/case-2024-001/"
    }
  ],
  "custody_log": [
    {"ts": "2024-11-15T03:42:11Z", "action": "captured", "actor": "CAM_TRAP_04"},
    {"ts": "2024-11-15T08:00:00Z", "action": "transferred", "actor": "ranger_007"},
    {"ts": "2024-11-15T09:15:00Z", "action": "archived", "actor": "analyst_002"}
  ]
}
```

The toolkit scripts (`edge_infer_camera.py`, `train_audio_classifier.py`) already generate SHA-256
hashes and include them in the event payload. See `toolkit/data/event_schema.json`.

## 5. Scripts & workflow
**Hash evidence file at capture (from edge_infer_camera.py pattern):**
```python
import hashlib, json, datetime

def hash_evidence(filepath):
    sha = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha.update(chunk)
    return sha.hexdigest()

def build_evidence_entry(filepath, captured_by):
    return {
        'filename': filepath.name,
        'sha256': hash_evidence(filepath),
        'captured_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'captured_by': captured_by
    }
```

**Generate chargesheet (extend the hub demo):**
```python
# The hub dashboard already has generateChargesheet() in JS.
# For a real case file, generate a server-side PDF:

from reportlab.pdfgen import canvas  # pip install reportlab
from datetime import datetime

def generate_chargesheet(case_id, species, offense_type, wpa_sections, evidence_manifest):
    filename = f"chargesheet_{case_id}.pdf"
    c = canvas.Canvas(filename)
    c.setFont("Courier", 10)
    c.drawString(50, 800, f"FORENSIC INCIDENT REPORT — CASE {case_id}")
    c.drawString(50, 785, f"DATE: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    c.drawString(50, 770, f"SPECIES: {species}")
    c.drawString(50, 755, f"OFFENSE: {offense_type}")
    c.drawString(50, 740, f"WPA SECTIONS: {wpa_sections}")
    c.drawString(50, 710, "EVIDENCE MANIFEST:")
    y = 695
    for ev in evidence_manifest:
        c.drawString(60, y, f"  {ev['filename']}  SHA256: {ev['sha256'][:16]}...")
        y -= 15
    c.save()
    return filename
```

**Custody transfer log:**
```bash
# On physical evidence transfer (e.g. USB drive handed from ranger to analyst):
python log_transfer.py \
  --event-id evt-2024-001-cam04 \
  --actor ranger_007 \
  --action transferred \
  --destination analyst_002
# Appends entry to custody_log in the hub DB and prints signed confirmation
```

## 6. Agent prompts
**Prompt A — build the case file generator:**
```
I need a Python script that builds a court-ready case file from a Tactical Event record.
The event has: event_id, type, source_id, ts, lat, lon, evidence (list of files + SHA-256),
custody_log (list of transfer entries).
The script should:
1. Verify each evidence file's current SHA-256 matches the hash stored in the event (integrity check)
2. Generate a PDF case file using reportlab with: case header, incident details, evidence manifest
   with hashes, custody log, and a signature block for the reporting officer
3. Save the PDF as case_{event_id}.pdf
4. Output PASS/FAIL integrity status for each evidence file
```

**Prompt B — chargesheet with correct legal citations:**
```
I need to generate a wildlife law chargesheet for the following jurisdiction: [INDIA / EU / KENYA / YOUR COUNTRY].
The incident involves: species=[SPECIES], offense=[OFFENSE TYPE], date=[DATE], location=[LOCATION].
Cite the correct sections of the applicable wildlife protection law for this offense.
Include: maximum penalty, required evidence elements, reporting chain (who to notify and in what order).
Format as a structured document that a forest officer can sign and submit to the prosecuting authority.
```

**Prompt C — GDPR/privacy compliance audit:**
```
I have a wildlife monitoring system that collects: camera-trap images (may include human faces),
audio recordings (may include human voices), GPS coordinates (of both animals and humans),
and community tip reports. Audit this data collection for compliance with [GDPR / national privacy law].
For each data type, provide:
1. Legal basis for collection
2. Data minimization requirements (what not to store)
3. Retention period recommendation
4. Access control requirements
5. How to handle a data subject access request
Output as a compliance checklist.
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Confirm that edge scripts (M2, M3) are generating SHA-256 hashes and including them in event JSON. Test with a sample capture.
- [ ] Build custody transfer log endpoint in hub. Test: capture → transfer → archive flow with 3 entries.
- [ ] Generate first real chargesheet from a real incident record. Have a local legal contact review for jurisdictional correctness.
- [ ] Set up local vault (encrypted folder on hub server) for evidence file storage. Only hub service account has write access.
- [ ] Run Prompt C privacy compliance audit for your jurisdiction. Address any gaps before deploying in the field.
- [ ] Clone genetic-forensic-portal. Test a sample genotype submission to confirm the API works for your species.
- [ ] First successful prosecution (or attempt): debrief on what evidence the prosecutor needed vs. what you provided. Iterate.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| India (WPA 1972) | chargesheet cites WPA schedules + sections (demo template in hub is already India-oriented) |
| Kenya (WCMA 2013) | cite Wildlife Conservation and Management Act; Kenya Wildlife Service is reporting authority |
| EU member state | GDPR minimization on suspect biometrics; AI-Act Art. 5 (real-time biometric ID restrictions); local public prosecutor |
| Transnational trafficking | INTERPOL Wildlife Crime unit; DNA portal links seizures across borders; CITES appendix references |
| Marine / fish | FAO CCRF compliance; vessel boarding evidence requirements differ from land-based |
