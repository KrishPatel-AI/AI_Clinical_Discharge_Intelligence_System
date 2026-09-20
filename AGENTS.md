# AGENTS.md

## Project
AI Clinical Discharge Intelligence System — a RAG-based tool that reads a
hospital discharge summary, retrieves the matching clinical guideline for the
diagnosis, and produces a completeness score plus guideline-grounded
suggestions for the doctor to review. The AI never edits the discharge
document. Every suggestion is read-only until a doctor explicitly accepts or
ignores it in the review UI, and that decision is written to an audit log.

Read ARCHITECTURE.md and STATUS.md before doing anything else.
STATUS.md tells you which phase is active right now — work on that phase
only, unless told otherwise.

Krish (the project owner) has no prior RAG experience and no guideline data
yet. Do not assume familiarity with RAG concepts when discussing this
project with him — explain in plain language when it matters, and never
assume a data source or dataset exists unless it's named in ARCHITECTURE.md
or STATUS.md.

## Approved stack — do not change without flagging it first
- Backend: Python, FastAPI
- Frontend: Streamlit (doctor-facing UI)
- AI orchestration: LangChain + LangGraph
- LLM runtime: Ollama, local, for development and initial deployment
- Vector store: ChromaDB or FAISS (guideline knowledge base)
- Relational store: PostgreSQL (users, reports, audit logs, dashboard metrics)
- Observability: Langfuse (tracing every prompt/response/latency/error),
  Ragas (RAG quality evaluation — retrieval quality, faithfulness, answer
  relevance, context precision)
- Containerization / CI: Docker, GitHub Actions
- Deployment target: Render or Railway

## LLM provider abstraction (required — this is how Ollama-to-cloud stays safe)
- All LLM calls go through a single internal interface (e.g.
  `backend/llm/provider.py`), never called directly from business logic.
- Which provider is active (Ollama today, a cloud model such as Gemini
  later) is chosen by one environment variable, read in exactly one place.
- The output contract — the Pydantic schema for extracted fields, and for
  scoring/suggestions — stays fixed regardless of which provider produced
  it. If a provider's raw output doesn't fit the schema, the provider
  adapter is responsible for conforming it, not the calling code.
- Prompts live in one place per task (e.g. `backend/llm/prompts.py`),
  version them (a comment or filename suffix is enough at this scale), and
  re-run the Ragas evaluation set (see below) after any provider or prompt
  change before treating it as safe to ship.

## Guideline knowledge base — sourcing and structure
Krish does not have guideline data yet. This is Phase 1's job, not assumed
to already exist. Do not fabricate or invent guideline content — only use
real, sourced documents.
- Realistic free starting sources to evaluate in Phase 1: MedlinePlus
  (produced by the U.S. National Library of Medicine — publishes free,
  structured patient-care and discharge-instruction content, with XML data
  files and a connect API; verify current reuse/redistribution terms on
  medlineplus.gov before ingesting), and publicly published Indian
  government/hospital standard treatment guidelines (e.g. National Health
  Mission or ICMR-published guidelines, where available as public PDFs).
  Confirm licensing/usage terms for whichever source is actually used, and
  record the source and terms in ARCHITECTURE.md once chosen — don't treat
  this as settled until it's written down.
- Guidelines live under `/knowledge_base/guidelines/<diagnosis-slug>/`, one
  folder per diagnosis, each with the source document(s) and a small
  metadata file (source name, URL, date retrieved, diagnosis name/synonyms).
  Adding, updating, or removing a diagnosis means adding/editing/removing a
  folder — never a code change.
- The ingestion/indexing script is idempotent and re-runnable: running it
  again after adding one new diagnosis folder must not require deleting or
  rebuilding the entire vector store from scratch, and must not silently
  duplicate existing entries.
- Start with 2–3 diagnoses. Expanding coverage later is adding folders, not
  redesigning anything — if a change to add a diagnosis requires touching
  extraction, comparison, or scoring code, that's a sign the coupling is
  too tight and should be flagged before proceeding.

## RAG evaluation and guardrails (required, not optional polish)
- Every suggestion the scoring engine outputs must include the specific
  retrieved guideline chunk/passage it's grounded in. A suggestion with no
  traceable source is a defect, not an acceptable shortcut.
- If retrieval returns no reasonably matching guideline for a diagnosis
  (below a defined similarity/confidence threshold), the system must say
  so explicitly — e.g. "No matching guideline found for this diagnosis" —
  rather than generating a best-guess suggestion. This is a required
  guardrail, not a future nice-to-have.
- Run the Ragas evaluation set (retrieval quality, faithfulness, answer
  relevance, context precision) on a small, fixed test set of sample
  cases whenever the knowledge base, prompts, or LLM provider changes.
  Treat a Ragas regression as a blocker for merging, the same as a failing
  test.
- Never let the system, its UI, or its documentation claim broader
  diagnosis coverage or accuracy than what the current knowledge base and
  evaluation results actually support.

## Design system (target: minimalist, consistent — Streamlit's real ceiling, honestly)
- One neutral base palette plus exactly one accent color. No gradients, no
  decorative color use. Define these as named tokens once (e.g. in
  `.streamlit/config.toml` and a small shared constants file), reused
  everywhere — never a one-off color picked per screen.
