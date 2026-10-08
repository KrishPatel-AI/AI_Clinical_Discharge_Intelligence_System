# STATUS.md

This file exists so that any agent, in any tool, on any day, can pick up
exactly where the last one left off — without you re-explaining the
project. Update the "Where things stand" section every time a phase
finishes or starts. Keep it short and factual: what's actually true, not
what's planned.

If you are starting a brand-new chat/session with no repo access (e.g. a
plain web chat), paste this entire file in first, then say which phase to
work on.

## Where things stand right now
- University Review-I (design & planning) is complete: problem statement,
  objectives, literature review, architecture, and tech stack are all
  approved (see ARCHITECTURE.md).
- Phase 0 is complete: the scaffold, local Python environment, Ollama
  installation/model, FastAPI and Streamlit entry points, ignore rules, and
  CI quality gates are merged to `main` and passing.
- Phase 1 — **requirement update verified complete, 2026-09-23.** Seven
  India-sourced guideline documents (replacing the original MedlinePlus
  set) are stored under `knowledge_base/guidelines/` for asthma, diabetes,
  and high-blood-pressure, each with a `metadata.json` recording source,
  title, URL, retrieval date, diagnosis, extractability, and licensing
  terms. The metadata records licensing constraints honestly rather than
  claiming unrestricted redistribution, which is correct, not a gap.
- Phase 2 is complete: ingestion (`build_index`, `_read_records` in
  `ingest.py`) is idempotent and compatible with the Phase 1 Markdown set;
  covered by `test_ingest.py`.
- Phase 3 — **requirement update verified complete, 2026-09-23.** Genuine
  PDF/DOCX parsing (`PdfReader`, `Document`) in `extract_upload_document`/
  `_extract_text` in `extraction.py`; temperature-0 and retry config in
  `get_ollama_temperature`/`get_llm_validation_retries` in `config.py`;
  golden extraction cases in `extraction_cases.json`, enforced by
  `test_golden_extraction.py`.
- Phase 4 is complete: retrieval/comparison merged via
  `phase-4-rag-retrieval-comparison`, including known-diagnosis and
  no-match tests. Re-validated against the Phase 1 India-sourced documents
  as part of the Phase 1 verification above.
- Phase 5 — **requirement update verified complete, 2026-09-23**, with one
  point to confirm rather than assume: the verification states scoring
  (`_score` in `workflow.py`) is algorithmic, not a second LLM call, which
  would make it inherently deterministic. This is a more specific claim
  than the requirement update asked for (which assumed scoring stayed an
  LLM call, just pinned/temperature-0). ARCHITECTURE.md is not updated to
  reflect "scoring has no LLM call" until that's confirmed directly — see
  the open item below. The `ReviewResponse` schema contract, no-match
  suppression, guideline-passage + source-URL on every suggestion, and
  golden scoring tests (`test_golden_scoring.py`) are confirmed either way.
- Phase 6 — **requirement update verified complete, 2026-09-23, and
  merged to `main`** (verified via `git merge-base --is-ancestor`). The
  "merge is still pending" note below was stale and is now corrected. Live
  per-suggestion `PATCH`, `preview`, and filterable `GET /reviews` exist
  in `discharge.py`; persistence in `persistence.py`/`database.py`;
  contract in `schemas.py`; covered by `test_persistence.py`.
- **Scoring confirmed algorithmic (resolved 2026-10-06):** verified that
  `_score_impl` in `backend/rag/workflow.py` calculates completeness score
  and maps gap suggestions completely programmatically without making any
  LLM call. ARCHITECTURE.md updated accordingly.
- Phase 7 (Structuring & formatting) is verified complete and merged to `main`.
- Phase 8 is verified complete and merged to `main` via PR #15 on 2026-10-07.
  Context Precision (0.919), Faithfulness (1.000), and Answer Relevancy (0.760)
  pass all required floors on GitHub Actions CI. Langfuse tracing and security
  auditing are active and passing.
