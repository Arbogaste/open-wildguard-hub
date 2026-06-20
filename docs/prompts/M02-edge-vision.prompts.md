# M2 Edge Vision — agent prompt pack

> Paste the context primer from `_AGENT_GUIDE.md` first, then one prompt below.

## P1 — Build the edge inference service
```
Implement a Python service that:
1. Reads frames from a webcam index, RTSP URL, or video file.
2. Runs a YOLOv8 (or ONNX/TFLite) model and alerts only on classes I pass (default human, vehicle).
3. On a detection (above a confidence threshold, with a cooldown), saves an annotated evidence JPEG
   and writes a Tactical Event JSON conforming to toolkit/data/event_schema.json, including a
   sha256 hash of the evidence file.
4. Writes events to an events/ dir for a separate transport to pick up (store-and-forward).
Target Raspberry Pi / Jetson. Keep dependencies minimal (ultralytics, opencv). Provide a CLI with
--weights --source --classes --conf --lat --lon --node. Add a README with the run command.
Start from toolkit/python/edge_infer_camera.py if present and improve it.
```

## P2 — Generate synthetic poacher training data
```
Real photos of armed poachers are scarce, which starves the 'human'/'weapon' classes. Build a
synthetic data generator that composites human and weapon cutouts (with alpha) onto wild-background
images, randomizing scale, position, lighting, blur and occlusion, and emits YOLO-format labels for
the pasted objects. Reference the approach in the Poaching-detection repo. Output a balanced dataset
ready for train_camera_trap_classifier.py. Include a config for class counts and augmentation ranges.
```

## P3 — Wire alert delivery (offline-first)
```
Add a transport that watches the events/ directory and delivers each Tactical Event + evidence image
over a configurable channel (Telegram bot, MQTT, or LoRa serial), with a persistent outbox so nothing
is lost when offline: queue on disk, retry with backoff, mark delivered. Must survive process restart
and long network outages. Keep the event schema intact. Provide config + a dry-run mode.
```

## P4 — Two-stage blank filter (save power)
```
Add a fast pre-filter that drops 'empty' frames (wind, no subject) before running the detector, to
save CPU/battery on edge nodes. Use a cheap motion/blank classifier (e.g. frame differencing or a
tiny MobileNet) as stage 1, the YOLO detector as stage 2. Reference FaunaScope's blank/non-blank
pipeline. Measure and report the % of frames skipped and any recall loss on the 'human' class.
```
