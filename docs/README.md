# WildGuard AI — Operator Playbooks (the "repo of repos" for wildlife protection)

This `docs/` tree is the heart of the project. The dashboard (`index.html`) is only a shell.
**The real value is here**: for every capability an anti-poaching team could need, you get a
self-contained playbook that tells you exactly what to deploy, which proven open-source repo to
clone, what hardware to build, what scripts to run, and what to paste into any AI agent to get a
concrete build plan.

Clone this hub and you can stand up a wildlife-protection program — from a single Android phone in
a small sanctuary to a transfrontier park with drones, acoustic nodes and forensic chain-of-custody.

> Wildlife dies every day. This repo exists so a ranger team anywhere on Earth can act **today**
> with free tools, not wait for a vendor.

---

## How to use these playbooks

Each module in [`modules/`](modules/) follows the same structure:

1. **Goal** — what this capability does and the threat it counters.
2. **Field tiers** — Essential (phone-only) / Intermediate / Advanced. Pick what your budget allows.
3. **Recommended repos** — battle-tested open-source projects, with what to take from each.
4. **Hardware** — bill of materials + wiring, when relevant ([`../toolkit/arduino/`](../toolkit/arduino/)).
5. **Scripts** — runnable training/inference/processing code ([`../toolkit/python/`](../toolkit/python/)).
6. **Agent prompts** — copy-paste prompts ([`../prompts/`](../prompts/)) to drive any LLM agent
   (Claude Code, Cursor, etc.) to implement a milestone end-to-end.
7. **Milestones** — a concrete checklist anyone can follow.
8. **International use cases** — how the module adapts across regions/biomes/legal systems.

You do **not** need to be a developer to start. The Essential tier of most modules is a phone +
a free app + a printed protocol.

---

## The 10 modules

| # | Module | Counters | Status |
|---|--------|----------|--------|
| [M1](modules/M01-hub-architecture.md) | Hub, interop & governance | fragmentation, no shared data model | playbook |
| [M2](modules/M02-edge-vision.md) | Edge computer vision | poachers/vehicles/weapons/snares on camera | playbook |
| [M3](modules/M03-bioacoustics.md) | Bioacoustics & gunshot triangulation | gunshots, chainsaws, vehicles | playbook |
| [M4](modules/M04-aerial-geo.md) | Aerial, thermal & geospatial | night intrusion, escape routes | scaffold |
| [M5](modules/M05-species-intel.md) | Species-centric ecological intel | GPS collars, geofence, anomalies | scaffold |
| [M6](modules/M06-field-community.md) | Field collection & community intel | offline ranger data, informant safety | scaffold |
| [M7](modules/M07-osint.md) | OSINT & illegal-market intel | online trafficking, price signals | scaffold |
| [M8](modules/M08-prediction-rl.md) | Prediction, sim & patrol planning | predictable patrols, hotspot blindness | scaffold |
| [M9](modules/M09-forensics-legal.md) | Evidence chain & legal compliance | cases thrown out of court | scaffold |
| [M10](modules/M10-resilience-maint.md) | Resilience, training & open-source ops | system rot, no field training | scaffold |

`playbook` = fleshed out and runnable. `scaffold` = structure + repo pointers in place, being filled.

---

## Recommended open-source repos (master catalog)

These are the projects the playbooks pull from. Clone the ones your use case needs.

| Repo | Module | Take this |
|------|--------|-----------|
| [FaunaScope](https://github.com/tanmaynikhare45/FaunaScope-Wildlife-Camera-Trap-Analysis-Platform) | M1, M2, M5 | React+FastAPI hub blueprint; 2-stage blank/species ML; Leaflet + EXIF mapping |
| [wildlife-poaching-detection](https://github.com/karthikka430-rgb/wildlife-poaching-detection) | M2 | lean real-time YOLOv8 intruder detection + instant evidence snapshot |
| [Ecosentinel](https://github.com/Kerbal12/Ecosentinel) | M2 | classic OpenCV/YOLOv3 CCTV intruder benchmark |
| [Poaching-detection](https://github.com/Tarshdeep2210/Poaching-detection) | M2 | EfficientNet animal/empty/poacher classifier; synthetic data; Grad-CAM explainability |
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | M2, M3, M4 | bimodal video+audio consensus; gunshot/chainsaw Keras models; PyDeck 3D |
| [greenwood](https://github.com/mikukula/greenwood) | M3, M5 | sound-source localization; elephant/gunshot bioacoustic classifier |
| [PAWS-public](https://github.com/lily-x/PAWS-public) | M8 | Harvard Stackelberg-game risk model + optimal patrol planning |
| [wildlifeRL](https://github.com/lucashu1/wildlifeRL) | M8 | RL/DDPG adversarial patrol simulation |
| [poaching_occupancy](https://github.com/oliviergimenez/poaching_occupancy) | M8 | HMM occupancy models that de-bias ranger patrol data |
| [Illegal_Elephant_Poaching_App](https://github.com/grac3smith/Illegal_Elephant_Poaching_App) | M5, M8 | real CITES MIKE dataset + statistical threat viz |
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | M7, M9 | multilingual OSINT scrape + LLM entity extraction + chargesheet generator |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | M7, M9 | parse legal verdicts → smuggling-chain & black-market price data |
| [genetic-forensic-portal](https://github.com/uw-cefs/genetic-forensic-portal) | M9 | secure genotype submission portal (ivory/horn DNA tracing) |
| [WildlifeFL](https://github.com/MeGaurav4/WildlifeFL) | M10 | federated YOLOv8/CRNN training with differential privacy |
| [Tracking-and-Poaching-Alert (DSA)](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | M5, M6, M8 | pure-Python R-Tree geofence + Dijkstra routing (edge-friendly) |
| [Poaching-Hunting-Uncoop-Env](https://github.com/violentlydave/Poaching-Hunting-in-an-Uncooperative-Environment) | M7 | radio/Wi-Fi opsec audit so poachers can't intercept patrols |

External platforms worth adopting (not in catalog, production-grade): **SMART** (smartconservationtools.org),
**EarthRanger** (earthranger.com), **CyberTracker**, **Rainforest Connection / RFCx**, **OpenSoundscape**, **Wildbook**.

---

## Toolkit (runnable, no vendor)

- [`../toolkit/python/`](../toolkit/python/) — training & inference scripts you can run on a laptop/GPU.
- [`../toolkit/arduino/`](../toolkit/arduino/) — microcontroller node firmware (PIR + camera + store-and-forward).
- [`../toolkit/data/`](../toolkit/data/) — dataset pointers & the canonical event schema.

## Agent prompts

- [`../prompts/`](../prompts/) — paste-into-any-agent prompt packs to implement each milestone.
