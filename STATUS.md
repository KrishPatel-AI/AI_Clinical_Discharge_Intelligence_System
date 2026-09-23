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
- Phase 1 is complete against the updated requirement: seven preserved,
  India-sourced PDFs with regenerated Markdown and per-document metadata are
  stored under `knowledge_base/guidelines/` for asthma, diabetes, and high
  blood pressure. Metadata records source, title, URL, retrieval date,
  diagnosis, extractability, and known reuse/licensing terms.
- Phase 2 is complete against the updated source set: the existing FAISS
  pipeline now reads the verified Markdown files with the minimum compatible
  ingestion change. The verified index contains 1,100 unique chunks across
  all three diagnoses; source filenames and URLs are preserved in metadata;
  repeated indexing remains idempotent; and all relevant tests pass.
- Phase 3 is complete against the updated requirement: PDF, DOCX, and TXT
  uploads use genuine text extraction; Ollama extraction sends temperature
  0, uses the configured model tag, validates the Pydantic schema, and
  retries invalid output a bounded number of times before failing. Fixed
  golden extraction cases are stored under `tests/golden/` and discovered by
  pytest. The focused extraction suite and full project suite pass.
- Phase 4 is complete: the retrieval and comparison workflow was merged to
  `main` through `phase-4-rag-retrieval-comparison`, including known-
  diagnosis and no-match tests. It was re-validated against the completed
  Phase 1/2 Markdown index; known-diagnosis and no-match behavior remain
  covered by the passing test suite.
- Phase 5 is complete under its original requirements: deterministic
  scoring, guideline-grounded suggestions, no-match suppression, and a
  real endpoint workflow test were verified on `main`. Requirement update
  below adds explicit temperature/model-pinning and a golden test set —
  "deterministic" here should be confirmed against that stricter bar, not
  assumed from the phase's original name.
- Phase 6 — implementation and validation complete on
  `phase-6-persistence-audit-log` (ORM-backed report creation, retrieval,
  explicit suggestion decisions, timestamped audit records, isolated
  database integration tests, and the updated live review API). **Merge is
  still pending review.**
- Active work: Phase 6 is complete and awaiting review/merge. Phase 7 is the
  next backend phase, but must not start until Phase 6 is approved and merged.
- Last updated: 2026-09-23

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
  **Requirement update (2026-09-22):** completed. The three original
  MedlinePlus records were replaced by seven preserved India-sourced PDFs
  and regenerated Markdown files covering the same three diagnosis folders.
  Metadata records source, title, URL, retrieval date, diagnosis,
  extractability, and known licensing terms. The asthma and type 1 diabetes
  repaired conversions were re-verified before indexing.

- [x] **Phase 2 — Guideline ingestion & indexing.** Chunking/embedding
  script, idempotent and re-runnable, indexing Phase 1's documents into
  FAISS. The minimum Markdown compatibility change was implemented without
  changing the existing chunking, embedding, FAISS, or no-match design.
  The final index contains 1,100 unique chunks from seven documents across
  asthma, diabetes, and high blood pressure, and repeated indexing does not
  create duplicates. Retrieval and source traceability were re-verified.

- [x] **Phase 3 — Document extraction.** FastAPI endpoint accepting
  PDF/Word/text, validating it, extracting diagnosis, medicines,
  follow-up info, and warning signs via the LLM provider abstraction.
  **Requirement update (2026-09-22):** completed. PDF and DOCX parsing use
  `pypdf` and `python-docx`, with direct tests for both formats. Ollama
  extraction sends temperature 0, uses the configured model tag, validates
  `DischargeExtraction`, and retries invalid output twice after the initial
  attempt before returning an explicit error. `/tests/golden` contains fixed
  input/expected-output cases and passes in the project test suite. Langfuse
  raw input/output tracing and broader Ragas evaluation remain Phase 8 work.

- [x] **Phase 4 — RAG retrieval + comparison.** LangGraph workflow:
  extracted diagnosis -> retrieve matching guideline (or report no
  match) -> compare section-by-section. Revalidated against the completed
  1,100-chunk Markdown index for asthma, diabetes, hypertension, and an
  unrelated no-match diagnosis. A local candidate-selection correction now
  prefers diagnosis-aligned results among the existing retrieved candidates;
  no new retrieval system or architecture was introduced.

