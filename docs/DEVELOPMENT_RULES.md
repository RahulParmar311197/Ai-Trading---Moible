# Development Rules

## Mandatory pre-flight

Before starting any new implementation:

- Read `AI_TRADING_PLATFORM_BLUEPRINT.md`.
- Read `PROJECT_STATUS.md`.
- Inspect the existing repository implementation.
- Identify the next unchecked item; do not skip ahead without a reason.

## Mandatory post-flight

After every meaningful implementation milestone:

- Run the relevant tests/validation.
- Update `PROJECT_STATUS.md`.
- Record files changed and what remains pending.
- Re-check the repository state.
- Only then begin the next milestone.

## Source of truth

`AI_TRADING_PLATFORM_BLUEPRINT.md` is the repository-level implementation reference. The detailed uploaded blueprint is authoritative for requirements not reproduced in the repository copy.

## Trading safety

Never enable live or autonomous execution before the safety gates in the blueprint and status tracker are satisfied. AI output is advisory/structured input; deterministic validation, risk controls, and execution controls remain authoritative.
