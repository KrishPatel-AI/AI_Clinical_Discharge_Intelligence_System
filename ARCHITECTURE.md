# ARCHITECTURE.md

This is the current system design. It reflects what has actually been built
or approved — not aspirations. Update it the moment a real architectural
decision is made or changed; append to the Revision Log below.

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
1. **Upload** — doctor uploads a discharge summary (PDF, Word, or plain text).
2. **Extract** — the AI extracts diagnosis, medicines, follow-up
   requirements, warning signs, and other key clinical fields.
3. **Retrieve** — the matching guideline is fetched from the vector store,
   based on the identified diagnosis. If none matches confidently, the
   system reports that instead of proceeding.
4. **Compare** — the extracted summary is compared against the retrieved
   guideline, section by section.
5. **Score** — a completeness score and a list of gaps are generated, each
   one explained and tied to the specific guideline passage it's based on.
6. **Review** — the doctor accepts or ignores each suggestion individually.
   Nothing is applied automatically.
7. **Approve** — a complete audit record is saved: timestamp, completeness
   score, every suggestion generated, and every doctor decision.

## Layers

| Layer | Technology | Responsibility |
|---|---|---|
| Presentation | Streamlit | Upload summaries, review AI suggestions, view session history/dashboard |
| API | FastAPI | Receives uploads, triggers the review pipeline, returns results to the UI |
| AI processing | LangChain + LangGraph + LLM provider abstraction | Extracts clinical fields, retrieves the guideline, compares, scores, and generates explanations |
| Knowledge | ChromaDB / FAISS | Stores and semantically searches the indexed guideline documents |
| Data | PostgreSQL | Stores users, generated reports, audit logs, dashboard metrics |
| Monitoring (cross-cutting) | Langfuse, Ragas | Langfuse traces every prompt/response/latency/error; Ragas evaluates retrieval quality, faithfulness, answer relevance, context precision |

## Guideline data — status: not yet sourced
No guideline dataset has been chosen or ingested yet. Candidates to
evaluate in Phase 1 (see AGENTS.md for the sourcing note):
- MedlinePlus (U.S. National Library of Medicine) — free, structured
  patient-care and discharge-instruction content with XML data files and a
  connect API. Reuse/redistribution terms must be verified on
  medlineplus.gov before ingestion.
- Publicly published Indian government/hospital standard treatment
  guidelines (e.g. National Health Mission or ICMR-published documents),
  where available as public PDFs.
This section will be updated with the actual source(s), licensing terms,
and diagnosis coverage once Phase 1 is complete — do not treat this as
decided until then.

## LLM provider strategy
- Development and initial deployment run on Ollama (local), to avoid
  per-request cost and rate limits while building.
- All LLM calls go through one internal provider interface (see AGENTS.md)
  so switching to a cloud model later is a configuration change, not a
  rewrite. The extraction/scoring output schema is fixed regardless of
  provider.
- Before treating a provider switch as safe, re-run the Ragas evaluation
  set and compare results against the Ollama baseline.

## Key decisions and why
- **Ollama as the default LLM runtime, swappable by design** — avoids
  per-request cost and rate limits during development; the provider
  abstraction (AGENTS.md) keeps a future cloud-model switch low-risk.
- **RAG over free-generation** — every suggestion must be traceable to an
  actual guideline passage, both for clinical trustworthiness and to
  satisfy the "explainable, guideline-grounded" requirement.
- **Streamlit for the frontend** — fastest path to a working, testable UI
  for this team's size and timeline. Known trade-off: Streamlit's layout
  system is responsive but has real limits on pixel-level, fully custom
  responsive design compared to a dedicated frontend framework. The
  standards in AGENTS.md are written to get as close to a clean, minimal,
  consistent product feel as Streamlit genuinely supports. If a specific
  visual requirement turns out to be unreachable in Streamlit, that is a
  deliberate stack-change discussion to have explicitly, not something to
  force with fragile workarounds.
- **No live hospital/EHR integration, no real patient data** — explicit
  scope boundary for this version.
- **Doctor-in-the-loop, no auto-apply** — the AI is a second reviewer,
  never an editor of the discharge document itself.
- **Stateless API + externalized state** — no structural blocker to
  scaling later, without over-provisioning for load the project doesn't
  currently have.

## Non-functional requirements
Targets the implementation is expected to meet — see AGENTS.md for the
concrete checklist behind each one.
- **Correctness:** tests for the success path and at least one realistic
  failure path on every feature; CI blocks merging on a red run.
- **Groundedness (RAG-specific):** no suggestion without a cited guideline
  passage; an explicit "no matching guideline" state when retrieval
  confidence is too low; Ragas evaluation re-run on any knowledge base,
  prompt, or provider change.
- **Security:** addressed against the OWASP Top 10 categories relevant to
  this system, using free/open-source scanning (`bandit`, `pip-audit`) in
  CI. No system is "fully secure" — this document tracks what is actually
  covered.
- **Scalability:** stateless API layer, externalized session/history
  state, config-driven service connections.
- **Responsiveness:** every screen usable from a small phone (~360px) to a
  large desktop (~1440px), within Streamlit's real layout capabilities
  (see the Streamlit trade-off above).
- **Maintainability:** one approved stack, one folder layout, guidelines
  added/changed by folder — not code — changes, this document kept
  current.
- **UI/UX:** minimalist, consistent, emoji-free interface with explicit
  loading/empty/error/success states on every screen.

## Out of scope for the current build (see STATUS.md for future-phase items)
- EHR integration / automatic patient record loading
- Department-specific guideline sets
- Medicine conflict detection
- Voice input
- Regional language support (Hindi, Gujarati, etc.)

## Revision log
- 2026-09-20 — Added Non-functional requirements section.
- 2026-09-20 — Added the RAG plain-language explainer, guideline data
  sourcing status (not yet sourced — candidates listed), LLM provider
  strategy, and the Streamlit responsiveness trade-off, at Krish's
  request, since none of this was previously written down explicitly.
