# AI Clinical Discharge Intelligence System

An AI-powered second reviewer for hospital discharge summaries. It reads a
discharge summary, retrieves the matching clinical guideline for the
diagnosis, and produces a completeness score plus guideline-grounded
suggestions for missing information (follow-up dates, medicines, warning
signs, etc.). The doctor reviews and approves or ignores every suggestion —
the AI never edits the discharge document itself.

B.Tech Engineering Project – II, Semester VII, AY 2026-27, Group 5-B.

## Status
Build not started yet — see [STATUS.md](./STATUS.md) for the current phase
and the full phase plan.

## Documentation map
- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design: the five layers, the
  end-to-end flow, and the key technical decisions and why.
- [STATUS.md](./STATUS.md) — what's built, what's next, and the decision
  log. Read this before starting any work session.
- [AGENTS.md](./AGENTS.md) — instructions for any AI coding agent working in
  this repo: stack, folder structure, commands, conventions, boundaries.

## How to run
Not yet available — will be filled in once Phase 0 (repo scaffold) is
complete. See STATUS.md.

## Scope
No real patient data is used or stored. The system does not connect to any
live hospital or EHR system. Guideline coverage starts with a small,
curated set of common diagnoses and expands over time.