- [x] **Phase 5 — Scoring, explanations & guardrails.** Completeness
  score and suggestions, each citing a specific guideline passage; no
  suggestion without a citation; no-match suppression instead of guessing.
  **Requirement update (2026-09-22):** completed. The current scoring stage
  is algorithmic rather than an LLM call, so there is no scoring sampling
  temperature or provider retry path to configure. The resulting
  `ReviewResponse` is schema-validated, every suggestion retains its cited
  passage and source URL, no-match suppression remains explicit, and scoring
  golden cases prove byte-identical JSON, score, and suggestion sections on
  repeated runs.

- [x] **Phase 6 — Persistence & audit log.** PostgreSQL schema for users,
  reports, audit logs, via the ORM only. Doctor accept/ignore decisions
  recorded per suggestion with a timestamp. Implementation and validation
  are complete on `phase-6-persistence-audit-log`; the updated API
  requirement is complete. **Requirement update (2026-09-22):** add
  the following endpoints, needed so any future frontend can update live
  rather than only submit-and-reload (see AGENTS.md's "API design for
  live interaction" for full detail):
  `PATCH /reviews/{id}/suggestions/{suggestion_id}` (set one suggestion's
  status without resubmitting the whole case),
  `GET /reviews/{id}/preview?format=pdf|docx|txt` (preview the current
  final document without marking it exported), and
  `GET /reviews?search=&status=&sort=&group_by=` (server-side search/
  filter/sort/group for history, rather than the frontend fetching
  everything). New done criteria = a full review cycle is retrievable
  from the database afterward (original criterion, unchanged), and each
  new endpoint above is verified directly against a real persisted test case.
  Phase 6 stores sanitized source text for preview, maps API `rejected` to
  the existing audit-compatible `ignored` decision, and includes a
  non-destructive migration for existing databases.

- [ ] **Phase 7 — Structuring & formatting.** New phase, added
  2026-09-22. Export-time, layout-only reformatting of the discharge
  document into a consistent structure (e.g. Patient Information,
  Diagnosis, Hospital Course, Medications, Advice, Follow-up), independent
  of the completeness score — runs even when the score is already high or
  when no guideline match exists. Must never add, remove, or reword
  clinical content; only reorganize and label it. Include a verification
  step confirming every sentence of the original document is still
  present in the structured output. Done = a high-scoring document and a
  no-match document both produce a cleanly structured export with zero
  content loss, confirmed by the verification step, not just visual
  inspection.

- [ ] **Phase 8 — Evaluation & monitoring, fully wired.** Langfuse tracing
  across every layer (extraction, retrieval, comparison, scoring,
  formatting) — not only the pieces already traced. The Ragas evaluation
  set and the golden/determinism set (Phases 3 and 5) become a permanent,
  scheduled part of CI rather than a manually-run check. Done = a Langfuse
  trace exists for a real run touching every layer, and both evaluation
  sets run automatically on a schedule or on every merge to `main`.

- [ ] **Phase 9 — Containerization, CI & security gates.** Dockerfile(s) +
  docker-compose for the full backend stack (API, vector store, database,
  Ollama); GitHub Actions running tests, lint, type-check, `bandit`,
  `pip-audit`, and both evaluation sets on every PR. Done = `docker
  compose up` runs the whole backend from a clean checkout, CI fully
  green end-to-end.

- [ ] **Phase 10 — Frontend.** On hold until its phase is reached. The
  finalized frontend is Next.js + HeroUI. It consumes the API exactly as
  specified in AGENTS.md's "API design for live interaction" section (see
  Phase 6's requirement update) — no backend changes should be needed to
  support it. Phases 8 and 9 do not depend on this decision and can proceed
  first if useful.

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
- 2026-09-23 — Completed the Phase 1/2 requirement update: replaced the
  MedlinePlus/XML knowledge base with seven preserved Indian-source PDFs and
  Markdown conversions, added the minimum Markdown ingestion compatibility,
  re-indexed 1,100 unique chunks, and verified 14 tests pass.
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
- 2026-09-23 — Finalized Next.js with HeroUI as the Phase 10 frontend;
  frontend implementation remains deferred until the backend prerequisites
  and Phase 10 scope are reached.
- 2026-09-23 — Completed Phase 6's live review API: typed `/reviews`
  creation/retrieval, per-suggestion PATCH status, non-exporting preview,
  server-side history filtering/grouping, source-text persistence, audit
  logging, existing-database migration, and real-case endpoint tests.
- *(add new entries here as real decisions get made — one line, with the
  reason)*