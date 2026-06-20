# M8 — Prediction, Simulation & Adaptive Patrol Planning

> Mission: a risk engine that fuses patrol history, events, habitat, weather, moon, seasonality and
> community data into hotspot maps + priority scores, and plans unpredictable optimal patrol routes.

## 1. Goal
Poachers study ranger patterns. If rangers always patrol the same routes at the same times, poachers
simply wait. This module makes patrols unpredictable and data-driven: a risk model scores every grid
cell in the reserve daily, and a patrol planner generates routes that cover high-risk areas first
while varying the approach so that no pattern is detectable. Lunar phase, weather, market price spikes
(from M7) and animal location data (from M5) all feed the risk model. The result: rangers spend
their limited hours where poaching is most likely to happen next.

## 2. Field tiers
| Tier | Tooling | What you get |
|------|---------|--------------|
| Essential | Spreadsheet heatmap from past incidents; manual route planning | pattern analysis, zones identified by intuition + data |
| Intermediate | Python risk model (pandas + sklearn) + QGIS heatmap + daily route suggestions | data-driven daily briefing, routes vary systematically |
| Advanced | PAWS Stackelberg game solver + RL adversarial simulation + automated dispatch | game-theoretically optimal unpredictable patrols; simulation of poacher counter-strategy |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [PAWS-public](https://github.com/lily-x/PAWS-public) | Stackelberg-game risk model + patrol planning under uncertainty; `iware/` balanced bagging for sparse/biased data | Harvard; **best academic implementation** available open-source |
| [wildlifeRL](https://github.com/lucashu1/wildlifeRL) | RL/DDPG adversarial patrol simulation in a grid environment | simulate poacher counter-strategies before deploying new patrol patterns |
| [poaching_occupancy](https://github.com/oliviergimenez/poaching_occupancy) | HMM occupancy models that de-bias patrol detection data (rangers find more where they patrol more) | critical for not over-weighting areas where you've already patrolled heavily |
| [DSA Alert Engine](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | Dijkstra nearest-ranger routing; real-time dispatch to closest available ranger | wire into daily patrol assignment |

## 4. Risk model features
Feed these into your risk model (one row = one grid cell per day):

| Feature | Source |
|---------|--------|
| Historical incident rate (last 30/90/365 days) | hub /events |
| Days since last patrol in cell | patrol logs (M6) |
| Lunar phase (full moon = higher risk at night) | Python `ephem` library |
| Rain forecast (rain reduces ranger patrols → opportunity) | OpenWeatherMap API or offline almanac |
| Animal density in cell (from M5 collar data) | collar fix points |
| OSINT price spike for species present (from M7) | hub /events price_spike_alert |
| Distance to known entry points (roads, rivers) | GeoJSON from M4 terrain analysis |
| Vegetation cover (NDVI) | Sentinel-2 from M4 |

## 5. Scripts & workflow
**Risk score per grid cell (daily):**
```python
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
import numpy as np

# Build feature matrix: one row per (grid_cell_id, date)
# Label: 1 = poaching incident occurred within 7 days, 0 = no incident
# IMPORTANT: use balanced bagging (PAWS iware/) to handle class imbalance
# and occupancy model (poaching_occupancy) to de-bias patrol-dependent data

def compute_risk_scores(features_df, model):
    features_df['risk_score'] = model.predict_proba(
        features_df[FEATURE_COLS])[:, 1]
    return features_df.sort_values('risk_score', ascending=False)

# Output: GeoJSON with risk_score per cell → push to hub map via /zones
```

**Unpredictable patrol route generator:**
```python
import random
from heapq import heappush, heappop

def generate_patrol_route(risk_scores, n_waypoints=8, ranger_start=None):
    """
    Select n_waypoints from high-risk cells with controlled randomness:
    - Top 40% risk cells selected with probability proportional to score
    - 20% waypoints drawn randomly from remaining cells (keep poacher guessing)
    - Route connects waypoints via Dijkstra (from DSA repo) on trail graph
    """
    top_cells = risk_scores.head(int(len(risk_scores) * 0.4))
    random_cells = risk_scores.iloc[int(len(risk_scores) * 0.4):]
    
    selected = (top_cells.sample(n=int(n_waypoints * 0.8),
                                  weights='risk_score', replace=False)
                .append(random_cells.sample(n=int(n_waypoints * 0.2))))
    
    return optimize_route_tsp(selected, ranger_start)
```

**Lunar phase risk adjustment:**
```python
import ephem

def lunar_risk_multiplier(date_str):
    moon = ephem.Moon(date_str)
    phase = moon.phase  # 0–100 (100 = full moon)
    # Full moon → higher visibility for poachers + rangers → net risk depends on context
    # Empirical finding from PAWS: risk peaks 3 days before full moon (optimal visibility + cover)
    return 1.0 + 0.3 * (phase / 100)
```

## 6. Agent prompts
**Prompt A — build the risk model:**
```
I have a SQLite database with:
- Table 'events': (id, type, lat, lon, ts) — historical incidents + patrols
- Table 'zones': GeoJSON of reserve grid cells (500m x 500m)
Build a Python script that:
1. Computes features per (grid_cell, week): incident_rate_30d, days_since_patrol,
   lunar_phase, distance_to_nearest_road, animal_density (if collar data available)
2. Trains a GradientBoostingClassifier on historical incident labels
3. Uses balanced bagging (SMOTE or class_weight='balanced') to handle class imbalance
4. Outputs risk scores as a GeoJSON FeatureCollection with {cell_id, risk_score, top_features}
5. POSTs the risk layer to the hub /zones endpoint for display on the map
```

**Prompt B — adversarial simulation:**
```
Using the wildlifeRL grid environment, simulate the following scenario:
- Reserve: 10x10 grid, 5 ranger agents, 3 poacher agents
- Rangers use the patrol route generator from above (70% high-risk, 30% random)
- Poachers use a basic counter-strategy: avoid cells patrolled in last 3 days
- Run 1000 episodes. Report: average catch rate, average poaching events per episode,
  how catch rate changes as the random component varies from 0% to 50%
Output a CSV of results and a summary recommendation for the optimal randomness level.
```

**Prompt C — daily patrol briefing:**
```
Generate a daily patrol briefing for a reserve with 4 rangers. Input:
- Risk scores GeoJSON (from Prompt A output)
- Current ranger positions (lat/lon)
- Weather: [rain yes/no], [visibility], [temperature]
- Lunar phase for today
Output a plain-text briefing:
1. Today's top 5 risk zones (cell IDs + risk scores + why)
2. Recommended patrol assignment (one route per ranger, optimized for coverage)
3. Weather notes affecting patrol effectiveness
4. Any active OSINT price spikes or animal geofence alerts to watch for
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Export 1 year of past incidents from hub /events. Build feature matrix (risk model input).
- [ ] Run occupancy model (poaching_occupancy) to de-bias the data before training.
- [ ] Train GradientBoostingClassifier. Evaluate with leave-one-month-out cross-validation. Target AUC > 0.70.
- [ ] Generate daily risk GeoJSON. Display on hub map as color-coded heatmap overlay.
- [ ] Build patrol route generator. Brief rangers on the 70/30 logic (high-risk + random component).
- [ ] Run wildlifeRL adversarial sim to tune the randomness level for your reserve geometry.
- [ ] Add lunar phase + weather inputs. Confirm risk score changes logically with moon phase.
- [ ] Wire M7 price spike events: when price_spike_alert fires for a species present in a zone, increase that zone's risk multiplier for 14 days.
- [ ] After 60 days: compare catch rate before/after model deployment. Report to funders.

## 8. International use cases
| Context | Adaptation |
|---------|------------|
| Large park (>5000 ha), few rangers | model essential: too much ground to patrol without prioritization |
| Data-poor reserve (<6 months history) | use balanced bagging + occupancy model; supplement with community tip density as a proxy feature |
| Transfrontier park | multi-site risk model; cross-border entry points as high-weight features |
| Marine protected area | swap grid cells for patrol boat sectors; add AIS vessel density and fishing season as features |
| Urban wildlife corridor | pedestrian and vehicle traffic patterns as risk features; night-time incidents dominate |
