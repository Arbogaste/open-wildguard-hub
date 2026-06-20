#!/usr/bin/env python3
"""
WildGuard M3 — Train a threat-sound classifier (gunshot / chainsaw / vehicle / ambient) from WAV
clips using mel-spectrograms + a small CNN. CPU-friendly. Exports ONNX for edge nodes.

Dataset layout
--------------
    audio/
      train/gunshot/*.wav  train/chainsaw/*.wav  train/vehicle/*.wav  train/ambient/*.wav
      val/...

Tips: augment with FFmpeg (mix rain/wind, vary gain) so the model survives field noise.

Run
---
    pip install torch torchaudio
    python train_audio_classifier.py --data audio --epochs 20 --export onnx
"""
import argparse
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="WildGuard M3 audio trainer")
    p.add_argument("--data", required=True, help="dataset root with train/ and val/")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--sr", type=int, default=16000, help="resample rate")
    p.add_argument("--seconds", type=float, default=2.0, help="clip window")
    p.add_argument("--export", choices=["onnx"], default=None)
    args = p.parse_args()

    try:
        import torch
        import torchaudio
        from torch import nn
        from torch.utils.data import Dataset, DataLoader
        from torchvision import models
    except ImportError:
        sys.exit("Install: pip install torch torchaudio torchvision")

    n_samples = int(args.sr * args.seconds)
    melspec = torchaudio.transforms.MelSpectrogram(sample_rate=args.sr, n_mels=64)
    to_db = torchaudio.transforms.AmplitudeToDB()

    class Clips(Dataset):
        def __init__(self, split):
            base = Path(args.data) / split
            self.classes = sorted([d.name for d in base.iterdir() if d.is_dir()])
            self.items = [(f, self.classes.index(d.name))
                          for d in base.iterdir() if d.is_dir()
                          for f in d.glob("*.wav")]

        def __len__(self): return len(self.items)

        def __getitem__(self, i):
            f, label = self.items[i]
            wav, sr = torchaudio.load(f)
            if sr != args.sr:
                wav = torchaudio.functional.resample(wav, sr, args.sr)
            wav = wav.mean(0, keepdim=True)  # mono
            if wav.shape[1] < n_samples:
                wav = torch.nn.functional.pad(wav, (0, n_samples - wav.shape[1]))
            wav = wav[:, :n_samples]
            spec = to_db(melspec(wav))            # [1, 64, T]
            spec = spec.repeat(3, 1, 1)           # 3ch for mobilenet
            return spec, label

    train_ds, val_ds = Clips("train"), Clips("val")
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
            opt.zero_grad(); lossf(net(x), y).backward(); opt.step()
        net.eval(); correct = total = 0
        with torch.no_grad():
            for x, y in vl:
                x, y = x.to(dev), y.to(dev)
                correct += (net(x).argmax(1) == y).sum().item(); total += y.numel()
        print(f"[wildguard] epoch {ep+1}/{args.epochs}  val_acc={correct/max(total,1):.3f}")

    torch.save({"model": net.state_dict(), "classes": classes}, "audio_threat_cls.pt")
    print("[wildguard] saved -> audio_threat_cls.pt")
    if args.export == "onnx":
        torch.onnx.export(net, torch.randn(1, 3, 64, int(n_samples / 200) + 1, device=dev),
                          "audio_threat_cls.onnx", input_names=["mel"], output_names=["logits"])
        print("[wildguard] exported -> audio_threat_cls.onnx")


if __name__ == "__main__":
    main()
