# M5 — Species-centric Ecological Intelligence

> Mission: shift from "hunt the poacher" to "dynamically protect the species" — GPS collars,
> geofencing, density estimation, nest/calf monitoring, behavioral anomaly alerts.

## 1. Goal
Most anti-poaching systems focus on detecting intruders. This module adds the animal side: where
are the animals right now, are they behaving normally, and what does a sudden movement or a herd
going still mean? GPS collars generate a live map of the most at-risk individuals. A herd that
suddenly flees or a lone bull that stops moving for 6+ hours is often the first detectable sign of
a poaching event — sometimes before any camera or audio node fires. This module also handles nest
protection, breeding season lockdowns, and population trend monitoring.

## 2. Field tiers
| Tier | Hardware | What you get |
|------|----------|--------------|
| Essential | Manual GPS waypoint logging on CyberTracker | animal sighting records, seasonal density maps updated by hand |
| Intermediate | Affordable GPS collars (Savannah Tracking, AWT) + GSM/satellite uplink | real-time track on hub map, geofence alerts |
| Advanced | Satellite-uplink collars + Wildbook individual ID + acoustic + camera cross-correlation | individual animal lifecycle, behavioral anomaly detection, population dynamics |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [Tracking-and-Poaching-Alert (DSA)](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | R-Tree geofence + nearest-ranger Dijkstra (pure Python, edge-friendly) | **best starting point** for collar geofencing |
| [Illegal_Elephant_Poaching_App](https://github.com/grac3smith/Illegal_Elephant_Poaching_App) | CITES MIKE dataset parsing, threat-by-species visualization | adapt for any species with MIKE data |
| [Wildbook / Wild Me](https://www.wildme.org/) | individual photo-ID, mark-recapture, citizen science data collection | open-source; use for elephant ear, big cat spot, turtle shell patterns |
| [PAWS-public](https://github.com/lily-x/PAWS-public) | occupancy model integration with collar data for density estimation | combine with M8 risk engine |

External: **Movebank** (movebank.org) — open collar tracking data portal. **GBIF** — species occurrence records. **CITES MIKE** — elephant poaching incident database.

If the source is not a collar feed, still treat it as M5 when it contributes identity, distribution, or conservation-status context. Camera-trap classifiers, taxonomic APIs, and historical incident datasets should converge into the same species profile.

Useful inputs here: `Movebank`, `Wildbook`, `GBIF`, `IUCN`, `CITES MIKE`, `BirdNET`/bird audio refs, and camera-trap corpora such as `MammAlps`, `LILA BC`, and `iWildCam`.

## 4. Hardware
- **GPS collars:** Savannah Tracking (savannah-tracking.com) and African Wildlife Tracking (awt.co.za) make affordable solar-assisted collars from ~$400–800/unit. Satellite uplink (Iridium/Thuraya) for remote areas with no GSM.
- **Nest / water monitoring:** fixed trail cameras (M2 module) at known breeding sites, water sources. Trigger zone = animal home range, not park boundary.
- **Citizen science:** train local rangers and community scouts to photograph animals with phones. Wildbook handles the ID matching server-side.

## 5. Scripts & workflow
**Geofence alert (from DSA repo):**
```python
# From DSA alert engine: R-Tree spatial index over collar points
from rtree import index
import json

# Load red zones as GeoJSON polygons
red_zones = json.load(open('red_zones.geojson'))

# On each collar GPS ping (lat, lon, animal_id):
def check_geofence(lat, lon, animal_id, red_zones):
    for zone in red_zones['features']:
        if point_in_polygon(lat, lon, zone['geometry']):
            post_event({
                'type': 'geofence_breach',
                'source_id': animal_id,
                'lat': lat, 'lon': lon,
                'payload': {'zone': zone['properties']['name']}
            })
```

**Behavioral anomaly detection:**
```python
# Stillness alert: animal hasn't moved >50m in N hours
from collections import deque
import math, time

tracks = {}  # animal_id -> deque of (ts, lat, lon)

def update_track(animal_id, ts, lat, lon):
    if animal_id not in tracks:
        tracks[animal_id] = deque(maxlen=50)
    tracks[animal_id].append((ts, lat, lon))
    
    # Check last 6 hours of pings
    recent = [(t, la, lo) for t, la, lo in tracks[animal_id]
              if ts - t < 6 * 3600]
    if len(recent) > 3:
        max_dist = max(haversine(recent[0][1:], p[1:]) for p in recent)
        if max_dist < 50:  # < 50m movement in 6h
            post_event({'type': 'stillness_alert', 'source_id': animal_id, ...})
```

**Population density map (QGIS):**
```
1. Export collar fix points as CSV (ts, lat, lon, animal_id) from Movebank or your hub.
2. Load in QGIS. Run Vector > Analysis > Kernel Density Estimation.
3. Overlay on terrain and patrol zones.
4. Areas of high density + low patrol coverage → priority patrol sectors (feed into M8).
```

## 6. Agent prompts
**Prompt A — build collar ingestion service:**
```
I have a collar data API that returns JSON pings with {animal_id, lat, lon, ts, battery_pct}.
Build a Python service that:
1. Polls the API every 5 minutes
2. Stores each ping as a Tactical Event (type: track) in the hub via POST /events
3. Runs a geofence check against red zones loaded from hub GET /zones
4. If a red zone breach is detected, posts a second event (type: geofence_breach) immediately
5. If an animal hasn't moved >50m in 6 hours, posts a stillness_alert event
Return the full service as a Python file with a requirements.txt.
```

**Prompt B — individual animal ID with photos:**
```
I have a folder of wildlife photos taken by rangers in the field. Each photo has GPS EXIF data.
Write a Python script that:
1. Extracts GPS coordinates from EXIF using Pillow/piexif
2. Calls the Wildbook API to submit each photo for individual ID matching
3. If a match is found (confidence > 0.85), returns the animal's known ID and sighting history
4. Saves results as a JSON sighting log with {photo_file, lat, lon, ts, animal_id, confidence}
5. Posts each confirmed sighting as a Tactical Event to the hub
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Define the priority species and individuals for your reserve. List collar IDs if any exist.
- [ ] Clone DSA alert engine. Run geofence check against a test set of collar pings and red zones.
- [ ] If collars exist: build ingestion service (Prompt A). Test live ping → hub event flow.
- [ ] Add stillness alert. Confirm alert fires in test within correct time window.
- [ ] Load collar fixes into QGIS. Generate kernel density map. Identify 3 priority patrol sectors.
- [ ] Set up Wildbook instance (if photo-ID needed). Submit 50 test photos. Confirm ID matching.
- [ ] Brief all rangers on what collar alerts mean and how to respond. Define response SOP.
- [ ] Integrate density map with M8 patrol planning: high density + low patrol coverage = priority.

## 8. International use cases
| Region / species | Adaptation |
|------------------|------------|
| Elephant / rhino (Africa) | collar + waterhole watch + stillness alert; anti-snare camera sweep of known corridors |
| Tiger / leopard (South/SE Asia) | camera-trap photo-ID via Wildbook; territory monitoring for range contraction as poaching signal |
| Raptors / birds of prey (EU) | nest-site GPS geofence active during breeding season only; no collar needed, camera at nest |
| Sea turtles | beach nesting-site geofence (seasonal); collar on adult females; nesting-density heatmap |
| Pangolin (covert) | VHF radio tags (collars too heavy); manual tracking by ranger; hub logs waypoints from VHF receiver |
