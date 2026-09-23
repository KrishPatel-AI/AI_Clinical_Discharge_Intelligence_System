# AGENTS.md

## Project
AI Clinical Discharge Intelligence System — a RAG-based tool that reads a
hospital discharge summary, retrieves the matching clinical guideline for
the diagnosis, and produces a completeness score plus guideline-grounded
suggestions for the doctor to review. The AI never edits the discharge
document. Every suggestion is read-only until a doctor explicitly accepts
or ignores it, and that decision is written to an audit log.

Read ARCHITECTURE.md and STATUS.md before doing anything else. STATUS.md
tells you which phase or enhancement task is active right now — work on
that item only, unless told otherwise.

Krish (the project owner) has no prior RAG experience. Do not assume
familiarity with RAG concepts — explain in plain language when it matters.

## Regional scope (internal — do not surface in any UI, document, or output)
This system is built for Indian hospitals, Indian patients, and Indian
clinical guidelines specifically. Every data-sourcing, terminology, and
guideline decision should default to Indian sources and Indian clinical
context (see the Guideline knowledge base section below) rather than
international ones, unless nothing suitable exists. This is a design
constraint for you as the implementer, not a claim, label, or marketing
point the system itself should ever state out loud — never add "India" or
"Indian" branding, disclaimers, or callouts to the UI, exported documents,
or user-facing text. The doctor should simply experience a system that
happens to be accurate for the cases they actually see.

## Approved stack — do not change without flagging it first
- Backend: Python, FastAPI
- Frontend: Next.js + HeroUI, finalized for Phase 10
- AI orchestration: LangChain + LangGraph
- LLM runtime: Ollama, local, for development and initial deployment
- Vector store: ChromaDB or FAISS (guideline knowledge base)
- Relational store: PostgreSQL (users, reports, audit logs, dashboard metrics)
- Observability: Langfuse (tracing every prompt/response/latency/error),
  Ragas (RAG quality evaluation)
- Containerization / CI: Docker, GitHub Actions
- Deployment target: Render or Railway

## Frontend framework decision — Next.js + HeroUI (Phase 10)
The frontend is finalized as Next.js with HeroUI (React and Tailwind-based,
free and open source, with light/dark theming). This is a Phase 10 decision
only: do not scaffold or modify frontend code while backend phases are
active. FastAPI remains a decoupled JSON API, so the frontend can consume it
without changing backend business logic. What earlier phases must do to keep
that integration low-risk:
- Keep all API responses as typed Pydantic models (already required).
- Enable CORS on the FastAPI app, configurable by allowed-origin list via
  environment variable, even though nothing depends on it yet.
- Follow the granular endpoint shape in the "API design for live
  interaction" section below — a live-updating frontend needs per-suggestion
  endpoints, not just a single upload-and-return call.
Do not scaffold the Next.js/HeroUI frontend before Phase 10.

## Phase 10 design brief (reference only — do not act on this before Phase 10)
Recorded now, ahead of time, so these requirements aren't lost or
re-derived from scratch once the frontend framework is actually chosen.
None of this authorizes starting frontend work early.
- **Visual direction:** noise-free, minimalist, and modern — a dashboard
  feel, not a form-heavy admin panel. Krish has specifically pointed to
  the Claude app's UI/UX as a reference for the *quality bar and
  restraint* to aim for (calm, uncluttered, confident use of whitespace)
  — this means taking inspiration from that level of polish, not copying
  its layout, components, or visual identity.
- **Avoid the generic "AI tool" look.** Do not default to the templated
  card-grid-plus-gradient aesthetic that most AI-generated UIs converge
  on. The result should read as a deliberately designed, MNC-grade
  healthcare product, not a hackathon demo or a copy of another AI tool's
  interface.
- **Balance, explicitly:** minimalist does not mean sparse to the point of
  being unclear. A doctor must always be able to tell what the system
  found, what it's suggesting, what's pending, what they accepted, and
  what they ignored, at a glance. If simplifying a screen would make any
  of that ambiguous, that screen is too simple, not appropriately minimal.
- **Wording:** plain, simple, clinical-but-approachable language
  throughout the interface — no jargon-for-its-own-sake, no marketing
  copy, no unexplained abbreviations.
