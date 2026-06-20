# M10 — Resilience, Training & Open-Source Operations

> Mission: treat the framework as a living product — health monitoring, predictive maintenance of
> sensors/batteries, model/dataset versioning, ranger training, and an open contributor ecosystem.

## 1. Goal
A platform that breaks silently is worse than no platform. Sensor nodes drain batteries in the field.
Camera traps fill their SD cards and stop recording. AI models degrade as animals change behavior or
poachers change tactics. This module makes the system self-aware: health dashboards catch failures
before rangers notice, predictive maintenance alerts replace batteries before they die, and federated
learning lets multiple reserves improve their shared AI models without exposing sensitive location
data. It also covers the human side: ranger training programs with scenario replays, and the
contributor docs that let the open-source community keep the project growing.

## 2. Field tiers
| Tier | Tooling | What you get |
|------|---------|--------------|
| Essential | Weekly manual node checklist + battery log spreadsheet | catches obvious failures; low overhead |
| Intermediate | Hub health dashboard (node last-seen + battery %) + automated alert on silence | real-time failure detection; email/Telegram alert |
| Advanced | Predictive battery model + DVC model versioning + federated learning across sites | failures caught before they happen; models improve without sharing data |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [WildlifeFL](https://github.com/MeGaurav4/WildlifeFL) | federated learning with Flower framework for YOLOv8/CRNN with differential privacy | **key repo** — parks improve models without sharing location-sensitive images |
| DVC | dataset and model version control; push trained models to edge devices via DVC remote | free; works with any cloud or local storage |
| Qdrant / Chroma | semantic search over past cases and poacher MO descriptions | local-first vector DB; no cloud needed |
| OpenVINO | run neural networks on old Intel CPUs without a GPU | lets low-budget reserves run inference on recycled office hardware |

## 4. Health monitoring schema
Each sensor node should report a heartbeat event every N minutes:

```json
{
  "type": "node_heartbeat",
  "source_id": "CAM_TRAP_04",
  "ts": "2024-11-15T03:00:00Z",
  "lat": -2.341, "lon": 34.842,
  "payload": {
    "battery_pct": 72,
    "sd_free_gb": 8.4,
    "uptime_hours": 312,
    "last_detection_ts": "2024-11-14T22:17:00Z",
    "model_version": "yolov8n-wildguard-v3",
    "precision": 0.91,
    "recall": 0.87
  }
}
```

Hub alerts when:
- `battery_pct < 20%` → schedule maintenance visit
- No heartbeat for > 2x normal interval → node offline alert
- `sd_free_gb < 2` → SD card near full
- `recall` drops > 10 points from baseline → model degradation alert

## 5. Scripts & workflow
**Node health dashboard (hub endpoint):**
```python
# GET /health/nodes — returns status of all registered nodes
@app.get("/health/nodes")
async def node_health():
    nodes = await db.fetch_all("""
        SELECT source_id,
               MAX(ts) as last_seen,
               json_extract(payload, '$.battery_pct') as battery_pct,
               json_extract(payload, '$.sd_free_gb') as sd_free_gb,
               json_extract(payload, '$.recall') as recall
        FROM events WHERE type = 'node_heartbeat'
        GROUP BY source_id
    """)
    now = datetime.utcnow()
    result = []
    for n in nodes:
        last = datetime.fromisoformat(n['last_seen'])
        status = 'ok'
        if (now - last).seconds > 3600: status = 'offline'
        elif n['battery_pct'] < 20: status = 'low_battery'
        elif n['sd_free_gb'] < 2: status = 'sd_full'
        result.append({**dict(n), 'status': status, 'minutes_since_ping': int((now-last).seconds/60)})
    return result
```

**Predictive battery model:**
```python
# Train on historical battery discharge curves per node type
# Features: days_since_charge, temperature, events_per_day, solar_hours
# Target: battery_pct in 7 days
# Alert: if predicted < 20% in 7 days → schedule maintenance now

from sklearn.linear_model import LinearRegression
import pandas as pd

def predict_battery_7d(node_id, history_df):
    X = history_df[['days_since_charge', 'avg_temp', 'events_per_day', 'solar_hours']]
    y = history_df['battery_pct']
    model = LinearRegression().fit(X[:-7], y[:-7])
    future_features = estimate_next_7_days(node_id)
    return model.predict([future_features])[0]
```

**Federated learning (WildlifeFL pattern):**
```bash
# Each reserve trains locally on its own data, never uploads raw images
# Only model weights (gradient updates) are shared → privacy preserved

# On each reserve's Pi:
python federated_train.py \
  --data-dir /local/camera-trap-images/ \
  --model yolov8n \
  --rounds 5 \
  --server-address hub.wildguard.net:8080

# Central aggregation server:
python flower_server.py --rounds 20 --min-clients 3
# After aggregation: improved shared model pushed back to all reserves via DVC
```

## 6. Agent prompts
**Prompt A — health monitoring dashboard:**
```
Build a minimal health monitoring dashboard for a wildlife sensor network. Requirements:
1. FastAPI endpoint GET /health/nodes that queries the hub SQLite DB for the latest
   node_heartbeat per source_id and returns status (ok/offline/low_battery/sd_full)
2. A lightweight HTML page (no external CDN) that polls /health/nodes every 60s and shows
   a status card per node: last seen, battery %, SD free, model recall, status badge
3. Sends a Telegram message (via bot API) when any node goes offline or battery < 20%
Return hub.py additions + health.html + requirements.txt.
```

**Prompt B — federated training setup:**
```
I have 3 conservation reserves that each have their own camera-trap datasets (private, cannot
share). I want them to collaboratively improve a shared YOLOv8n human-detection model.
Using the Flower federated learning framework:
1. Set up a central server that aggregates gradients (FedAvg strategy)
2. Set up a client script that trains locally on local images for N rounds, then sends
   only the weight update (not images) to the server
3. After aggregation, push the improved model to each client via DVC remote
4. Add differential privacy (Opacus) with epsilon=8 as a privacy budget
Return server.py, client.py, and setup instructions.
```

**Prompt C — scenario training exercise:**
```
Generate a ranger training exercise scenario for anti-poaching field response. The scenario:
- Reserve: savanna, 3000 ha, 4 rangers on duty
- Alert: camera trap detects 2 armed individuals at coordinates [-2.341, 34.842] at 03:42 UTC
- Complication: one ranger is 8km away, radio contact intermittent, no drone available tonight
Generate:
1. The full sequence of actions the duty officer should take (step-by-step, timed)
2. Three decision points where trainees must choose between options (with correct answers)
3. A debrief checklist: what evidence should have been collected, what was the chain of custody,
   what legal actions should have been initiated within 24 hours
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Add heartbeat event emission to all sensor nodes (M2 camera, M3 audio, M5 collar ingestion). Confirm they arrive in the hub.
- [ ] Build /health/nodes endpoint. Display on a simple HTML health page. Test: kill a node, confirm it shows as offline within 2x heartbeat interval.
- [ ] Set up Telegram bot alert for offline + low battery events. Test end-to-end.
- [ ] Log model precision/recall in each heartbeat. Set baseline. Alert if recall drops >10 points.
- [ ] Set up DVC for model versioning. Tag the current production model as v1. Test rollback.
- [ ] If multiple sites available: set up WildlifeFL federation server. Run 3-client test with synthetic data.
- [ ] Run first scenario training exercise (Prompt C) with ranger team. Debrief. Update SOPs.
- [ ] Write contributor onboarding doc: how to add a new sensor module, how to add a new playbook, how to submit a new capability. Add to docs/CONTRIBUTING.md.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Multi-park network (Africa / SE Asia) | federated learning shares model improvements across sites without sharing location-sensitive photos |
| Low-budget reserve | OpenVINO runs inference on recycled office PCs; skip GPU; predictive maintenance is highest ROI |
| Remote / off-grid site | satellite heartbeat (Iridium) once per hour; longer alert threshold (2x = 2h) |
| High staff turnover | scenario training exercises at onboarding; SOPs in local language; hub UI translated (see i18n) |
| Donor-funded program | health dashboard + MEL metrics from M6 = accountability report to donors; model recall trend = proof of value |
