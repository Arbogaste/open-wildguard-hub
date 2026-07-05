# M3 Bioacoustics — agent prompt pack

> Paste the context primer from `_AGENT_GUIDE.md` first, then one prompt below.

## P1 — Build the spectrogram classifier (edge-ready)
```
Implement a Python trainer + inference for an acoustic threat classifier.
Classes (default): gunshot, chainsaw, vehicle, distress, ambient.
1. Load labeled WAV clips from a folder layout class_name/*.wav.
2. Convert to log-mel spectrograms (librosa or torchaudio), fixed window (e.g. 1s) with overlap.
3. Train a small CNN (CPU-friendly); report per-class precision/recall + confusion matrix.
4. Export TFLite (int8) for ESP32/Pi edge nodes; print model size + on-device latency estimate.
5. Inference CLI reads a WAV (or mic stream), emits a Tactical Event JSON per detection conforming to
   toolkit/data/event_schema.json (threat_class = the predicted class, confidence, sha256 of the clip).
Use ESC-50 as hard negatives and xeno-canto for bird/ambient. Reference the CRNN in WildlifeFL and the
Keras detectors in Forest-Conservation-System. Start from toolkit/python/train_audio_classifier.py and
improve it. Keep deps minimal.
```

## P2 — Acoustic node firmware (ESP32 + I2S MEMS)
```
Write/extend ESP32 firmware for an acoustic node: I2S MEMS mic (INMP441), deep-sleep until an
energy/threshold gate fires, then capture a short window, timestamp it from GPS PPS (sub-ms), and send
a compact LoRa packet (node_id, timestamp, peak energy, optional class if on-device TFLite runs).
Power budget matters: stay in deep sleep, wake on sound. Provide the wiring notes and the LoRa packet
format. Start from toolkit/arduino/acoustic_node.ino.
```

## P3 — TDoA localization service
```
Build a service that collects per-node arrival timestamps for the SAME event (matched by time window
+ energy) from 3+ time-synced nodes, then solves for the source coordinates by time-difference-of-
arrival (least squares on a local ENU plane), and writes a located Tactical Event to the events/ dir.
Handle: node clock offsets, outlier rejection, and a confidence/error estimate (meters). Start from
toolkit/python/tdoa_locate.py (which already solves a single event) and wrap it into a streaming
matcher. Push located events to the map (M1) and patrol dispatch (M8).
```

## P4 — Denoise & robustness (rain/wind)
```
Add a preprocessing stage that improves detection in bad weather: FFmpeg/torchaudio high-pass +
spectral-gating denoise for rain/wind before the classifier; and a hard-negative mining loop that
folds misfires (wind gusts, thunder, birds) back into the ambient class. Quantify the precision gain
on a held-out noisy set. Keep it cheap enough for edge nodes.
```

## P5 — Weekly acoustic briefing
```
Generate a weekly acoustic summary from the events DB: counts per class per zone, time-of-day
patterns (gunshots cluster at night?), any new chainsaw hotspot, and located events plotted. Output a
plain-text briefing + a JSON summary for the hub. Flag zones whose acoustic activity overlaps an M8
high-risk cell.
```