- Phase 9 is verified complete, 2026-10-07:
  - Schema management replaced ad-hoc startup `ALTER TABLE` in `backend/db.py`
    with versioned Alembic migrations (`alembic.ini`, `alembic/env.py`, and
    `alembic/versions/cc7a5170229d_initial_schema.py`).
  - Ad-hoc column inspection was removed from `backend/db.py` and `get_db()`,
    preventing concurrent connection locks or schema race conditions.
  - `tests/test_migrations.py` tests `alembic upgrade head`, table/column
    existence, downgrade to base, and re-upgrade idempotency.
  - Production Docker setup added in `docker/Dockerfile`, `docker/entrypoint.sh`,
    and `docker-compose.yml` orchestrating FastAPI (non-root `appuser`),
    PostgreSQL 16, Ollama, and persistent vector store volumes.
  - CORS middleware enabled in FastAPI app per AGENTS.md requirement with
    `ALLOWED_ORIGINS` config helper.
  - CI workflow updated to run `alembic upgrade head`, validate Dockerfile
    build, and verify docker-compose syntax on every pull request.
- Phase 10 is verified complete, 2026-10-08:
  - Complete production frontend implemented with Next.js App Router, React,
    TypeScript, and HeroUI as the authoritative design system.
  - Native HeroUI light/dark mode theming without competing token systems.
  - New review upload flow with PDF, DOCX, and TXT client/server validation,
    loading states, and error handling.
  - Review workspace with completeness score, diagnosis display, and
    guideline recommendation cards.
  - Granular per-suggestion review with live PATCH updates and atomic state.
  - Live document comparison showing original discharge summary alongside
    the structured reviewed document (split-view on desktop, tabs on mobile).
  - Synchronized backend preview (`GET /reviews/{id}/preview`) with structured
    content and accepted suggestions, ensuring preview fidelity before export.
  - Export flow supporting PDF, DOCX, and TXT with live preview before commit.
  - Searchable, filterable, sortable, groupable, and paginated review history.
  - Audit trail viewer showing immutable physician decisions.
  - Unit tests covering frontend API client, error normalization, and query params.
  - CI workflow updated with Node.js setup, frontend lint, test, and build steps.
- Active state: **All planned implementation phases (Phases 0 through 10) are complete and verified.**
  Application is operational end-to-end with FastAPI backend, PostgreSQL/SQLite,
  Ollama RAG pipeline, and Next.js + HeroUI frontend. Phase 11 (cloud deployment)
  is deferred as future scope.
- Last updated: 2026-10-08

## Definition of done — applies to every phase below
- Tests exist for its success path and at least one realistic failure
  path, and they pass.
- Lint, type-check, and the security scans (`bandit`, `pip-audit`) are
  clean in CI.
- No emojis were introduced anywhere.
- Any RAG-affecting change (knowledge base, prompts, provider) has the
  Ragas evaluation set re-run, with results compared to the prior
  baseline, and the golden/determinism set (Phase 5) re-run alongside it.
- Any judgment-task LLM call (extraction, comparison, scoring) runs at a
  pinned model version and temperature 0, with schema-validated output
  and bounded retries on validation failure — not just "produces a
  reasonable-looking result."
- ARCHITECTURE.md and this file are updated if anything changed.

## Phase plan
Work exactly one phase at a time. Do not start the next phase until the
current one is merged to `main` and marked done here. Where a phase below
already shows a completion date from earlier work, that history is real
and kept as-is — a "Requirement update" note under a phase means the bar
for that phase has been raised since it was first completed, not that the
original work didn't happen.

- [x] **Phase 0 — Repo scaffold & environment.** Folder structure from
  AGENTS.md, Python virtual environment / requirements file, Ollama
  installed with one model pulled locally, empty FastAPI and Streamlit
  entry points that run, `.gitignore` covering `.env` and local artifacts,
  CI workflow skeleton. Done = both `uvicorn` and `streamlit run` start
  without errors, CI runs green on an empty repo.

- [x] **Phase 1 — Source & structure guideline data.** Evaluate guideline
  sources, pick starting diagnoses, verify usage/reuse terms, save source
  documents under `/knowledge_base/guidelines/<diagnosis-slug>/` with
  metadata (source, URL, date retrieved, licensing terms).
  **Requirement update (2026-09-22), verified complete 2026-09-23:** the
  system is scoped specifically to Indian hospitals and Indian clinical
  practice (see AGENTS.md's Regional scope note — internal sourcing
  constraint, never surfaced in the product). Seven India-sourced
  guideline documents now replace the original MedlinePlus set, under
  `knowledge_base/guidelines/` for asthma, diabetes, and
  high-blood-pressure, each with a `metadata.json` recording source,
  title, URL, retrieval date, diagnosis, extractability, and licensing
  terms. The metadata correctly records licensing constraints rather than
  asserting unrestricted redistribution. ARCHITECTURE.md's "Guideline
  data" section still needs updating to name these actual sources in
  place of the MedlinePlus placeholder text — a documentation sync, not a
  code gap.

