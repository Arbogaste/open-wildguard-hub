# M8 — Prediction, Simulation & Adaptive Patrol Planning (SCAFFOLD)

> Mission: a risk engine that fuses patrol history, events, habitat, weather, moon, seasonality and
> community data into hotspots + priority scores, and plans unpredictable optimal patrol routes.

## Recommended repos / tools
| Repo / tool | Take this |
|------|-----------|
| [PAWS-public](https://github.com/lily-x/PAWS-public) | Harvard Stackelberg-game risk model + patrol planning under uncertainty; `iware/` balanced bagging for sparse data |
| [wildlifeRL](https://github.com/lucashu1/wildlifeRL) | RL/DDPG adversarial patrol simulation (grid env) |
| [poaching_occupancy](https://github.com/oliviergimenez/poaching_occupancy) | HMM occupancy models that de-bias ranger data |
| [DSA Alert Engine](https://github.com/Ruthwik9590/Tracking-and-Poaching-Alert-System-using-Advanced-Data-Structures) | Dijkstra nearest-ranger routing |

Orchestration: n8n/Windmill/Trigger.dev/Celery; agents CrewAI/AutoGen; drone swarm handoff (LangGraph).

## Milestones
- [ ] Build risk features from patrol+event history (de-biased via occupancy HMM).
- [ ] Hotspot map + priority scores on the hub.
- [ ] Patrol route generator (PAWS-style, unpredictable) → dispatch (links map route tool).
- [ ] Lunar-phase risk windows.

## International use cases
| Context | Adaptation |
|---------|------------|
| Large park, few rangers | optimize scarce patrols, rotate checkpoints |
| Data-poor reserve | balanced bagging + occupancy to act on sparse/biased data |
