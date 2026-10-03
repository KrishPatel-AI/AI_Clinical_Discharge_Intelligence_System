# AI Clinical Discharge Intelligence System

An AI-powered second reviewer for hospital discharge summaries. It reads a
discharge summary, retrieves the matching clinical guideline for the
diagnosis, and produces a completeness score plus guideline-grounded
suggestions for missing information (follow-up dates, medicines, warning
signs, etc.). The doctor reviews and approves or ignores every suggestion -
the AI never edits the discharge document itself.

B.Tech Engineering Project - II, Semester VII, AY 2026-27, Group 5-B.

## Status
Phases 0-7 are complete against the verified current requirements. The
initial Indian-source knowledge base covers asthma, diabetes, and high blood
pressure: seven preserved PDFs, seven Markdown conversions, and 1,100 unique
FAISS chunks with source traceability. Phase 4 is revalidated against that
knowledge base, and Phase 5 uses deterministic algorithmic scoring with
golden tests. Phase 6 is complete: the typed `/reviews` API supports live
per-suggestion status updates, non-exporting previews, and server-side
history search and grouping. Phase 7 is complete: export-time layout-only
structuring is implemented, with content-presence verification to ensure the
original discharge content is not dropped during export formatting. The
frontend decision is finalized as Next.js with HeroUI, but frontend
implementation is deferred to Phase 10. Phases 8-9 are the next backend
work items, followed by Phase 10 frontend and Phase 11 deployment.
See [STATUS.md](./STATUS.md) for the current phase and the full plan.

## Documentation map
- [ARCHITECTURE.md](./ARCHITECTURE.md) - system design: the layers, the
  end-to-end flow, and the key technical decisions and why.
- [STATUS.md](./STATUS.md) - what's built, what's next, and the decision
  log. Read this before starting any work session.
- [AGENTS.md](./AGENTS.md) - instructions for any AI coding agent working in
  this repo: stack, folder structure, commands, conventions, boundaries,
  and the Phase 10 frontend design brief (recorded now so it isn't lost
  before that phase starts).

## How to run
See STATUS.md for current setup instructions as the backend phases
progress; this section should be filled in with the real run commands
once Phase 9 (containerization) is complete.

## Scope
No real patient data is used or stored. The system does not connect to any
live hospital or EHR system. Guideline coverage starts with a small,
curated set of common diagnoses and expands over time.