- One consistent type scale (a small number of font sizes — e.g. heading,
  subheading, body, caption) and one consistent spacing scale, applied the
  same way on every screen.
- Every interactive element (buttons, inputs, cards) uses the same visual
  treatment across the app. No two screens should look like they came from
  different projects.
- No emojis anywhere in the interface, code, or documentation. Status or
  state indicators use plain text labels, optionally paired with a simple
  typographic glyph — never color or emoji alone.
- Be explicit with Krish, in-session, if a specific "Google-product-level"
  visual request (custom animation, precise pixel control, non-standard
  component behavior) is not realistically achievable in Streamlit — name
  the limitation rather than attempting a fragile workaround that breaks
  on the next Streamlit update.

## Responsiveness (target: usable from small phones to large desktops)
- Never use fixed pixel widths for layout containers; use Streamlit's
  container/column system and relative sizing so layouts reflow rather
  than break on narrow screens.
- Test every new or changed screen at minimum at three widths: a small
  phone (~360px), a tablet (~768px), and a desktop (~1440px) — actually
  resize a browser window or use device emulation, don't assume it's fine.
- Tables and any wide content scroll horizontally within their own
  container rather than forcing the whole page to scroll sideways.
- Touch targets (buttons, upload controls) stay large enough to use
  comfortably on a touchscreen, not just a mouse.
- Document any genuine responsiveness limitation you hit (Streamlit has
  real ones) in ARCHITECTURE.md's non-functional requirements section
  rather than silently shipping a broken mobile view.

## Non-negotiable project rule
The system is advisory only. Never implement a path where a suggestion is
applied to the discharge document automatically. Every suggestion needs an
explicit doctor decision (accept/ignore) before anything is treated as
final, and that decision must be recorded in the audit log.

## Folder structure (create if missing; don't restructure without asking)
```
/backend                FastAPI app: routers, services
/backend/llm            Provider abstraction, prompts (see above)
/backend/rag            LangGraph workflow: extract -> retrieve -> compare -> score
/backend/models         Pydantic schemas + SQLAlchemy models
/knowledge_base
/knowledge_base/guidelines/<diagnosis-slug>/   source docs + metadata
/knowledge_base/ingest.py                      indexing script
/frontend               Streamlit app
/tests                  pytest suite, mirrors /backend structure
/tests/eval             Ragas evaluation set and runner
/docker                 Dockerfile(s), docker-compose.yml
.github/workflows       CI config
```

## Commands
Keep this section accurate — update it the moment a command changes.
- Run backend: `uvicorn backend.main:app --reload`
- Run frontend: `streamlit run frontend/app.py`
- Run tests: `pytest`
- Run RAG evaluation: `python tests/eval/run_ragas.py`
- Lint: `ruff check .`
- Type-check: `mypy backend`
- Security scan: `bandit -r backend` and `pip-audit`
- Ingest/re-index guidelines: `python knowledge_base/ingest.py`
- Run everything via Docker: `docker compose up`

## Conventions
- Every suggestion the scoring engine outputs must carry a reference to the
  specific retrieved guideline passage it's grounded in.
- Pydantic models for every API request/response, never raw dicts.
- One logical change per commit. Conventional commit messages
  (feat:, fix:, chore:, docs:, test:).
- No real or identifiable patient data anywhere — code, fixtures, test
  data, or example files. Synthetic or de-identified only.
- No emojis anywhere — code, comments, commits, README, any documentation
  file, or the UI.
- No claim, anywhere in code comments, README, commit messages, or UI
  copy, that overstates what the system actually does or covers — no
  "bug-free," "fully secure," "covers all diagnoses," or similar. State
  what's actually true.

## Quality & testing standards
- Every feature ships with tests covering the success path and at least
  one realistic failure path.
- CI runs lint, type-check, tests, and the Ragas evaluation set (where
  relevant) on every pull request. A red CI run blocks merging, always.

## Security standards (free/open-source tooling only)
- Secrets live in environment variables / a local `.env`, never committed;
  `.env` is in `.gitignore` from the first commit.
- All database access goes through the ORM / parameterized queries.
- Every file upload is validated for type and size before processing.
  Sanitize extracted text before it's used in any prompt or stored.
- `bandit` and `pip-audit` run in CI on every PR.
- Hashed passwords (`passlib`/bcrypt) for any authentication — never
  hardcoded or plaintext credentials.
- Production traffic is HTTPS only.
- Basic rate limiting on the upload endpoint.
- No PHI/PII crosses the scope boundary in ARCHITECTURE.md.

## Scalability & maintainability
- Backend endpoints are stateless; session/history state lives in
  PostgreSQL, not server memory.
- Long-running work (extraction, retrieval, scoring) runs as an async
  endpoint or background task.
- Vector store and database connections come from configuration/
  environment variables, never hardcoded.
- Any list view showing more than ~20 records is paginated.

## Boundaries
- Never commit directly to `main` — feature branch + pull request, always.
- Never add a new dependency without naming it in the PR description.
- Never change the approved stack above without proposing it and getting
  explicit sign-off first.
- Update ARCHITECTURE.md the moment a real architectural decision changes.
- Update STATUS.md at the end of every phase.
