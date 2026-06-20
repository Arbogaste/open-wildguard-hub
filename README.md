# WildGuard AI / open-wildguard-hub

WildGuard AI is an offline-first, field-oriented anti-poaching platform designed for remote conservation areas where power, bandwidth, and hardware are limited. The repository is intentionally structured as a practical operating system for wildlife protection, not as a heavyweight enterprise stack.

This repository currently serves two roles:

1. It is the product home for the platform architecture, roadmap, and operator-facing documentation.
2. It is the public-facing guide for how to extend the project with new capabilities, new datasets, and new use-case specific documents.

## What This Repo Is For

- A lightweight command center for conservation operations.
- A modular technical base that can grow from a minimal edge deployment to a broader multi-site ecosystem.
- A documentation hub for people who need to adapt the system to their own field conditions.
- A reference implementation that favors local operation, explicit data contracts, and safe synchronization over infrastructure complexity.

## What This Repo Is Not

- It is not a cloud-first SaaS product.
- It is not a microservices platform.
- It is not tied to a single vendor or a single deployment target.
- It is not meant to depend on live connectivity to remain useful in the field.

## Core Principles

1. Simplicity first
   - Keep the moving parts small and understandable.
   - Avoid abstraction layers that do not directly reduce risk or effort.
   - Prefer explicit data contracts over implicit behavior.

2. Offline-first by default
   - Local operation must continue when connectivity is weak or absent.
   - Sync should be opportunistic, not foundational.
   - Every critical workflow needs a local fallback.

3. Flat, standard data formats
   - Use JSON, GeoJSON, CSV, and line-delimited logs.
   - Keep schemas versioned and documented.
   - Avoid custom transport logic unless it solves a real field constraint.

4. Production readiness over prototype aesthetics
   - Every new feature should ship with a fallback path, a test plan, and a doc update.
   - Operators must be able to understand the system without reading the code.
   - A feature is not done until it can survive field conditions.

## Documentation Contract

The documentation is intentionally split by role:

- `README.md`
  - Project mission, current scope, delivery milestones, and release readiness.
- `goal.md`
  - The canonical objective, non-goals, and acceptance criteria.
- `dev.md`
  - The master technical guide for architecture, implementation rules, and future documentation structure.
- Future `docs/use-cases/*.md`
  - One guide per real-world workflow or deployment scenario.
- `index.html`
  - The interactive command center and operator guide for practical use cases.

## Roadmap

The platform is being hardened in milestone order. The current state is documentation-first with an interactive prototype UI, and the next steps are aimed at production-grade foundations.

| Milestone | Status | Outcome |
|---|---|---|
| M0 | In progress | Canonical mission, documentation map, and delivery contract |
| M1 | In progress | Production-oriented README, goal file, and technical master guide |
| M2 | Planned | Stable local runtime, event schema, and persistence layer |
| M3 | Planned | Offline synchronization, queueing, and evidence integrity |
| M4 | Planned | Field workflows and use-case specific guides |
| M5 | Planned | Edge services for vision, audio, telemetry, and mapping |
| M6 | Planned | Release hardening, testing, and deployment readiness |

## Immediate Priorities

1. Make the documentation the source of truth for the project.
2. Define the production-ready scope clearly enough that the implementation can move without ambiguity.
3. Expand the HTML dashboard into a real operator guide for common field scenarios.
4. Keep the technical design small enough to run on constrained hardware.
5. Add one document per use case as the codebase grows.

## Current Build Focus

- The HTML dashboard should explain how the platform is used in real situations, not just how it looks.
- The technical docs should explain how to deploy, extend, and maintain the system independently.
- The repository should be useful before every planned capability is complete.
- Field safety and evidence integrity remain higher priority than feature breadth.

## Quick Start

This repository is still in active development. The current front-end is a static prototype and should be treated as the command center shell, not the full runtime.

```bash
cd open-wildguard-hub
```

Open `index.html` to review the dashboard and the embedded guidance.

## Production Readiness Criteria

The project can be considered production ready when it can:

- Run on constrained hardware with local persistence.
- Continue operating when network access is unavailable.
- Synchronize events safely when connectivity returns.
- Preserve evidence integrity and a clear chain of custody.
- Provide clear, practical guidance for real field workflows.
- Support new use cases without forcing a rewrite of the core.

## Upstream Codebase Approach

This hub is intended to orchestrate and document capabilities that may be sourced from existing open projects. The long-term goal is not to absorb everything into one monolith, but to expose stable interfaces, shared conventions, and practical integration patterns.

## License

MIT License, unless a specific upstream component requires a different license.
