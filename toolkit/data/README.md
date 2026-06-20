# Toolkit · Data

## Canonical event schema
[`event_schema.json`](event_schema.json) — every subsystem normalizes detections into this one
record. Keep it flat and versioned (see `dev.md`). The edge scripts already emit it.

## Open datasets to train on (no need to start from zero)
| Dataset | Use | Link |
|---------|-----|------|
| LILA BC (Labeled Information Library of Alexandria: Biology & Conservation) | camera-trap images, many species, millions of frames | lila.science |
| Snapshot Serengeti | savanna camera-trap, species + empty | lila.science |
| iWildCam (Kaggle/WILDS) | cross-region camera-trap generalization | github.com/visipedia/iwildcam_comp |
| ENABirds / xeno-canto | bird audio for bioacoustics | xeno-canto.org |
| ESC-50 / UrbanSound8K | gunshot/chainsaw/vehicle ambient negatives | github.com/karolpiczak/ESC-50 |
| CITES MIKE elephant data | historical illegal-kill stats (M5/M8) | via Illegal_Elephant_Poaching_App repo |
| MammAlps v1 | multi-view video/audio behavior monitoring | zenodo.org/records/15040901 |
| MammAlps dense annotations | dense behavior + track labels | zenodo.org/records/15040901 |
| Gorongosa camera traps | camera-trap images for generalization | lilablobssc.blob.core.windows.net |
| GBIF species match API | taxonomic normalization for species records | api.gbif.org |
| IUCN Red List API | conservation-status enrichment | apiv3.iucnredlist.org |
| Copernicus Sentinel-1 GRD | radar imagery for surface-water / terrain features | developers.google.com/earth-engine |

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
