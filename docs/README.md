# WildGuard AI — Operator Playbooks

The `docs/` folder is the real product. The dashboard (`index.html`) is a shell.
Here you get a **complete implementation guide** for every capability an anti-poaching team needs —
from a single phone in a small sanctuary to a transfrontier network with drones, acoustic nodes, and
court-ready forensic chain-of-custody.

> **Wildlife dies every day. This exists so a ranger team anywhere on Earth can act today with free tools — not wait for a vendor.**

---

## Who is this for?

| You are… | Start with… |
|-----------|------------|
| A **field ranger** with no coding experience | M6 (offline patrol logging) → M3 (gunshot alerts) |
| An **NGO or park manager** setting up a new system | M1 (hub) → M2 (cameras) → M9 (evidence chain) |
| A **developer / technologist** wanting to contribute | M2 or M3 (most code depth) → M8 (prediction AI) |
| A **researcher or analyst** | M5 (species intel) → M7 (OSINT) → M8 (occupancy models) |
| An **incident investigator or lawyer** | M9 (evidence chain + chargesheet generator) |

You do **not** need to be a developer to start. The Essential tier of every module works with a phone and a free app.

---

## The 10 modules — what each one does and why it matters

Each module solves one specific problem rangers face in the field. They are independent — deploy one, all, or any combination.

---

### M1 · Set up the platform
**[→ Full playbook](modules/M01-hub-architecture.md)**

**The problem**: ranger teams across a park use incompatible apps, WhatsApp groups, paper forms and spreadsheets. An alert on one radio reaches only part of the team. Evidence is scattered. There is no shared picture.

**What this gives you**: a central command hub — a local server or cloud API — that collects all events (camera traps, audio nodes, GPS collars, community tips) into one database. Every team member sees the same map. Alerts are routed automatically. Data syncs when connectivity returns.

**Who deploys it**: one technologist or IT-savvy NGO staff member. Everyone else just uses the result.

**Effort**: 1–2 days for the Essential tier (FastAPI + SQLite + Leaflet map).

---

### M2 · Detect humans on camera — automatically
**[→ Full playbook](modules/M02-edge-vision.md)**

**The problem**: a reserve has dozens of camera traps. A ranger reviews thousands of images per week manually. Poachers are missed because no human can watch every feed. At night, without thermal, cameras are nearly blind.

**What this gives you**: AI that runs directly on the camera trap or on a Raspberry Pi next to it. When a human, vehicle, or weapon appears, it fires an alert in under 30 seconds — without sending the image to any cloud service. Photos of confirmed detections are auto-tagged as evidence with GPS, timestamp, and SHA-256 hash.

**Why on-device**: no cloud bill, works offline, legally safer (no biometric data leaves the park).

**Effort**: 1 afternoon to flash a Pi with the included firmware. Full training pipeline for local species/environment: 1–2 days with a GPU.

---

### M3 · Detect gunshots and chainsaws — 24/7
**[→ Full playbook](modules/M03-bioacoustics.md)**

**The problem**: a ranger hears a gunshot 3 km away. By the time they find the direction and drive there, the poachers are gone. Chainsaws in remote logging are never heard at all.

**What this gives you**: a network of cheap microphone nodes (≈$15 each, Raspberry Pi Zero + microphone) that listen continuously. When a gunshot or chainsaw is detected, the hub triangulates the location using time-difference-of-arrival and pins it on the map. Rangers get GPS coordinates, not a compass direction.

**Accuracy**: 3-node triangle reaches ≈50 m accuracy for gunshots within a 1 km radius.

**Effort**: 3–4 nodes, each takes 2 hours to assemble. Software: 1 day.

---

### M4 · Aerial and satellite overwatch
**[→ Playbook](modules/M04-aerial-geo.md)**

**The problem**: poachers move through terrain rangers cannot patrol on foot. Night-time intrusions are invisible. After an incident, there is no aerial record of escape routes.

**What this gives you**: scheduled drone patrol routes that cover the highest-risk zones automatically. Thermal imaging identifies human heat signatures at night that optical cameras miss. Post-flight photogrammetry (WebODM) creates updated terrain maps. Satellite layers from Sentinel-2 give free weekly coverage for deforestation monitoring.

**Hardware requirement**: any DJI or ArduPilot-compatible drone. The AI runs on a laptop connected at base.

**Effort**: flight planning takes 30 minutes once configured. Full thermal analysis pipeline: 1 day.

---

### M5 · Track animals and detect anomalies
**[→ Playbook](modules/M05-species-intel.md)**

**The problem**: a tagged elephant stops moving. Is it dead? Asleep? Injured? A ranger drives 40 km to check. Meanwhile, the collar data was there — no one built the alert.

