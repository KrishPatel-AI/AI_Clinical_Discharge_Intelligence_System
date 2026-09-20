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
- Phase 1 is complete: three official MedlinePlus XML health-topic records
  and per-diagnosis metadata with attribution terms are stored under
  `knowledge_base/guidelines/`.
- Phase 2 is complete: the sourced XML records are parsed, chunked, and
  incrementally indexed in FAISS with stable IDs; repeated runs do not
  duplicate chunks, and queries return the expected diagnosis for all three
  initial records.
- Phase 3 is complete: validated PDF, DOCX, and TXT uploads return the fixed
  extraction schema through the FastAPI endpoint, with success/failure tests
  and a live synthetic Ollama-provider check.
- Active phase: **Phase 3 — Document extraction** (complete on this branch;
  activate Phase 4 after merge to `main`)
- Last updated: 2026-09-20

## Definition of done — applies to every phase below
- Tests exist for its success path and at least one realistic failure
  path, and they pass.
- Lint, type-check, and the security scans (`bandit`, `pip-audit`) are
  clean in CI.
- No emojis were introduced anywhere.
- Any new screen has its loading/empty/error/success states designed and
  is checked at phone/tablet/desktop widths (see AGENTS.md).
- Any RAG-affecting change (knowledge base, prompts, provider) has the
  Ragas evaluation set re-run, with results compared to the prior baseline.
- ARCHITECTURE.md and this file are updated if anything changed.

## Phase plan
Work exactly one phase at a time. Do not start the next phase until the
current one is merged to `main` and marked done here.

- [x] **Phase 0 — Repo scaffold & environment.** Folder structure from
  AGENTS.md, Python virtual environment / requirements file, Ollama
  installed with one model pulled locally, empty FastAPI and Streamlit
  entry points that run, `.gitignore` covering `.env` and local artifacts,
  CI workflow skeleton. Done = both `uvicorn` and `streamlit run` start
  without errors, CI runs green on an empty repo.
- [x] **Phase 1 — Source & structure guideline data.** No RAG knowledge
  required for this phase — it's about finding and organizing real
  documents, not code. Evaluate MedlinePlus and/or public Indian government
  guideline documents (see ARCHITECTURE.md), pick 2–3 starting diagnoses,
  verify usage/reuse terms, and save the source documents under
  `/knowledge_base/guidelines/<diagnosis-slug>/` with a metadata file each
  (source, URL, date retrieved). Done = 2–3 diagnosis folders exist with
  real, sourced documents and recorded licensing terms; ARCHITECTURE.md's
  "Guideline data" section is updated with what was actually chosen.
- [x] **Phase 2 — Guideline ingestion & indexing.** Write the
  chunking/embedding script, index the Phase 1 documents into
  ChromaDB/FAISS, make the script idempotent and re-runnable. Done = a
  test script queries the store and gets back a relevant guideline chunk
  for each of the starting diagnoses.
- [x] **Phase 3 — Document extraction.** FastAPI endpoint that accepts an
  uploaded file (PDF/Word/text), validates it, extracts diagnosis,
  medicines, follow-up info, and warning signs via the LLM provider
  abstraction. Done = uploading a sample summary returns structured JSON,
  with tests for a valid and an invalid file.
- [ ] **Phase 4 — RAG retrieval + comparison.** LangGraph workflow: take
  the extracted diagnosis, retrieve the matching guideline (or report no
  match), compare section-by-section against the extracted summary. Done =
  the workflow returns matched items and gaps for a known test case, and
  correctly reports "no match" for a diagnosis outside current coverage.
- [ ] **Phase 5 — Scoring, explanations & guardrails.** Turn the comparison
  into a completeness score and suggestions, each citing the specific
  guideline passage. Done = a sample upload produces a verifiable score
  and suggestions; a test asserts every suggestion carries a guideline
  reference and that low-confidence retrieval never produces a guessed
  suggestion.
- [ ] **Phase 6 — Persistence & audit log.** PostgreSQL schema for users,
  reports, audit logs, via the ORM only. Doctor accept/ignore decisions
  recorded per suggestion with a timestamp. Done = a full review cycle is
  retrievable from the database afterward.
- [ ] **Phase 7 — Streamlit review UI.** Upload screen, review/report
  screen with accept/ignore controls, paginated session history — wired
  end-to-end, styled per the design system and responsiveness standards in
  AGENTS.md. Done = a full upload-to-decision flow works through the UI at
  phone/tablet/desktop widths, with all states designed.
- [ ] **Phase 8 — Evaluation & monitoring.** Langfuse tracing across
  extraction, retrieval, and scoring; a fixed Ragas evaluation set
  established as the ongoing regression baseline. Done = a Langfuse trace
  and a Ragas report both exist, and the evaluation set is runnable as a
  single command.
- [ ] **Phase 9 — Containerization, CI & security gates.** Dockerfile(s) +
  docker-compose; GitHub Actions running tests, lint, and the security
  scans on every PR. Done = `docker compose up` runs the whole system from
  a clean checkout, CI fully green.
- [ ] **Phase 10 — Deployment & provider-swap check.** Deploy to Render or
  Railway (HTTPS only). Before or as part of this phase, do one real test
  of switching the LLM provider from Ollama to a cloud model via
  configuration only, and re-run the Ragas set to confirm no unacceptable
  regression, then decide which provider actually runs in the deployed
  system. Done = a doctor-facing URL exists, a full review cycle works on
  it, and the provider-swap test result is recorded in ARCHITECTURE.md.

Requirement changes go here too: if scope changes mid-project, add a new
phase (or split an existing one) rather than silently expanding a phase
that's already "done."

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
- *(add new entries here as real decisions get made — one line, with the
  reason)*
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
  provider check; Phase 4 is ready to start after this branch is merged to
  `main`.