- [x] **Phase 2 — Guideline ingestion & indexing.** Chunking/embedding
  script, idempotent and re-runnable, indexing Phase 1's documents into
  FAISS. No requirement update to the script itself — re-run it once
  Phase 1's re-sourcing is complete, and re-verify retrieval returns the
  expected diagnosis for each new document.

- [x] **Phase 3 — Document extraction.** FastAPI endpoint accepting
  PDF/Word/text, validating it, extracting diagnosis, medicines,
  follow-up info, and warning signs via the LLM provider abstraction.
  **Requirement update (2026-09-22), verified complete 2026-09-23:**
  genuine PDF/DOCX parsing confirmed (`PdfReader`, `Document`) in
  `extract_upload_document`/`_extract_text` in `extraction.py`, not a
  placeholder fallback. Temperature-0 and pinned-model config in
  `get_ollama_temperature`/`get_llm_validation_retries` in `config.py`.
  Golden extraction cases in `extraction_cases.json`, enforced by
  `test_golden_extraction.py`. Format-specific parsing tests in
  `test_extraction.py`.

- [x] **Phase 4 — RAG retrieval + comparison.** LangGraph workflow:
  extracted diagnosis -> retrieve matching guideline (or report no
  match) -> compare section-by-section. No new requirement beyond
  re-validating against Phase 1's re-sourced documents once available.

- [x] **Phase 5 — Scoring, explanations & guardrails.** Completeness
  score and suggestions, each citing a specific guideline passage; no
  suggestion without a citation; no-match suppression instead of guessing.
  **Requirement update (2026-09-22), verified complete 2026-09-23:** the
  `ReviewResponse` schema contract (`schemas.py`), no-match suppression,
  guideline-passage + source-URL on every suggestion, and golden scoring
  tests (`test_golden_scoring.py`, `test_workflow.py`) are all confirmed
  in `_compare`/`_score` in `workflow.py`. One point still to confirm, not
  yet settled either way: whether `_score` makes any LLM call at all, or
  is fully programmatic — see the open item in "Where things stand." The
  determinism outcome is verified regardless of which is true; only the
  ARCHITECTURE.md description of *how* it's achieved is pending
  confirmation.

- [x] **Phase 6 — Persistence & audit log.** PostgreSQL schema for users,
  reports, audit logs, via the ORM only. Doctor accept/ignore decisions
  recorded per suggestion with a timestamp. Merged to `main` from
  `phase-6-persistence-audit-log` (verified via
  `git merge-base --is-ancestor`).
  **Requirement update (2026-09-22), verified complete 2026-09-23:** live
  per-suggestion `PATCH /reviews/{id}/suggestions/{suggestion_id}`,
  `GET /reviews/{id}/preview?format=pdf|docx|txt`, and filterable
  `GET /reviews?search=&status=&sort=&group_by=` all implemented in
  `discharge.py`, backed by `persistence.py`/`database.py` and the
  `schemas.py` contract, covered by `test_persistence.py`.

- [x] **Phase 7 — Structuring & formatting.** Verified complete,
  2026-10-03, merged via PR #13. Export-time, layout-only reformatting of
  the discharge document into a consistent structure (e.g. Patient Information,
  Diagnosis, Hospital Course, Medications, Advice, Follow-up), independent
  of the completeness score — runs even when the score is already high or
  when no guideline match exists. The formatter never adds, removes, or
  rewords original clinical content; it reorganizes and labels original
  content, and only includes accepted suggestions under a clearly marked
  "Added on review" section. A content-presence verification step confirms
  every original sentence remains present in the structured output before
  the export is accepted.

- [x] **Phase 8 — Evaluation & monitoring, fully wired.** Verified complete,
  2026-10-06. Langfuse tracing covers every pipeline stage with metadata-only
  instrumentation (stage name, status, latency, IDs — no raw PHI).
  Dependency audit (`pip-audit`) is clean with two documented exceptions in
  `SECURITY_NOTES.md` (`PYSEC-2026-2447`, `PYSEC-2026-3046`). The Ragas
  evaluation was redesigned and verified: Faithfulness evaluates suggestions
  against natural summary text and retrieved guideline passages without
  injected rules (1.000, minimum 0.500), Context Precision evaluates against
  the 5-chunk candidate ranked passage set from FAISS (0.919, minimum 0.500),
  and Answer Relevancy clears its floor (0.504 >= 0.500). Done locally;
  ready for PR and CI run on GitHub Actions.

