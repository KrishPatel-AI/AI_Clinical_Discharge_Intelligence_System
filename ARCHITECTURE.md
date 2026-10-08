# ARCHITECTURE.md

This is the current system design. It reflects what has actually been
built or approved — not aspirations. Update it the moment a real
architectural decision is made or changed; append to the Revision Log
below.

## What "RAG" means in this project, in plain terms
Retrieval-Augmented Generation: instead of asking the AI model to answer
from what it already "knows" (which it might get wrong or make up), the
system first retrieves the actual, specific guideline document relevant to
the diagnosis from a searchable store, then asks the model to compare the
discharge summary against that retrieved text. Every suggestion is
therefore anchored to a real document, not to the model's general
knowledge. If no relevant guideline can be retrieved, the system says so
instead of guessing.

## System flow (what happens to one discharge summary)
1. **Import** — doctor uploads a discharge summary (PDF, Word, or plain
   text). The file is genuinely parsed into text, not placeholder-
   substituted (see Non-functional requirements).
2. **Extract** — the AI extracts diagnosis, medicines, follow-up
   requirements, warning signs, and other key clinical fields, as
   structured blocks anchored to positions in the document.
3. **Retrieve** — the matching guideline is fetched from the vector
   store, based on the identified diagnosis. If none matches confidently,
   the system reports that instead of proceeding.
4. **Compare** — the extracted summary is compared against the retrieved
   guideline, section by section.
5. **Score** — a completeness score and a list of gaps are generated,
   each one explained and tied to the specific guideline passage it's
   based on.
6. **Review** — the doctor accepts or ignores each suggestion
   individually, one decision at a time (see API design below). Nothing
   is applied automatically.
7. **Structure & format (export-time)** — independent of the score,
   the document is reorganized into a consistent, labeled structure
   (layout only, no content changes) as part of producing the export.
8. **Export** — the doctor previews, then downloads, the final reviewed
   and structured document as PDF, DOCX, or TXT. A complete audit record
   is saved: timestamp, completeness score, every suggestion generated,
   every doctor decision, and the export event itself.

## Layers

| Layer | Technology | Responsibility |
|---|---|---|
| Presentation | Next.js + HeroUI | Upload, inline review, live preview, history |
| API | FastAPI | Receives uploads, exposes granular per-suggestion and preview endpoints, triggers the pipeline |
| AI processing | LangChain + LangGraph + LLM provider abstraction | Extracts structured fields via LLM, retrieves via FAISS, compares sections, and scores completeness algorithmically |
| Formatting | Independent module, export-time | Layout-only structuring of the final document |
| Knowledge | ChromaDB / FAISS | Stores and semantically searches the indexed guideline documents |
| Data | PostgreSQL | Stores users, generated reports, audit logs, dashboard metrics |
| Monitoring (cross-cutting) | Langfuse, Ragas | Traces operation metadata (stage, status, latency, trace/observation IDs) across every layer — never raw clinical text or PHI; evaluates retrieval quality, faithfulness, answer relevance, context precision |

## Guideline data — status: sourced (verified 2026-09-23)
This system is scoped specifically for Indian hospitals and Indian
clinical practice (internal design constraint — see AGENTS.md's Regional
scope note; this is never surfaced to the doctor as a claim or label).
Seven India-sourced guideline documents are ingested, covering asthma,
diabetes, and high-blood-pressure, replacing the earlier MedlinePlus
placeholder set. The original candidates evaluated were ICMR (Indian
Council of Medical Research, icmr.gov.in) Standard Treatment Guidelines
and National Health Mission / NHSRC adapted Standard Treatment Guidelines.
The exact per-document source, title, retrieval date, and licensing terms
are not duplicated here — they're recorded per-diagnosis in
`knowledge_base/guidelines/<diagnosis-slug>/metadata.json`, which is the
authoritative record and should be checked directly rather than assumed
from this summary. ICMR publications in particular carry a notice
requiring permission for reproduction or distribution; the metadata
correctly records licensing constraints rather than asserting
unrestricted redistribution is allowed.

## LLM provider strategy
- Development and initial deployment run on Ollama (local), with a pinned
  model version (not a "latest" alias) and sampling temperature set to 0
  for extraction/comparison/scoring, to make behavior repeatable.
