# M4 — Aerial, Thermal & Geospatial (SCAFFOLD)

> Mission: drones (scheduled / on-demand / alert-triggered) with RGB+thermal to validate intrusions,
> follow escape routes, find snares; plus 3D/GIS terrain to plan interception points.

## Goal
Thermal beats RGB for detection probability, especially at dawn and at 90° view (PMC8232034). Use
photogrammetry to map trails, chokepoints, blind spots; link to heatmaps and patrols.

## Recommended repos / tools
| Repo / tool | Take this |
|------|-----------|
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | PyDeck 3D terrain rendering |
| COLMAP / OpenMVS | photogrammetric 3D reconstruction of escape routes |
| QGIS + satellite layers | vegetation, fire, water, illegal tracks |

## Milestones
- [ ] Define drone mission types (patrol / on-demand / alert-triggered).
- [ ] Thermal-RGB validation pipeline (dawn priority).
- [ ] 3D map of chokepoints → mark interception points on hub map.

## International use cases
| Context | Adaptation |
|---------|------------|
| Open savanna | thermal night overwatch, long-range fixed-wing |
| Dense canopy | thermal limited under canopy → lean on M3 audio |
| Mountain | terrain-aware flight planning, cold battery management |