- [x] **Phase 9 — Containerization, CI & security gates.** Verified complete
  2026-10-07. Dockerfile (`docker/Dockerfile`) with non-root security user,
  smart entrypoint (`docker/entrypoint.sh`), and `docker-compose.yml`
  orchestrating API, PostgreSQL 16, Ollama, and persistent vector store.
  Versioned database migrations implemented via Alembic (`alembic/versions/cc7a5170229d_initial_schema.py`)
  replacing ad-hoc startup `ALTER TABLE` in `backend/db.py`. Migration
  lifecycle tested in `tests/test_migrations.py`. GitHub Actions CI
  workflow validates lint (`ruff`), type checking (`mypy`), migrations
  (`alembic upgrade head`), unit/integration tests, golden determinism
  suite, Ragas evaluation, security scan (`bandit`), dependency audit
  (`pip-audit`), and Docker build/compose configurations on every PR.


- [x] **Phase 10 — Frontend.** Verified complete, 2026-10-08. Built with
  Next.js App Router, React, TypeScript, and HeroUI as the authoritative
  design system. Features responsive split-screen comparison, live
  per-suggestion review updates (`PATCH`), synchronized layout-preserving
  document preview, export generation across PDF/DOCX/TXT formats, and a
  searchable, sortable, filterable, and paginated review history. Unit
  tests cover API contracts and CI runs lint, tests, and build.

- [ ] **Phase 11 — Deployment & cloud-LLM provider-swap validation.**
  Deploy the backend (and, once built, the frontend) to Render or
  Railway, HTTPS only. As part of this phase, actually perform the
  Ollama-to-cloud swap (e.g. to Gemini) by changing only the provider
  environment variable from the LLM provider abstraction — no changes to
  extraction/comparison/scoring code. Re-run the Ragas and golden sets
  against the cloud provider and compare to the Ollama baseline before
  treating the swap as safe. Done = a live URL exists, a full review
  cycle works on it, and the provider-swap comparison is recorded in
  ARCHITECTURE.md. If this swap takes more than a config change, that
  means the Phase 3/5 provider abstraction needs revisiting — not that
  this phase is unusually hard.

Requirement changes go here too: if scope changes mid-project, add a new
phase (or a requirement update to an existing one, as above) rather than
silently expanding a phase that's already "done."

## Decision log
- Ollama chosen as the default LLM runtime, swappable via a provider
  abstraction so a cloud model can be used later without rewriting
  extraction/scoring logic.
- RAG architecture chosen specifically so every suggestion is traceable to
  an actual guideline passage, not a general LLM judgement.
- No real patient data, no live hospital/EHR integration — fixed scope
  boundary for this version.
- 2026-09-20 — Added quality/security/UI/scalability standards and a
  per-phase Definition of Done.
- 2026-09-20 — Split the original "guideline knowledge base" phase into a
  data-sourcing phase (Phase 1) and a technical ingestion phase (Phase 2),
  since no guideline data or RAG background existed yet; added an explicit
  no-match guardrail requirement and a provider-swap validation step in
  the deployment phase.
- 2026-09-20 — Phase 0 marked complete after the scaffold was merged to
  `main` and CI passed; Phase 1 started on a separate branch for guideline
  source evaluation.
- 2026-09-20 — Phase 1 marked complete after three MedlinePlus records were
  retrieved, validated as XML, organized by diagnosis, and documented with
  source and attribution metadata; Phase 2 started for indexing.
- 2026-09-20 — Phase 2 marked complete after the idempotent FAISS index was
  implemented and queried successfully for diabetes, asthma, and high blood
  pressure; Phase 3 started for document extraction.
- 2026-09-20 — Phase 3 marked complete after PDF, DOCX, and TXT validation,
  structured extraction tests, endpoint testing, and a synthetic live Ollama
  provider check; Phase 4 started on the dedicated
  `phase-4-rag-retrieval-comparison` branch.
- 2026-09-20 — Phase 4 marked complete after the retrieval/comparison
  workflow, API endpoint, known-diagnosis tests, and explicit no-match tests
  were merged to `main`; Phase 5 started on the dedicated
  `phase-5-scoring-explanations-guardrails` branch.
- 2026-09-20 — Phase 5 marked complete after deterministic scoring,
  guideline-grounded suggestions, no-match suppression, and a real endpoint
  workflow test were verified on `main`; Phase 6 started on the dedicated
  `phase-6-persistence-audit-log` branch.