- All LLM calls go through one internal provider interface (see
  AGENTS.md) so switching to a cloud model later is a configuration
  change. The extraction/scoring output schema is fixed regardless of
  provider.
- Before treating a provider switch as safe, re-run the Ragas evaluation
  set and the golden/determinism test set, and compare against the
  Ollama baseline.

## Frontend framework — implemented: Next.js + HeroUI
Built and verified in Phase 10. Next.js 15 (App Router, React 19, TypeScript)
with HeroUI (accessible React component library built on Tailwind CSS, with
native light/dark theming) provides fine-grained control over layout,
inline review interactions, synchronized split-view document comparison,
and live export preview.

The frontend operates decoupled from backend business logic, consuming the
granular FastAPI JSON REST API (`POST /reviews`, `GET /reviews/{id}`,
`PATCH /reviews/{id}/suggestions/{suggestion_id}`, `GET /reviews/{id}/preview`,
`POST /reviews/{id}/export`, and `GET /reviews`).

## Key decisions and why
- **Langfuse traces metadata only, never raw clinical text.** Every
  pipeline stage (extraction, retrieval, comparison, scoring,
  structuring, verification, export) is instrumented, but what's sent to
  Langfuse is stage name, status, latency, and trace/observation IDs —
  not the discharge summary content or any extracted clinical field. This
  is a deliberate application of the no-PHI-leaves-the-boundary rule to
  the monitoring layer specifically, not an oversight to be "fixed" by
  sending more detail later.
- **Ollama as the default LLM runtime, swappable by design, temperature
  pinned to 0** — avoids per-request cost and rate limits during
  development; determinism is required because doctors need consistent,
  explainable output, not creative variation.
- **RAG over free-generation** — every suggestion must be traceable to an
  actual guideline passage.
- **India-specific guideline sourcing** — the system is built for Indian
  hospitals and Indian clinical practice; this shapes data sourcing only
  and is never surfaced as a claim in the product itself.
- **Structuring/formatting is a separate, layout-only stage from
  scoring** — conflating "reformat the document" with "suggest clinical
  content" would risk the system quietly changing meaning under the guise
  of tidying layout, which is not acceptable for a clinical document.
- **No live hospital/EHR integration, no real patient data** — explicit
  scope boundary for this version.
- **Doctor-in-the-loop, no auto-apply** — the AI is a second reviewer,
  never an editor of the discharge document itself.
- **Stateless API + externalized state** — no structural blocker to
  scaling later.
- **Scoring is purely algorithmic, not an LLM call** — completeness score
  is calculated programmatically (100 * matched / compared) and suggestions
  are mapped directly from identified section gaps with guideline citations.
  This eliminates variance and makes scoring deterministic by construction.

## Non-functional requirements
Targets the implementation is expected to meet — see AGENTS.md for the
concrete checklist behind each one.
- **Correctness:** tests for the success path and at least one realistic
  failure path on every feature; CI blocks merging on a red run.
- **Determinism:** temperature-0 LLM calls for judgment tasks, pinned
  model versions, schema-validated structured output with bounded
  retries, and a golden test set that must stay stable across runs.
- **Groundedness (RAG-specific):** no suggestion without a cited guideline
  passage; an explicit "no matching guideline" state when retrieval
  confidence is too low; Ragas evaluation re-run on any knowledge base,
  prompt, or provider change.
- **Import fidelity:** PDF, DOCX, and TXT are genuinely parsed, not
  placeholder-substituted, with explicit errors on unparseable files.
- **Structuring fidelity:** export-time reformatting never adds, removes,
  or rewords clinical content — verified by a content-presence check, not
  just assumed.
- **Security:** addressed against the OWASP Top 10 categories relevant to
  this system, using free/open-source scanning (`bandit`, `pip-audit`) in
  CI. No system is "fully secure" — this document tracks what is actually
  covered.
- **Scalability:** stateless API layer, externalized session/history
  state, config-driven service connections.
- **API design for live interaction:** granular per-suggestion endpoints
  and a preview endpoint, so any future frontend can update in real time
  without a full resubmission (see AGENTS.md for the endpoint list).
