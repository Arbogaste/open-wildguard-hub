# M2 — Edge Computer Vision & Perimeter Sensing

> Mission: detect humans vs wildlife, weapons, vehicles and snares on camera **at the edge**,
> filter wind/birds, and fire an alert with an evidence snapshot — without streaming GB to the cloud.

## 1. Goal
Most reserves already have camera traps or fixed cameras but drown in footage. This module turns
cameras into real-time guards: a model runs on cheap local hardware, distinguishes a poacher from
an elephant, ignores wind-blown branches, and pushes a geotagged alert + a saved frame. Works on
trails, fence lines and waterholes. Reduces ranger response time from days (manual photo review) to
minutes.

## 2. Field tiers
| Tier | Hardware | What you get |
|------|----------|--------------|
| Essential | Android phone + free camera-trap app, or 1 USB webcam + old laptop | manual/triggered capture, offline review, blank-frame filtering |
| Intermediate | Raspberry Pi 4/5 + Pi Camera or USB cam, solar + battery | on-device YOLOv8n inference, store-and-forward alerts |
| Advanced | Jetson Orin Nano / OpenVINO mini-PC + multi-camera + LoRa/satellite | multi-class (human/weapon/vehicle/snare), night IR, mesh of nodes |

## 3. Recommended repos
| Repo | Take this | Notes |
|------|-----------|-------|
| [wildlife-poaching-detection](https://github.com/karthikka430-rgb/wildlife-poaching-detection) | `backend/app.py` real-time YOLOv8 + instant evidence snapshot, HTML/JS alert UI | Python, modern, lean. **Best starting point.** |
| [Poaching-detection](https://github.com/Tarshdeep2210/Poaching-detection) | EfficientNet animal/empty/poacher classifier; **synthetic data generator** (paste human cutouts on wild backgrounds); **Grad-CAM** explainability | solves "no real armed-poacher photos to train on" |
| [FaunaScope](https://github.com/tanmaynikhare45/FaunaScope-Wildlife-Camera-Trap-Analysis-Platform) | 2-stage **blank/non-blank → species** pipeline (`backend/src/services/ml.py`); EXIF→map | saves power by dropping empty frames before detection |
| [Ecosentinel](https://github.com/Kerbal12/Ecosentinel) | OpenCV/YOLOv3 + MobileNet-SSD CCTV baseline | use as benchmark on legacy hardware |
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | video+audio **bimodal consensus** to cut false positives | pairs with M3 |

Labeling: use **CVAT** or **Label Studio** (both open-source) to annotate your own footage.
Edge optimization: **TinyML** / **OpenVINO** to run on weak/old hardware.

## 4. Hardware
- **PIR-triggered camera node** (Essential/Intermediate): see [`../../toolkit/arduino/pir_camera_node.ino`](../../toolkit/arduino/pir_camera_node.ino).
  BOM: ESP32-CAM (~$8), PIR HC-SR501 (~$1), 18650 cell + solar TP4056, weatherproof + bark-camo enclosure.
  Logic: PIR wakes ESP32 → capture → store to SD → opportunistic Wi-Fi/LoRa upload (store-and-forward).
- Camouflage: 3D-printed bark-texture enclosure. Solar for off-grid endurance.

## 5. Scripts
- [`../../toolkit/python/train_camera_trap_classifier.py`](../../toolkit/python/train_camera_trap_classifier.py)
  — fine-tune a YOLOv8 / image classifier on your labeled camera-trap dataset (human/animal/vehicle/empty).
  Runs on a single GPU or CPU. Exports to ONNX/TFLite for edge.
- [`../../toolkit/python/edge_infer_camera.py`](../../toolkit/python/edge_infer_camera.py)
  — run live inference on a webcam/RTSP/Pi camera, draw boxes, save evidence frame + JSON event on detection.

## 6. Agent prompts
- [`../prompts/M02-edge-vision.prompts.md`](../prompts/M02-edge-vision.prompts.md) — prompts to (a) build the
  edge inference service, (b) generate synthetic poacher training data, (c) wire alerts to Telegram/LoRa.

## 7. Milestones (clone-and-follow checklist)
- [ ] Collect/obtain 500+ frames; label human/animal/vehicle/empty in Label Studio.
- [ ] Generate synthetic armed-poacher frames (Poaching-detection method) to cover the rare class.
- [ ] Train with `train_camera_trap_classifier.py`; target ≥0.85 recall on `human`.
- [ ] Export to TFLite/ONNX; verify it runs on target edge device.
- [ ] Deploy `edge_infer_camera.py` on a node; confirm evidence frame + event JSON on trigger.
- [ ] Wire alert delivery (M4/Telegram/LoRa). Field-test false-positive rate over 72h.

## 8. International use cases
| Region / biome | Adaptation |
|----------------|------------|
| African savanna (elephant/rhino) | wide trails + waterholes; vehicle + firearm classes priority; thermal at dawn (see M4) |
| SE-Asia dense canopy (tiger/pangolin) | snare/trap detection class is critical; short-range PIR nodes on game trails |
| EU temperate forest (wolf/bear/raptor) | nest/den protection; vehicle + off-track footprint focus; GDPR — see M9 privacy |
| Marine/coastal (turtle/seabird) | beach-access cameras; night-poaching of nests; salt-proof enclosures |
| Andes/Amazon (jaguar, illegal logging) | pair with M3 chainsaw audio; low-bandwidth store-and-forward essential |