- 2026-09-20 — Phase 6 implementation was validated with ORM-backed report
  creation, retrieval, explicit suggestion decisions, timestamped audit
  records, and isolated database integration tests; the phase remains
  pending merge to `main`.
- 2026-09-21 — Re-scoped the system to Indian hospitals and Indian
  clinical guidelines specifically (internal sourcing constraint, never
  surfaced in the product). Identified that reported output inconsistency
  needs a determinism fix (pinned model, temperature 0, schema validation,
  a golden test set), that document import needed verification against
  placeholder fallback, that an export-time structuring stage was
  missing, and that the API needed a granular, live-interaction shape.
  Initially tracked these as a separate "Enhancement pass" (E1-E7) plus a
  separate "Future phases" list (F1-F4) outside the main phase numbering.
- 2026-09-22 — Reverted the E-series/F-series split after Krish flagged
  it as confusing alongside the original Phase 0-10 numbering. All of the
  above updates are now folded directly into the single continuous phase
  plan above, as "Requirement update" notes on Phases 1, 3, 5, and 6 and
  as newly numbered Phases 7-11 (Structuring & formatting; Evaluation &
  monitoring; Containerization & CI; Frontend; Deployment). Real
  completion history for Phases 0-6 (dates, branch names, what was
  actually verified) is preserved unchanged from the prior version of
  this file — a requirement update raises the bar for a phase, it does
  not erase that the original work happened.
- 2026-09-23 — Copilot verified, with specific file/function citations,
  that the requirement updates on Phases 1, 3, 5, and 6 are all met, and
  that the `phase-6-persistence-audit-log` branch is merged to `main`
  (STATUS.md's earlier "merge pending" note was stale). Active phase
  moved to Phase 7. One open item: Phase 5's verification states scoring
  is algorithmic rather than LLM-based, which is more specific than the
  original requirement update assumed — pending a direct one-line
  confirmation before ARCHITECTURE.md's AI-processing layer description
  is changed to match.
- 2026-09-24 — Krish directly confirmed the frontend as finalized:
  Next.js + HeroUI. Updated AGENTS.md and ARCHITECTURE.md to state this
  as decided rather than deferred. The open item above (algorithmic vs.
  LLM-based scoring) remains unresolved — was never actually answered,
  and is being deprioritized as a non-blocking documentation detail
  rather than chased further.
- 2026-09-24 — Phase 8 reopened after being marked complete earlier the
  same day. A more rigorous audit (prompted by Krish explicitly asking
  for zero-gap verification) found the Ragas Faithfulness metric was
  being fed hand-authored extraction evidence alongside the retrieved
  guideline, which meant a passing score didn't prove groundedness in
  the guideline alone. Also found: ARCHITECTURE.md described Langfuse as
  tracing "every prompt/response," which doesn't match the actual
  metadata-only implementation — corrected to state the metadata-only
  design explicitly, as a deliberate privacy decision, not a gap. Also
  flagged: the report table's schema uses manual startup `ALTER TABLE`
  logic, which should become a versioned migration before Phase 9/11 -
  added to Phase 9's scope rather than fixed mid-Phase-8.
- 2026-10-06 — Completed Phase 8 end-to-end. Verified that `_score_impl`
  in `workflow.py` is entirely programmatic (closed open item in
  ARCHITECTURE.md). Redesigned Ragas evaluation so Context Precision
  evaluates real candidate ranking against FAISS top-5 (0.919),
  Faithfulness evaluates suggestions against genuine summary and retrieved
  guideline passage without injected rules (1.000), and Answer Relevancy
  passes (0.504). All golden, unit, lint, and security checks clean.
- 2026-10-07 — Phase 9 completed end-to-end. Alembic versioned migrations
  introduced to replace startup `ALTER TABLE` and inspection queries in
  `backend/db.py`. Multi-stage Dockerfile and Docker Compose orchestration
  added for API, PostgreSQL 16, Ollama, and vector store. CORS enabled
  on FastAPI app. CI workflow updated to run migrations and validate
  Docker build and compose configurations.
- 2026-10-08 — Phase 10 completed end-to-end. Production Next.js App Router
  frontend implemented with HeroUI component and theme system. Harmonized
  `preview_review` endpoint to return structured document representation with
  accepted suggestions. Added client-side tests, CI workflow updates, and
  full interaction flows for upload, review, preview, export, and history.
- *(add new entries here as real decisions get made — one line, with the
  reason)*