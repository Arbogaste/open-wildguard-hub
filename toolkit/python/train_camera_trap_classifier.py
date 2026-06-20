#!/usr/bin/env python3
"""
WildGuard M2 — Train a camera-trap classifier (human / animal / vehicle / empty).

Two modes:
  * YOLO mode  (default): fine-tune Ultralytics YOLOv8 for detection. Best for boxes + edge export.
  * cls  mode: train a lightweight transfer-learning image classifier (no boxes) when you only
               have whole-image labels. Pure torchvision, CPU-friendly.

Dataset layout
--------------
YOLO mode (Ultralytics format):
    dataset/
      data.yaml            # names: [human, animal, vehicle], train/val paths
      images/train/*.jpg
      labels/train/*.txt
classifier mode:
    dataset/
      train/human/*.jpg  train/animal/*.jpg  train/vehicle/*.jpg  train/empty/*.jpg
      val/...

Run
---
    pip install -r requirements.txt
    # YOLO
    python train_camera_trap_classifier.py --mode yolo --data dataset/data.yaml --epochs 50 --export onnx
    # classifier
    python train_camera_trap_classifier.py --mode cls --data dataset --epochs 15 --export tflite

Edge export gives you ONNX / TFLite to run on Raspberry Pi, Jetson or via OpenVINO. See
edge_infer_camera.py for live inference.
"""
import argparse
import sys
from pathlib import Path


def train_yolo(args):
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit("Install ultralytics:  pip install ultralytics")
    model = YOLO(args.weights or "yolov8n.pt")  # nano = edge-friendly
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
                project="runs_wildguard", name="camera_trap")
    metrics = model.val()
    print(f"[wildguard] mAP50={metrics.box.map50:.3f}  mAP50-95={metrics.box.map:.3f}")
    if args.export:
        path = model.export(format=args.export)  # 'onnx' | 'tflite' | 'openvino'
        print(f"[wildguard] exported edge model -> {path}")


def train_classifier(args):
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader
        from torchvision import datasets, transforms, models
    except ImportError:
        sys.exit("Install torch + torchvision:  pip install torch torchvision")

    root = Path(args.data)
    tf_train = transforms.Compose([
        transforms.Resize((224, 224)), transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(),
    ])
    tf_val = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
    train_ds = datasets.ImageFolder(root / "train", tf_train)
    val_ds = datasets.ImageFolder(root / "val", tf_val)
    classes = train_ds.classes
    print(f"[wildguard] classes: {classes}")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    net = models.mobilenet_v3_small(weights="DEFAULT")
    net.classifier[-1] = nn.Linear(net.classifier[-1].in_features, len(classes))
    net = net.to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-4)
    lossf = nn.CrossEntropyLoss()
    tl = DataLoader(train_ds, batch_size=args.batch, shuffle=True)
    vl = DataLoader(val_ds, batch_size=args.batch)

    for ep in range(args.epochs):
        net.train()
        for x, y in tl:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad(); loss = lossf(net(x), y); loss.backward(); opt.step()
        net.eval(); correct = total = 0
        with torch.no_grad():
            for x, y in vl:
                x, y = x.to(dev), y.to(dev)
                correct += (net(x).argmax(1) == y).sum().item(); total += y.numel()
        print(f"[wildguard] epoch {ep+1}/{args.epochs}  val_acc={correct/max(total,1):.3f}")

    out = Path("camera_trap_cls.pt"); torch.save({"model": net.state_dict(), "classes": classes}, out)
    print(f"[wildguard] saved -> {out}")
    if args.export == "onnx":
        import torch as t
        t.onnx.export(net, t.randn(1, 3, 224, 224, device=dev), "camera_trap_cls.onnx",
                      input_names=["image"], output_names=["logits"])
        print("[wildguard] exported -> camera_trap_cls.onnx")
    elif args.export:
        print("[wildguard] for tflite: export onnx then use onnx2tf, or train via YOLO mode.")


def main():
    p = argparse.ArgumentParser(description="WildGuard M2 camera-trap trainer")
    p.add_argument("--mode", choices=["yolo", "cls"], default="yolo")
    p.add_argument("--data", required=True, help="data.yaml (yolo) or dataset root (cls)")
    p.add_argument("--weights", help="base weights (yolo)")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--export", choices=["onnx", "tflite", "openvino"], default=None)
    args = p.parse_args()
    (train_yolo if args.mode == "yolo" else train_classifier)(args)


if __name__ == "__main__":
    main()
