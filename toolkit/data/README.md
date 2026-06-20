# Toolkit · Data

## Canonical event schema
[`event_schema.json`](event_schema.json) — every subsystem normalizes detections into this one
record. Keep it flat and versioned (see `dev.md`). The edge scripts already emit it.

## Open datasets to train on (no need to start from zero)
| Dataset / resource | Use | Link |
|-------------------|-----|------|
| LILA BC | camera-trap images, many species, millions of frames | [lila.science](https://lila.science/) |
| Snapshot Serengeti | savanna camera-trap, species + empty | [lila.science](https://lila.science/) |
| iWildCam / WILDS | cross-region camera-trap generalization | [github.com/visipedia/iwildcam_comp](https://github.com/visipedia/iwildcam_comp) |
| ENABirds / xeno-canto | bird audio for bioacoustics | [xeno-canto.org](https://xeno-canto.org/) |
| ESC-50 | gunshot/chainsaw/vehicle ambient negatives | [github.com/karolpiczak/ESC-50](https://github.com/karolpiczak/ESC-50) |
| UrbanSound8K | ambient negatives for audio classifiers | [urbansounddataset.weebly.com](https://urbansounddataset.weebly.com/) |
| CITES MIKE elephant data | historical illegal-kill stats (M5/M8) | [CITES MIKE portal](https://cites.org/eng/prog/mike/index.php/portal) / [Illegal_Elephant_Poaching_App](https://github.com/grac3smith/Illegal_Elephant_Poaching_App) |
| MammAlps v1 | multi-view video/audio behavior monitoring | [Zenodo](https://zenodo.org/records/15040901) |
| MammAlps dense annotations | dense behavior + track labels | [Zenodo](https://zenodo.org/records/15040901) |
| Gorongosa camera traps | camera-trap images for generalization | [LILA mirror](https://lilablobssc.blob.core.windows.net/gorongosacameratraps/gorongosa-camera-traps-public-256x256.zip) |
| GBIF species match API | taxonomic normalization for species records | [api.gbif.org](https://api.gbif.org/v1/species/match) |
| IUCN Red List API | conservation-status enrichment | [apiv3.iucnredlist.org](https://apiv3.iucnredlist.org/api/v3/species/) |
| iNaturalist observations | citizen science / OSINT enrichment | [api.inaturalist.org](https://api.inaturalist.org/v1/observations) |
| Open-Meteo | weather features for risk and patrol planning | [api.open-meteo.com](https://api.open-meteo.com/v1/forecast) |
| SoilGrids | habitat / terrain enrichment | [rest.isric.org](https://rest.isric.org/soilgrids/v2.0/properties/query) |
| Nominatim | reverse geocoding for incidents | [nominatim.openstreetmap.org](https://nominatim.openstreetmap.org/reverse) |
| Copernicus Sentinel-1 GRD | radar imagery for surface-water / terrain features | [developers.google.com/earth-engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD) |
| OpenTopodata | elevation / terrain enrichment | [api.opentopodata.org](https://api.opentopodata.org/v1/) |

## What these unlock
- M2: camera-trap detection, blank-frame filtering, species classification.
- M3: bird / forest audio detection, hard negatives, localization.
- M4: terrain, water, weather and route-risk enrichment.
- M5: species identity, density, conservation status, collar feeds.
- M8: risk model features and patrol planning.
- M10: cross-site adaptation, versioning, federation, rollback.

## Labeling
Use **CVAT** or **Label Studio** (both open-source, self-hostable) for boxes/classes on your own
footage. Export YOLO format for `train_camera_trap_classifier.py`.

## Synthetic data (rare classes)
Real armed-poacher photos are scarce. Use the **Poaching-detection** repo method: paste human/weapon
cutouts onto wild backgrounds to balance the `human`/`weapon` classes. Or diffusion models (FLUX/SD)
for weather/lighting variety.

## Generalization notes
- Prefer resources that can serve multiple modules instead of one project-specific pipeline.
- A dataset can support M2 if it has imagery, M3 if it includes audio, M5 if it carries species labels, and M10 if it helps with cross-site adaptation.
- A public API belongs here if it can enrich events, normalize species names, or add geospatial context regardless of the originating repo.
- If a team wants a fast start, use the rows above as the minimum shared stack before custom training.