- **Navigation:** doctors should be able to reach any part of the system
  in a small, predictable number of steps, using whatever routing/
  navigation conventions are standard for the chosen framework at the
  time (e.g. Next.js App Router conventions, if that's the eventual
  choice) rather than a custom-invented pattern.
- **Dark mode and light mode are both required**, regardless of which
  frontend framework is ultimately chosen — this is a product requirement,
  not something contingent on HeroUI specifically.
- **Live interaction, backed by the API already specified below:** the
  original document and the doctor-edited final document shown side by
  side, updating live as the doctor accepts or ignores each suggestion
  (via the granular `PATCH` endpoint — no full-page reload), and a live
  preview of the export output before the doctor commits to downloading
  it (via the `preview` endpoint).
- **History** should be genuinely searchable, filterable, categorizable,
  and groupable in the UI, backed directly by the `GET /reviews` query
  parameters already specified below — the UI work here is presentation,
  the backend capability already exists once Phase 6's update is merged.
- A working reference build of these interaction patterns (inline
  suggestion review, live split-screen sync, format-switchable export)
  already exists from earlier exploratory work in Streamlit and can be
  used as a starting reference for the *interaction design*, even though
  its specific implementation (Streamlit) may not be the final framework.

## LLM provider abstraction (required — this is how Ollama-to-cloud stays safe)
- All LLM calls go through a single internal interface (e.g.
  `backend/llm/provider.py`), never called directly from business logic.
- Which provider is active is chosen by one environment variable, read in
  exactly one place.
- The output contract (Pydantic schemas for extraction, comparison, and
  scoring) stays fixed regardless of provider.
- Prompts live in one place per task, versioned, with the Ragas evaluation
  set re-run after any provider or prompt change.

## Determinism and accuracy (required — this addresses reported inconsistency)
If the system currently produces different-feeling results across runs on
the same input, treat that as a defect to fix, not an inherent property of
LLMs to accept. Concretely:
- Set the LLM's sampling temperature to 0 (or as close to 0 as the
  provider allows) for extraction, comparison, and scoring calls. These
  are judgment tasks that should be as repeatable as possible, not
  creative-writing tasks.
- Pin the exact model version/tag in configuration (e.g. a specific Ollama
  model tag, not a "latest" alias) so behavior doesn't silently shift on a
  model update.
- Require structured output (a defined Pydantic schema) from every LLM
  call in the pipeline. If a response fails to validate against the
  schema, retry a small, fixed number of times, then fail explicitly with
  a clear error rather than returning a best-effort guess.
- Maintain a small, fixed set of "golden" test cases (known input, known
  expected extraction/score/suggestions) that must produce stable results
  across runs. Add to this set whenever a real inconsistency is found and
  fixed — this is what actually prevents recurrence, more than a general
  instruction to "be accurate."
- Log the raw model input and output for every pipeline run via Langfuse,
  so any case a doctor flags as wrong can actually be traced and
  diagnosed, not just re-run and hoped to be different.
- Never let variance in a non-deterministic call reach the doctor as an
  unexplained inconsistency — if retrieval confidence is low or output
  validation fails, that must produce an explicit state (see the
  no-match guardrail in the RAG evaluation section), never a silent guess.
- The current scoring stage is algorithmic rather than an LLM call. It uses
  the validated comparison state to calculate the score and create cited
  suggestions, so temperature/model/retry settings do not apply to scoring.
  Its output is validated by the `ReviewResponse` schema and fixed golden
  cases.

## Guideline knowledge base — Phase 1 and Phase 2 complete
The initial guideline knowledge base contains real, sourced Indian clinical
documents for asthma, diabetes, and high blood pressure. The source PDFs are
preserved under `knowledge_base/guidelines/<diagnosis-slug>/` alongside
full Markdown conversions and metadata. Metadata records the source, title,
URL, retrieval date, diagnosis, text extractability, and known
reuse/licensing terms. Do not fabricate guideline content, and do not infer
that a source may be redistributed merely because it is publicly readable.