**What this gives you**: automatic ingestion of GPS collar data with stillness alerts (animal hasn't moved in X hours → automatic flag on the map). Virtual geofences trigger alerts when animals leave safe zones. Photo-ID integration (Wildbook) lets you track individuals from camera images without physical collars.

**Also useful for**: detecting unusual clustering (multiple animals fleeing = possible human disturbance), population monitoring reports, donor accountability data.

**Effort**: collar ingestion script runs in 1 hour. Geofence setup: 30 minutes per zone.

---

### M6 · Log patrols and receive community tips — offline
**[→ Playbook](modules/M06-field-community.md)**

**The problem**: rangers log patrols on paper. Community informants can't report safely — there is no anonymous channel. Managers have no idea where rangers actually went or what they found.

**What this gives you**: SMART-compatible offline patrol logging on Android (no connectivity required). Community tip portal via LimeSurvey with anonymous submission and automatic translation. All data syncs to the hub when the ranger returns to range. Privacy rules prevent tip-offs that could identify informants.

**Why it matters for evidence**: patrol records with GPS tracks + timestamps are admissible in court. They prove when and where rangers were, and what they found.

**Effort**: SMART app install + sync config: 2 hours. Community portal setup: 1 day.

---

### M7 · Monitor illegal wildlife markets online
**[→ Playbook](modules/M07-osint.md)**

**The problem**: ivory and rhino horn trading has moved to Facebook Marketplace, WhatsApp groups, Telegram channels, and local classified sites. Rangers are not trained to monitor these. By the time an alert reaches law enforcement, the seller has deleted the post.

**What this gives you**: automated scrapers that monitor target platforms and extract species, price, location, and seller contact from each listing. EXIF metadata from seized photos is extracted automatically (GPS coordinates where the photo was taken). Price spike monitoring flags unusual market activity that precedes large seizures.

**Legal note**: all monitoring uses only public data accessible without authentication. Evidence is archived with timestamps and hashes.

**Effort**: scraper setup: 1 day. Monitoring is then automatic with daily digest to email or Telegram.

---

### M8 · Predict where poachers strike next
**[→ Playbook](modules/M08-prediction-rl.md)**

**The problem**: rangers patrol the same routes every day. Poachers know this. They simply wait. Meanwhile, the actual high-risk zones are under-patrolled because no one has done the analysis.

**What this gives you**: a risk map updated daily, combining moon phase, species GPS movement, patrol history, vegetation cover, and seasonal factors. A route generator builds unpredictable patrol routes that still cover the highest-risk zones. Reinforcement learning models learn from adversarial data to counter adaptive poachers.

**What it does NOT do**: it does not predict individuals or use surveillance. It predicts terrain risk, not people.

**Effort**: first risk model runs in 2 hours with existing patrol data. Full RL training: 1–2 GPU-days.

---

### M9 · Build court-ready evidence
**[→ Playbook](modules/M09-forensics-legal.md)**

**The problem**: a poacher is caught. The photos exist. The GPS log exists. But the case is thrown out because no one can prove the files weren't altered after collection, the chain of custody is broken, or the species identification is contested.

**What this gives you**: every photo, audio clip, and GPS event is SHA-256 hashed at the moment of capture and logged with who handled it and when. The chargesheet generator cites the correct articles of wildlife law for your jurisdiction (India/Kenya/EU/others). Genetic forensics integration links seized ivory or horn to specific poaching hotspots via DNA.

**Why this is the most important module**: an unbroken evidence chain turns a poacher into a conviction. Without it, all the other technology is wasted.

**Effort**: hash pipeline runs automatically once configured (30 minutes). Chargesheet generation: instant from existing event data.

---

### M10 · Keep the system running long-term
**[→ Playbook](modules/M10-resilience-maint.md)**

**The problem**: a system that breaks silently is worse than no system. Camera traps fill their SD cards. Batteries die. AI models degrade as animals change behavior or poachers change tactics. New rangers don't know how to use the system.

**What this gives you**: automated health monitoring for every node (battery %, last-seen, SD space, model accuracy). Predictive alerts warn you to change a battery 7 days before it dies. Federated learning lets multiple reserves improve their shared AI models without sharing location-sensitive images. Scenario-based ranger training exercises with debrief checklists.

**Effort**: health dashboard: 1 day. Scenario training exercise: 2 hours to run, zero code required.

---

## Recommended open-source repos — what each one is for

These are the projects the playbooks pull from. Each entry explains the problem it solves, not just its name.

---

### Computer vision & camera traps

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [MegaDetector](https://github.com/microsoft/MegaDetector) | Detects animals, humans, and vehicles in camera-trap images with state-of-the-art accuracy. Used by hundreds of conservation projects worldwide. | Your starting point for any camera-trap AI. Use this before building custom models. |
| [MegaDetector-Classifier](https://github.com/microsoft/MegaDetector-Classifier) | Fine-tunes MegaDetector for species identification in your specific region/biome. | After MegaDetector filters out blanks, this identifies what species triggered the camera. |
| [wildlife-poaching-detection](https://github.com/karthikka430-rgb/wildlife-poaching-detection) | Lean real-time YOLOv8 pipeline that flags human intruders and immediately saves an evidence snapshot. | When you need live alerting from a Pi-connected camera, not batch processing. |
| [Poaching-detection](https://github.com/Tarshdeep2210/Poaching-detection) | EfficientNet classifier that distinguishes animal / empty / poacher with Grad-CAM explainability (highlights what the AI is looking at). | When you need explainable AI for court evidence or for retraining with local data. |
| [Ecosentinel](https://github.com/Kerbal12/Ecosentinel) | OpenCV + YOLOv3 CCTV intruder detection benchmark. Older but well-documented. | Useful as a baseline for comparing detection accuracy or for hardware with no GPU. |
| [animl-frontend](https://github.com/tnc-ca-geo/animl-frontend) | Operational camera-trap management UI used by The Nature Conservancy. Handles image ingestion, labeling, and operator review workflow. | When you need a production-grade operator interface for reviewing camera-trap images at scale. |

---

### Bioacoustics & audio detection

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [MegaDetector-Acoustic](https://github.com/microsoft/MegaDetector-Acoustic) | Microsoft's bioacoustic model suite for wildlife sound monitoring. Covers species calls, gunshots, chainsaws. | Starting point for any audio detection — mirrors the reliability of MegaDetector for sound. |
| [SPARROW](https://github.com/microsoft/SPARROW) | Reference hardware design and firmware for edge audio recording nodes. Tells you exactly what microphone to buy and how to flash it. | Use this to build the acoustic nodes for M3. It eliminates the hardware guesswork. |
| [greenwood](https://github.com/mikukula/greenwood) | Sound-source localization + elephant call / gunshot classifier. Includes TDoA (time-difference-of-arrival) triangulation code. | When you have 3+ microphone nodes and want to triangulate shot locations on the map. |
| [Forest-Conservation-System](https://github.com/KarnaPratik/Forest-Conservation-System) | Combines video (YOLOv3) + audio (Keras gunshot/chainsaw detector) and fuses both signals before alerting. Reduces false positives. | When you want to require both visual AND audio confirmation before sending an alert. |

---

### Aerial & geospatial

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [MegaDetector-Overhead](https://github.com/microsoft/MegaDetector-Overhead) | Detects wildlife and humans in overhead/aerial imagery from drones and satellites. Adapted from MegaDetector for top-down view. | Any drone or satellite imagery pipeline. Handles the scale-change challenge that breaks ground-level models. |
| [FaunaScope](https://github.com/tanmaynikhare45/FaunaScope-Wildlife-Camera-Trap-Analysis-Platform) | React + FastAPI hub with Leaflet map, EXIF geo-tagging, and 2-stage blank/species ML pipeline. Clean architecture blueprint. | Reference when designing the hub API and map UI — good code to fork rather than build from scratch. |

---

### Species intelligence & ecology

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [Tracking-and-Poaching-Alert (DSA)](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | Pure-Python R-Tree spatial index + Dijkstra shortest-path for geofence alerts and patrol routing. Runs on a Pi with no heavy dependencies. | Edge deployments with no GPU and no cloud. Implements geofencing and routing in < 100 MB RAM. |
| [Illegal_Elephant_Poaching_App](https://github.com/grac3smith/Illegal_Elephant_Poaching_App) | Uses the real CITES MIKE (Monitoring the Illegal Killing of Elephants) dataset for occupancy modelling and threat visualization. | Research and reporting. Shows donors and government bodies where elephant poaching is statistically concentrated. |
| [poaching_occupancy](https://github.com/oliviergimenez/poaching_occupancy) | Hidden Markov Model occupancy analysis that corrects for patrol effort bias (areas patrolled more look riskier just because rangers go there). | Any statistical analysis of where poaching actually occurs vs. where rangers look. Critical for unbiased risk mapping. |
| [MammAlps](https://github.com/eceo-epfl/MammAlps) | Dense multi-view video + audio behavior annotation dataset for Alpine mammals. Benchmark for multi-modal behavior recognition. | Training or benchmarking models that need to recognize specific animal behaviors (fleeing, feeding, injury) from multi-camera setups. |

---

### OSINT & market intelligence

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [Wildlife-News](https://github.com/Siddhanthkjain2005/Wildlife-News) | Multilingual web scraper + LLM entity extraction that pulls species, price, location from wildlife trade posts. Also includes the chargesheet generator the hub demo uses. | Starting point for any online market monitoring. The LLM extraction works with local Ollama models — no API key required. |
| [anti-poaching-platform](https://github.com/lemonadedw/anti-poaching-platform) | Parses court verdicts and seizure reports into structured smuggling-chain and black-market price data. Builds a searchable precedent database. | Investigative work. Helps identify trafficking networks and predict which routes/species come next based on past convictions. |
| [Poaching-Hunting-Uncoop-Env](https://github.com/violentlydave/Poaching-Hunting-in-an-Uncooperative-Environment) | Radio/Wi-Fi operational security audit framework. Models how poachers intercept patrol communications. | If your team suspects your patrol radio traffic or mobile data is being monitored. Run this audit first before changing comms. |

---

### Prediction & patrol planning

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [PAWS-public](https://github.com/lily-x/PAWS-public) | Harvard Stackelberg game-theoretic model. Computes optimal patrol strategies assuming poachers are rational adversaries who adapt to predictable patrols. | Production patrol planning in parks where poachers are organized and experienced. Deployed in real parks in Uganda, Cambodia, Malaysia. |
| [wildlifeRL](https://github.com/lucashu1/wildlifeRL) | Reinforcement learning / DDPG simulation environment. Trains an AI patrol agent against an adversarial poacher agent. | Research and experimentation. Use this to test patrol strategies in simulation before deploying in the field. |

---

### Evidence & legal

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [genetic-forensic-portal](https://github.com/uw-cefs/genetic-forensic-portal) | Secure web portal for submitting wildlife DNA genotypes to population databases. Links seized ivory or horn to the geographic origin of the animal and specific known poaching hotspots. | Transnational trafficking cases where you need to prove the material crossed borders and identify the source population. |

---

### Platform infrastructure

| Repo | What it actually does | When to use it |
|------|-----------------------|----------------|
| [Biodiversity](https://github.com/microsoft/Biodiversity) | Microsoft's umbrella hub for conservation AI: documentation, model zoo, ecosystem links, and coordination across all their wildlife projects. | Orientation. Read this before choosing which Microsoft models to use — it maps the whole ecosystem. |
| [Pytorch-Wildlife](https://github.com/microsoft/Pytorch-Wildlife) | Unified training and inference framework for all Microsoft wildlife models. One codebase to run MegaDetector, Acoustic, and Overhead. | When you want a single pipeline to train and deploy multiple model types without switching frameworks. |
| [WildlifeFL](https://github.com/MeGaurav4/WildlifeFL) | Federated learning (Flower framework) for YOLOv8/CRNN with differential privacy. Multiple reserves improve a shared model without sharing location-sensitive images. | Multi-reserve networks where data sharing raises legal or security concerns. Each reserve keeps its raw images. |
| [audtheia-environmental-monitoring](https://github.com/AudtheiaOfficial/audtheia-environmental-monitoring) | Environmental monitoring automation with geo enrichment, event schemas, and workflow triggers. | Integration layer. Useful when connecting sensors from multiple vendors into a unified event pipeline. |

---

## External platforms (production-grade, not in this repo)

These are deployed in real parks today. Worth adopting in parallel with this toolkit:

| Platform | What it does | Cost |
|----------|--------------|------|
| **SMART** (smartconservationtools.org) | Gold standard for patrol management and ranger data collection. Works offline. Used in 1000+ protected areas. | Free |
| **EarthRanger** (earthranger.com) | Real-time situational awareness platform. Integrates GPS collars, camera alerts, radio check-ins on one map. | Free for NGOs |
| **Rainforest Connection / RFCx** | Solar-powered acoustic sensors + cloud AI that detects chainsaws and gunshots in real time. Used in 30+ countries. | Subsidized for reserves |
| **Wildbook** (wildbook.org) | Photo-ID platform for individual animal recognition. Matches individuals across camera-trap images automatically. | Free |
| **OpenSoundscape** | Python library for bioacoustic analysis. Widely used in academic wildlife monitoring. | Free / open source |
| **CyberTracker** | Offline data collection app for rangers. Works on cheap Android phones. Developed for African reserves. | Free |

---

## Toolkit (runnable code, no vendor required)

- [`../toolkit/python/`](../toolkit/python/) — training and inference scripts you can run on a laptop. Camera detection, audio classifier, TDoA localization, OSINT scraper.
- [`../toolkit/arduino/`](../toolkit/arduino/) — firmware for PIR + camera nodes and acoustic nodes. Flash, deploy, done.
- [`../toolkit/data/`](../toolkit/data/) — canonical event JSON schema and dataset pointers.

## Agent prompts

- [`../prompts/`](../prompts/) — paste any of these into Claude, GPT-4o, Gemini, or Cursor to get a working implementation of a specific milestone. Each prompt is self-contained and specifies exactly what to build.