- **Maintainability:** one approved backend stack, one folder layout,
  guidelines added/changed by folder — not code — changes, this document
  kept current. Schema evolutions are handled deterministically via
  Alembic versioned migrations (`alembic/versions/`), eliminating startup
  locks or concurrency hazards across multiple container instances.
- **UI/UX (Phase 10):** Production frontend implemented in Next.js App
  Router with React, TypeScript, and HeroUI as the authoritative UI/design
  system source of truth. Built with native light and dark modes, live
  per-suggestion review interaction via `PATCH`, live structured document
  comparison, preview-before-download (`GET /reviews/{id}/preview`),
  export generation (`POST /reviews/{id}/export`), and comprehensive
  history search, filtering, sorting, grouping, and pagination.

## Out of scope for the current build (see STATUS.md for future-phase items)
- EHR integration / automatic patient record loading
- Department-specific guideline sets beyond the initial coverage
- Medicine conflict detection
- Voice input
- Regional language (Hindi, Gujarati, etc.) input/output — noted as a
  plausible future direction given the system's Indian focus, not yet
  scoped

## Revision log
- 2026-09-20 — Added Non-functional requirements section.
- 2026-09-20 — Added the RAG plain-language explainer, guideline data
  sourcing status (not yet sourced — candidates listed), LLM provider
  strategy, and the Streamlit responsiveness trade-off.
- 2026-09-21 — Re-scoped guideline sourcing to India-specific sources
  (ICMR, NHM/NHSRC) in place of the earlier US-centric candidate, per
  Krish's explicit requirement that the system be built for Indian
  hospitals and clinical practice. Added determinism as a first-class
  non-functional requirement in response to reported inconsistent
  output. Added the structuring/formatting pipeline stage, the import-
  fidelity requirement for real PDF/DOCX parsing, the granular API
  design for live interaction, and the deferred frontend-framework note
  (Next.js + HeroUI under consideration, not yet decided).
- 2026-09-23 — Corrected stale phase references left over from a
  since-reverted "Enhancement pass" numbering scheme (see STATUS.md's
  decision log); frontend is Phase 10 throughout this document now, not
  Phase 7. Added a UI/UX non-functional requirement line pointing to
  AGENTS.md's new Phase 10 design brief, which records Krish's frontend
  requirements (minimalist/dashboard style, Claude-app-inspired restraint
  without copying it, mandatory light and dark mode, live split-screen
  and export preview backed by the API already specified) ahead of time
  so they aren't lost before that phase starts.
- 2026-09-23 — Updated "Guideline data" from "not yet sourced" to
  "sourced" after Copilot verified seven India-sourced documents exist
  with per-diagnosis metadata (see STATUS.md's Phase 1 entry for the
  verification evidence). Did not update the AI-processing layer's
  description of scoring, despite a verification report suggesting
  scoring may be fully algorithmic rather than LLM-based — that specific
  claim is logged as an open item in STATUS.md pending a direct
  one-line confirmation, not assumed from a paraphrase.
- 2026-09-24 — Finalized the frontend section as Next.js + HeroUI per
  Krish's direct confirmation (previously stated as deferred). Corrected
  the Langfuse description from "traces every prompt/response" to the
  actual metadata-only behavior, and recorded it as a deliberate Key
  Decision rather than leaving the privacy boundary implicit. Flagged
  the manual `ALTER TABLE` schema logic in `db.py` as a concurrency risk
  to resolve via a migration tool in Phase 9, not Phase 8.
- 2026-10-06 — Confirmed directly that scoring in `backend/rag/workflow.py`
  is entirely algorithmic and programmatic (no second LLM call). Updated
  the AI processing layer description and Key Decisions accordingly.
- 2026-10-07 — Phase 9 completed: replaced ad-hoc startup schema mutations in
  `backend/db.py` with versioned Alembic migrations. Added containerization
  specs (`docker/Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml`)
  orchestrating API, PostgreSQL 16, Ollama, and vector store volumes. Enabled
  CORS on FastAPI app with configurable origins.
- 2026-10-08 — Phase 10 completed: built production Next.js + HeroUI frontend
  with responsive App Router architecture, upload workflow with validation,
  live suggestion decision review, live document synchronization, export
  format preview and download, full history search/filter/sort/pagination,
  and native HeroUI light/dark theming. Synchronized preview endpoint with
  authoritative reviewed document structuring.