The verified documents are from ICMR, the Department of Health Research and
Ministry of Health and Family Welfare, and the Lung India publication that
documents bronchial-asthma recommendations. The indexed set currently has
seven documents and 1,100 unique FAISS chunks across the three diagnosis
folders. The Markdown ingestion path preserves source filenames and URLs in
index metadata and remains idempotent.

Future diagnosis coverage must be added as a new sourced folder with its
metadata and Markdown representation. Do not change extraction, comparison,
scoring, or retrieval code merely to add a diagnosis.
- Guidelines live under `/knowledge_base/guidelines/<diagnosis-slug>/`,
  one folder per diagnosis, each with the source document(s) and a
  metadata file (source name, URL, date retrieved, diagnosis name/
  synonyms, and India-relevance notes such as regional terminology or
  dosage-form availability where relevant).
- The ingestion/indexing script is idempotent and re-runnable. Adding,
  updating, or removing a diagnosis means adding/editing/removing a
  folder — never a code change.
- Expand coverage by adding folders, not by touching extraction,
  comparison, or scoring code. If adding a diagnosis requires a code
  change, the coupling is too tight and should be flagged.

## RAG evaluation and guardrails (required, not optional polish)
- Every suggestion must include the specific retrieved guideline
  chunk/passage it's grounded in. A suggestion with no traceable source is
  a defect.
- If retrieval returns no reasonably matching guideline for a diagnosis
  (below a defined, configurable similarity/confidence threshold), the
  system must say so explicitly rather than generating a best-guess
  suggestion.
- Run the Ragas evaluation set (retrieval quality, faithfulness, answer
  relevance, context precision) whenever the knowledge base, prompts, or
  LLM provider changes. A Ragas regression blocks merging, same as a
  failing test.
- Never let the system, its UI, or its documentation claim broader
  diagnosis coverage or accuracy than what the current knowledge base and
  evaluation results actually support.

## Document import (PDF, DOCX, TXT — required, not a placeholder)
- The system must genuinely parse all three formats, not fall back to
  placeholder text for anything but a truly corrupt or unreadable file:
  PDF via a real text-extraction library (e.g. `pdfplumber` or `pypdf`),
  DOCX via `python-docx`, plain text directly.
- Validate file type and size before parsing. If a file fails to parse
  cleanly, return an explicit, specific error to the caller — never
  silently substitute placeholder content into a real case.

## Document structuring and formatting (required — separate from scoring)
This is independent of the completeness score and must run regardless of
it, including when a document already scores well or when the diagnosis
has no matching guideline:
- On export, the system reformats the imported document into a
  consistent, well-labeled structure (e.g. Patient Information, Diagnosis,
  Hospital Course, Medications, Advice, Follow-up) even if no AI
  suggestions apply.
- This is a layout-only operation: reorganizing and labeling existing
  content. It must never add, remove, or reword clinical facts. Only
  content that came from an accepted suggestion (a real AI-generated
  addition, already reviewed and approved by the doctor) may add new
  clinical content, and it must remain visually distinguishable from the
  original document's own content (see the "Added on review" convention
  already used in the review workspace).
- Include a verification step that checks every sentence of the original
  document is still present (possibly relabeled/reordered) in the
  structured output, and flags a warning if content appears to have been
  dropped during structuring. Treat a dropped-content warning as a defect
  to fix, not something to suppress.

## API design for live interaction (required for future frontend support)
Whatever frontend eventually consumes this API needs to update the UI
per-decision, not just submit-and-reload, and needs a way to preview
output before committing to a download. Design the FastAPI layer
accordingly:
- `POST /reviews` — upload a document, returns the case with its extracted
  blocks and suggestions.
- `GET /reviews/{id}` — fetch the current state of a case.
- `PATCH /reviews/{id}/suggestions/{suggestion_id}` — set a single
  suggestion's status (pending/accepted/rejected). This is the endpoint a
  live UI calls on every Accept/Ignore click — do not require a full
  re-submission to change one suggestion's status.
- `GET /reviews/{id}/preview?format=pdf|docx|txt` — returns a preview-safe
  representation of the current final document, without marking the case
  as exported. This is what a live "preview before download" UI calls.
- `POST /reviews/{id}/export?format=pdf|docx|txt` — generates the actual
  downloadable file, marks the case exported, and writes to the audit log.
