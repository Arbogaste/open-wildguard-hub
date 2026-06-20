# M3 — Bioacoustics & Gunshot Triangulation

> Mission: 24/7 listening network that detects gunshots, chainsaws, off-road vehicles and animal
> distress calls, then **triangulates the source** (TDoA) onto the map for patrols/drones.

## 1. Goal
Sound travels where cameras can't see. Low-power microphones in the canopy catch a gunshot or a
chainsaw kilometers away, classify it in near-real-time, and — with 3+ nodes — compute the shot's
coordinates by time-difference-of-arrival. Counters poaching and illegal logging in dense forest
and at night, where vision fails.

## 2. Field tiers
| Tier | Hardware | What you get |
|------|----------|--------------|
| Essential | 1 phone/recorder + offline classifier | spot detection of gunshot/chainsaw, no location |
| Intermediate | 2-4 Pi/ESP32 + MEMS mic nodes, time-synced | detection + rough direction |
| Advanced | 5+ GPS-time-synced nodes + LoRa backhaul | full TDoA triangulation, distress-call models |

## 3. Recommended repos
| Repo | Take this | Notes |
|------|-----------|-------|
| [greenwood](https://github.com/mikukula/greenwood) | **sound-source localization** algorithms; elephant/gunshot classifier (Numpy/Scipy/TF) | core of this module |
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | `audio_stream.py` + pre-trained Keras gunshot/chainsaw models; video+audio consensus | ready-to-run detectors |
| [WildlifeFL](https://github.com/MeGaurav4/WildlifeFL) | CRNN audio model (5 classes) trained federated | for multi-park collaboration (M10) |

Adopt **OpenSoundscape** (open-source detection/classification/localization) and **FFmpeg** for
denoising (rain/wind). Reference platform: **Rainforest Connection (RFCx)**.

## 4. Hardware
- **Acoustic node**: ESP32 + I2S MEMS mic (INMP441 ~$3) + GPS module (for time sync) + LoRa.
  See [`../../toolkit/arduino/acoustic_node.ino`](../../toolkit/arduino/acoustic_node.ino) (scaffold:
  capture window → on-device energy/threshold gate → timestamped clip → LoRa).
- TDoA needs sub-ms time sync across nodes → use GPS PPS or a shared LoRa beacon.

## 5. Scripts
- [`../../toolkit/python/train_audio_classifier.py`](../../toolkit/python/train_audio_classifier.py)
  — train a gunshot/chainsaw/vehicle/distress classifier from labeled WAV clips (mel-spectrogram CNN).
  CPU-friendly; exports TFLite for edge nodes.
- [`../../toolkit/python/tdoa_locate.py`](../../toolkit/python/tdoa_locate.py)
  — given per-node arrival timestamps + node GPS coords, solve for the sound source location.

## 6. Agent prompts
- [`../prompts/M03-bioacoustics.prompts.md`](../prompts/M03-bioacoustics.prompts.md) — prompts to build
  the spectrogram classifier, the node firmware, and the TDoA solver service.

## 7. Milestones
- [ ] Gather labeled clips (gunshot/chainsaw/vehicle/ambient); augment with FFmpeg noise.
- [ ] Train with `train_audio_classifier.py`; export TFLite; validate on-device latency.
- [ ] Deploy 1 node → confirm detection events. Then 3+ time-synced nodes.
- [ ] Run `tdoa_locate.py` on real arrival timestamps; verify location error < target meters.
- [ ] Push located events to the map (M1) and patrol dispatch (M8).

## 8. International use cases
| Region / biome | Adaptation |
|----------------|------------|
| African savanna | gunshot priority; long inter-node spacing (open terrain, sound carries) |
| SE-Asia / Amazon canopy | chainsaw + gunshot; denser node grid (sound attenuates in foliage) |
| EU temperate forest | gunshot + off-road vehicle; integrate with hunting-season legal rules (M9) |
| Mountain (snow leopard) | wind denoising critical; ruggedized cold-weather enclosures |
