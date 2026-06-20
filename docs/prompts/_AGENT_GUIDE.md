# Agent prompt packs

Copy-paste prompts to drive **any** coding agent (Claude Code, Cursor, Aider, etc.) to implement a
WildGuard milestone end-to-end. Each pack assumes the agent has cloned this hub.

## How to use
1. Open your agent in a fresh repo (or this hub).
2. Paste the **context primer** below, then the milestone prompt from the module's `.prompts.md`.
3. Review every output. These prompts produce a *plan + code*; you keep judgment (field safety,
   legality, privacy — see M9).

## Context primer (paste first, always)
```
You are helping build WildGuard, an offline-first, open-source anti-poaching toolkit for ranger
teams in low-resource conservation areas. Constraints that override default choices:
- Offline-first: every critical workflow must work with no network; sync is opportunistic.
- Runs on constrained hardware (Raspberry Pi, ESP32, old laptops). Prefer small models, TFLite/ONNX.
- Flat, versioned data: events follow toolkit/data/event_schema.json (Tactical Event).
- Evidence integrity matters (chain-of-custody, SHA-256, timestamps) — legal cases depend on it.
- Favor proven open-source repos over greenfield. Reuse, document, integrate. No vendor lock-in.
- Output a concrete plan first (files, steps, test plan), then code. Explain trade-offs briefly.
```

## Packs
- [`M02-edge-vision.prompts.md`](M02-edge-vision.prompts.md)
- (more per module as they reach `playbook` status)
