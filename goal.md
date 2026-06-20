# WildGuard AI Goal

## Objective

Build a production-ready, offline-first anti-poaching platform that can protect wildlife in remote conservation areas and remain useful even when power, connectivity, and compute resources are limited.

## Why This Exists

The project must do two things at once:

1. Deliver practical capabilities for field teams as soon as possible.
2. Create reusable capabilities, resources, and documentation so other teams can adapt the platform independently.

This means the repository is both a product and a technical reference.

## Primary Outcomes

- A stable command center UI that explains and supports real field workflows.
- A small, predictable runtime that can operate on constrained hardware.
- A clear event model for alerts, telemetry, routes, and evidence.
- Reliable offline operation with opportunistic synchronization.
- A documentation system that can grow into one guide per use case.

## Non-Negotiable Constraints

- No dependency on always-on connectivity.
- No requirement for heavyweight orchestration.
- No hidden behavior in the data layer.
- No undocumented UI flows.
- No use-case logic that cannot be explained and maintained by a small team.

## Acceptance Criteria

The project is considered on track when the repository can provide:

- A readable mission statement and release scope.
- A milestone-based implementation plan.
- A technical master document for architecture and conventions.
- An HTML guide that shows how the system is used in real scenarios.
- A path to split documentation into dedicated use-case documents over time.

## Documentation Strategy

- `README.md`
  - Public project overview, milestone planning, and readiness criteria.
- `goal.md`
  - Canonical objective and acceptance criteria.
- `dev.md`
  - Technical master guide for architecture, data contracts, and implementation rules.
- `index.html`
  - Interactive guide and command-center style walkthroughs.
- Future `docs/use-cases/*.md`
  - One file per real deployment scenario.

## Near-Term Delivery Order

1. Stabilize the product narrative and documentation structure.
2. Expand the HTML guide for field operators and maintainers.
3. Define the local data model and persistence rules.
4. Add offline synchronization and evidence handling.
5. Split recurring workflows into dedicated use-case documents.
6. Harden the system for deployment on constrained hardware.

## Definition of Done

This objective is reached when the system can be extended, operated, and documented without requiring a redesign of the core.
