# M4 — Aerial, Thermal & Geospatial

> Mission: drones (scheduled / on-demand / alert-triggered) with RGB + thermal to validate
> intrusions, track suspects and find snares; plus GIS terrain layers to plan interception points.

## 1. Goal
Ground sensors (M2 cameras, M3 audio) detect events but can't follow a suspect through thick bush.
A drone dispatched within 2–4 minutes of an alert can confirm the threat, track movement, and relay
GPS coordinates to rangers on foot. Thermal imaging is the key differentiator at night and under
canopy edge. This module covers: automated drone dispatch, thermal + RGB fusion, 3D terrain mapping
for route planning, and satellite layer integration for habitat monitoring.

## 2. Field tiers
| Tier | Hardware | What you get |
|------|----------|--------------|
| Essential | Smartphone with GPS + offline satellite map tiles | manual patrol planning, offline maps, zone annotations |
| Intermediate | DJI Mini 3 or clone + thermal add-on + tablet | triggered overwatch, manual thermal scan, video recorded as evidence |
| Advanced | Autonomous hexacopter + Herelink + onboard AI | scheduled perimeter patrol, on-alert auto-launch, AI detection during flight, real-time video to hub |

## 3. Recommended repos
| Repo / tool | Take this | Notes |
|-------------|-----------|-------|
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | PyDeck 3D terrain rendering + zone overlay on Leaflet | plug into the hub dashboard |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | patrol route and beat planner | adapt for drone flight-path planning |
| QGIS + SRTM tiles | terrain elevation, illegal tracks, vegetation, fire scars, water | free; export to GeoTIFF for offline use |
| OpenDroneMap (WebODM) | photogrammetric 3D reconstruction from drone photos | map escape routes, chokepoints, snare density |
| ArduPilot / Mission Planner | autonomous waypoint missions, fence triggers | open-source autopilot for compatible drones |

## 4. Hardware
- **Consumer drone (Intermediate):** DJI Mini 3 Pro (~$700) or equivalent. FLIR Lepton thermal module where available.
- **Thermal note:** most effective at dawn/dusk and in open areas. Under dense canopy → pair with M3 audio.
- **Autonomous (Advanced):** ArduPilot-compatible hexacopter + Herelink ground station. Configure geofence and return-to-home before field deployment.
- **Power:** carry spare LiPo batteries. Typical consumer drone: 25–30 min per battery. Plan recharge rotation.
- **Offline maps:** export QGIS layers to MBTiles. Load on tablet via Avenza Maps or Leaflet offline. No connectivity needed in field.

## 5. Scripts & workflow
**Offline 3D terrain map (WebODM):**
```bash
# 1. Fly a grid pattern (overlap >80% front, >60% side)
# 2. Import photos into WebODM
docker run -ti -p 8000:8000 opendronemap/webodm --media-root=/data
# 3. Export orthophoto + DSM as GeoTIFF
# 4. Load into QGIS; mark chokepoints, escape routes, water sources
# 5. Export patrol layers as GeoJSON → import into hub /zones
```

**QGIS satellite layer workflow:**
```
1. Install QGIS (free). Add QuickMapServices plugin.
2. Load SRTM elevation: QGIS > Plugins > SRTM Downloader (select reserve bbox).
3. Add NDVI vegetation index from Sentinel-2 via Copernicus Data Space.
4. Draw patrol zones, red zones, water sources as vector layers.
5. Export as GeoJSON → POST to hub /zones.
```

Generalize this module around terrain enrichment, not around one map provider: satellite layers, elevation, weather, water occurrence, and reverse geocoding can all feed the same route-risk layer.

Use `OpenDroneMap` for drone-derived terrain, `QGIS` for offline GIS, `Copernicus Sentinel-1` for radar layers, and `Open-Meteo`/`Nominatim`/`SoilGrids` for environmental enrichment.

## 6. Agent prompts
**Prompt A — generate patrol flight plan:**
```
I have a reserve GeoJSON polygon and a set of known high-risk zones (GeoJSON FeatureCollection).
Generate a lawn-mower drone flight plan as a list of GPS waypoints that:
- Covers the full polygon at 80m altitude
- Spends extra time over high-risk zones (denser passes)
- Returns to home at the centroid of the polygon
Output as JSON array of {lat, lon, alt, speed, action} compatible with ArduPilot waypoints.
```

**Prompt B — thermal anomaly detection:**
```
I have a thermal camera video (grayscale MP4). Write a Python script using OpenCV that:
1. Reads frames at 2fps
2. Detects hot blobs above threshold using connected-component analysis
3. Filters by size (reject <50px = small animals, >5000px = vehicle)
4. Saves detection frames as JPEG evidence files
5. Outputs JSON list of {frame, timestamp, bbox, blob_area} per detection
```

**Prompt C — chokepoint analysis:**
```
I have a DSM GeoTIFF of my patrol area. Write Python using rasterio and scipy that:
1. Loads the DSM
2. Computes slope; identifies low-slope terrain corridors between ridges
3. Marks narrowest crossing points as GeoJSON Point features
4. Saves chokepoints.geojson for import into Leaflet
```

## 7. Milestones (clone-and-follow checklist)
- [ ] Download QGIS. Import reserve boundary. Add SRTM elevation + satellite imagery.
- [ ] Mark patrol zones, water sources, high-risk areas as GeoJSON layers. Import to hub /zones.
- [ ] Fly a test grid (or use existing photos). Run through WebODM. Identify 3–5 chokepoints on 3D map.
- [ ] Set up offline map tiles on field tablets (MBTiles + Avenza or Leaflet offline).
- [ ] Define drone dispatch SOP: who decides to launch, max dispatch time, no-fly weather rules.
- [ ] First live alert-triggered dispatch. Time from alert to drone-on-site. Target < 5 min.
- [ ] Post drone observation as Tactical Event to hub. Confirm evidence file attached with GPS coordinates.
- [ ] Advanced: configure ArduPilot mission for scheduled perimeter patrol (e.g. 03:00 and 05:00 daily).

## 8. International use cases
| Region / biome | Adaptation |
|----------------|------------|
| African open savanna | thermal night overwatch priority; long-range fixed-wing for large areas (5k+ ha) |
| Dense tropical canopy | thermal limited under canopy → rely on M3 audio for detection; drone covers open perimeter only |
| Mountain terrain | terrain-aware waypoints (elevation-aware); cold weather cuts battery life 30%+ |
| Marine / coastal | swap for boat patrol or fixed-wing seaplane; AIS vessel tracking layer in hub |
| Amazon / riverine | river corridors are primary ingress routes; drone patrols river edges at dawn |