- `GET /reviews?search=&status=&sort=&group_by=` — history listing with
  search, filter, sort, and grouping support, so a history UI doesn't need
  to fetch everything and filter client-side.

Phase 6 implements these routes with typed Pydantic responses. Preview is a
non-exporting text-safe representation of the persisted source document;
layout structuring and downloadable export remain Phase 7 work. The legacy
`/discharge` routes remain available for compatibility with existing clients.

## Non-negotiable project rule
The system is advisory only. Never implement a path where a suggestion is
applied to the discharge document automatically. Every suggestion needs an
explicit doctor decision before anything is treated as final, and that
decision must be recorded in the audit log.

## Folder structure (create if missing; don't restructure without asking)
```
/backend                FastAPI app: routers, services
/backend/llm            Provider abstraction, prompts
/backend/rag            LangGraph workflow: extract -> retrieve -> compare -> score
/backend/formatting     Document structuring/formatting (see above), separate from /rag
/backend/importers      PDF/DOCX/TXT parsing
/backend/models         Pydantic schemas + SQLAlchemy models
/knowledge_base
/knowledge_base/guidelines/<diagnosis-slug>/   source docs + metadata
/knowledge_base/ingest.py                      indexing script
/tests                  pytest suite, mirrors /backend structure
/tests/eval             Ragas evaluation set and runner
/tests/golden           Golden test cases for determinism (see above)
/docker                 Dockerfile(s), docker-compose.yml
.github/workflows       CI config
```

## Commands
Keep this section accurate — update it the moment a command changes.
- Run backend: `uvicorn backend.main:app --reload`
- Run tests: `pytest`
- Run RAG evaluation: `python tests/eval/run_ragas.py`
- Run golden/determinism checks: `python tests/golden/run_golden.py`
- Lint: `ruff check .`
- Type-check: `mypy backend`
- Security scan: `bandit -r backend` and `pip-audit`
- Ingest/re-index guidelines: `python knowledge_base/ingest.py`
- Run everything via Docker: `docker compose up`

## Conventions
- Every suggestion carries a reference to the specific retrieved guideline
  passage it's grounded in.
- Pydantic models for every API request/response, never raw dicts.
- One logical change per commit. Conventional commit messages.
- No real or identifiable patient data anywhere.
- No emojis anywhere — code, comments, commits, README, any documentation
  file, or any user-facing output.
- No claim, anywhere in code comments, README, commit messages, or output,
  that overstates what the system actually does or covers — no
  "bug-free," "fully secure," "covers all diagnoses," or similar.
  "Error-free" and "100% secure" are not achievable claims for any real
  system; state what is actually tested/covered instead.

## Quality & testing standards
- Every feature ships with tests covering the success path and at least
  one realistic failure path.
- CI runs lint, type-check, tests, the golden/determinism set, and the
  Ragas evaluation set (where relevant) on every pull request. A red CI
  run blocks merging, always.

## Security standards (free/open-source tooling only)
- Secrets live in environment variables / a local `.env`, never committed.
- All database access goes through the ORM / parameterized queries.
- Every file upload is validated for type and size before processing.
  Sanitize extracted text before it's used in any prompt or stored.
- `bandit` and `pip-audit` run in CI on every PR.
- Hashed passwords for any authentication.
- Production traffic is HTTPS only.
- Basic rate limiting on the upload endpoint.
- No PHI/PII crosses the scope boundary in ARCHITECTURE.md.

## Scalability & maintainability
- Backend endpoints are stateless; session/history state lives in
  PostgreSQL.
- Long-running work runs as an async endpoint or background task.
- Vector store and database connections come from configuration, never
  hardcoded.
- Any list view showing more than ~20 records is paginated.

## Boundaries
- Never commit directly to `main` — feature branch + pull request, always.
- Never add a new dependency without naming it in the PR description.
- Never change the approved stack without proposing it and getting
  explicit sign-off first.
- Do not touch frontend/Phase 10 work while any earlier phase in
  STATUS.md is active.
- Update ARCHITECTURE.md the moment a real architectural decision changes.
- Update STATUS.md at the end of every phase or enhancement task.