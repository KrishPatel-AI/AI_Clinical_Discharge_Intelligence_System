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
| Presentation | Next.js + HeroUI (Phase 10) | Upload, inline review, live preview, history |
| API | FastAPI | Receives uploads, exposes granular per-suggestion and preview endpoints, triggers the pipeline |
| AI processing | LangChain + LangGraph + LLM provider abstraction | Extracts, retrieves, compares, scores, generates explanations |
| Formatting | Independent module, export-time | Layout-only structuring of the final document |
| Knowledge | ChromaDB / FAISS | Stores and semantically searches the indexed guideline documents |
| Data | PostgreSQL | Stores users, generated reports, audit logs, dashboard metrics |
| Monitoring (cross-cutting) | Langfuse, Ragas | Traces every prompt/response; evaluates retrieval quality, faithfulness, answer relevance, context precision |

## Guideline data — Phase 1 and Phase 2 complete
The initial knowledge base is sourced for Indian clinical practice and is
stored under `knowledge_base/guidelines/<diagnosis-slug>/`. It contains
seven preserved source PDFs and their regenerated Markdown representations
across three diagnosis folders: asthma, diabetes, and high blood pressure.
Each document has metadata recording its title, source, URL, retrieval date,
diagnosis, extractability, and known reuse/licensing terms.

The currently indexed sources are:
- ICMR Standard Treatment Workflow for asthma.
- Lung India bronchial asthma recommendations.
- ICMR type 1 diabetes guidelines.
- ICMR type 2 diabetes guidelines and Standard Treatment Workflow.
- ICMR Standard Treatment Workflow for hypertension in adults.
- Ministry of Health and Family Welfare hypertension guideline for adults in
  India.

The Markdown ingestion path preserves the diagnosis folder, source filename,
source URL, and chunk number in FAISS metadata. The existing fixed-size
chunking, hashing-based embeddings, FAISS index, idempotent indexing, and
no-match behavior remain unchanged. The current verified index contains
1,100 unique chunks, all with source URLs. Licensing metadata records where
permission must still be confirmed; indexing does not imply permission to
redistribute the source documents.

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

## Frontend framework — finalized for Phase 10
Streamlit was the original choice for speed of iteration. The frontend is
now finalized as Next.js with HeroUI, a free, open-source React component
library built on Tailwind CSS with light/dark theming. This choice supports
the required inline review, live split-screen synchronization, searchable
history, and export preview without coupling presentation code to backend
processing.

This decision does not affect Phases 1-6: FastAPI already exposes a
decoupled JSON API (see the API design section in AGENTS.md), so the
frontend is isolated from backend logic. Before Phase 10, the backend must
keep typed Pydantic responses, configurable CORS, and the granular
per-suggestion, preview, export, and history endpoints. Do not scaffold the
Next.js/HeroUI frontend before Phase 10.

## Key decisions and why
- **Ollama as the default LLM runtime, swappable by design, temperature
  pinned to 0** — avoids per-request cost and rate limits during
  development; determinism is required because doctors need consistent,
  explainable output, not creative variation.
- **RAG over free-generation** — every suggestion must be traceable to an
  actual guideline passage.
- **Algorithmic scoring for the current phase** — completeness scoring and
  suggestion creation operate on validated comparison results instead of a
  second LLM call. This removes scoring sampling variance while preserving
  the fixed `ReviewResponse` contract and cited evidence requirement.
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
- **Live review API before frontend work** — Phase 6 persists the sanitized
  source text and exposes typed create, retrieve, per-suggestion status,
  preview, and history routes under `/reviews`. Preview does not mark a case
  exported; document structuring and actual file export remain Phase 7.

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
  kept current.
- **UI/UX (Phase 10, not yet built):** minimalist, modern, dashboard-style,
  free of the generic "AI tool" look, with both light and dark mode
  required regardless of framework — full detail in AGENTS.md's
  "Phase 10 design brief," kept there rather than duplicated here.

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
- 2026-09-23 — Completed the updated Phase 1 and Phase 2 requirements:
  replaced the original MedlinePlus/XML knowledge base with seven
  India-sourced PDF/Markdown document pairs, recorded per-document
  provenance and licensing status, added minimal Markdown ingestion support,
  and verified an idempotent 1,100-chunk FAISS index across three diagnoses.
- 2026-09-23 — Finalized Next.js with HeroUI as the Phase 10 frontend;
  backend phases remain framework-independent and must preserve typed API
  contracts, configurable CORS, and granular review/preview/history routes.
- 2026-09-23 — Completed the Phase 3 extraction requirement update with
  genuine PDF/DOCX parsing tests, temperature-zero Ollama requests, bounded
  schema-validation retries, and fixed golden extraction cases.
- 2026-09-23 — Revalidated Phase 4 against the Markdown knowledge base and
  corrected candidate selection so retrieved diagnosis metadata aligns with
  the requested diagnosis without introducing a new retrieval system.
- 2026-09-23 — Completed the Phase 5 scoring requirement update using the
  existing deterministic algorithmic scorer, schema validation, grounded
  citations, no-match suppression, and repeated-run scoring golden cases.