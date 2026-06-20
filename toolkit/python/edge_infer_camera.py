#!/usr/bin/env python3
"""
WildGuard M2 — Live edge inference. Watch a camera, detect threat classes, save an evidence
frame + a canonical event JSON on each detection. Designed for Raspberry Pi / Jetson / laptop.

Source can be a webcam index (0), an RTSP URL, or a video file.

Run
---
    pip install ultralytics opencv-python
    python edge_infer_camera.py --weights camera_trap.onnx --source 0 \
        --classes human vehicle --conf 0.5 --lat -2.33 --lon 34.83 --node node_edge_42

On detection it writes:
    evidence/<event_id>.jpg          # the frame
    events/<event_id>.json           # canonical Tactical Event (see ../data/event_schema.json)

Wire events/ to your alert transport (Telegram bot, LoRa, MQTT, EarthRanger). Keep it offline-first:
store-and-forward when the network is down.
"""
import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def make_event(node, lat, lon, threat, conf, evidence_path):
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "source_type": "camera_trap",
        "source_id": node,
        "coordinates": {"latitude": lat, "longitude": lon, "elevation": None},
        "threat_class": threat,
        "confidence": round(float(conf), 3),
        "evidence_hash": sha256_file(evidence_path),  # chain-of-custody (M9)
        "evidence_url": str(evidence_path),
        "metadata": {"detector": "yolov8", "module": "M2"},
    }


def main():
    p = argparse.ArgumentParser(description="WildGuard M2 edge inference")
    p.add_argument("--weights", required=True, help=".pt/.onnx/.tflite model")
    p.add_argument("--source", default="0", help="webcam idx, RTSP url, or file")
    p.add_argument("--classes", nargs="*", default=["human", "vehicle"], help="alert on these")
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--lat", type=float, default=0.0)
    p.add_argument("--lon", type=float, default=0.0)
    p.add_argument("--node", default="node_edge_01")
    p.add_argument("--cooldown", type=float, default=10.0, help="seconds between saved events")
    args = p.parse_args()

    try:
        import cv2
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("Install: pip install ultralytics opencv-python")

    Path("evidence").mkdir(exist_ok=True)
    Path("events").mkdir(exist_ok=True)
    model = YOLO(args.weights)
    src = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open source {args.source}")

    print(f"[wildguard] node={args.node} watching {args.source}; alert classes={args.classes}")
    last_save = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        res = model.predict(frame, conf=args.conf, verbose=False)[0]
        names = res.names
        hits = [(names[int(b.cls)], float(b.conf)) for b in res.boxes
                if names[int(b.cls)] in args.classes]
        now = time.time()
        if hits and (now - last_save) >= args.cooldown:
            last_save = now
            threat, conf = max(hits, key=lambda t: t[1])
            eid = uuid.uuid4().hex[:12]
            ev_img = Path("evidence") / f"{eid}.jpg"
            cv2.imwrite(str(ev_img), res.plot())  # annotated frame = evidence
            event = make_event(args.node, args.lat, args.lon, threat, conf, ev_img)
            with open(Path("events") / f"{event['event_id']}.json", "w") as f:
                json.dump(event, f, indent=2)
            print(f"[ALERT] {threat} conf={conf:.2f} -> {ev_img}  event={event['event_id']}")
    cap.release()


if __name__ == "__main__":
    main()
