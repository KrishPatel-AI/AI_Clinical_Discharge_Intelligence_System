# AI Clinical Discharge Intelligence System

An AI-powered second reviewer for hospital discharge summaries. It reads a
discharge summary, retrieves the matching clinical guideline for the
diagnosis, and produces a completeness score plus guideline-grounded
suggestions for missing information (follow-up dates, medicines, warning
signs, etc.). The doctor reviews and approves or ignores every suggestion -
the AI never edits the discharge document itself.

B.Tech Engineering Project - II, Semester VII, AY 2026-27, Group 5-B.

## Status
Phases 0-9 are complete and verified. The system features genuine document
parsing (PDF, DOCX, TXT), an India-sourced clinical guideline knowledge base
(asthma, diabetes, high blood pressure) indexed with FAISS, deterministic
RAG-grounded comparison and scoring, live-interaction APIs (`/reviews`), layout-only
export structuring, complete Langfuse metadata observability, Ragas evaluation gates,
Alembic versioned schema migrations, and full Docker Compose containerization.
Frontend implementation (Next.js + HeroUI) is scoped for Phase 10.
See [STATUS.md](./STATUS.md) for the active status and phase details.

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

### 1. Run full stack via Docker Compose
To launch the complete system (FastAPI API, PostgreSQL 16, Ollama, and vector store) with automated migrations and indexing:
```bash
docker compose up
```
The API will be available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

### 2. Local development
To run locally in a Python 3.11 virtual environment:
```bash
# Apply database migrations
alembic upgrade head

# Ingest / update guideline vector index
python knowledge_base/ingest.py

# Start FastAPI server
uvicorn backend.main:app --reload
```

### 3. Verification & testing
```bash
# Run unit & integration test suite
pytest

# Run golden determinism test suite
pytest tests/golden -q

# Run Ragas evaluation
python tests/eval/run_ragas.py

# Lint and type-check
ruff check .
mypy backend

# Security scan and dependency audit
bandit -r backend
pip-audit --skip-editable --ignore-vuln PYSEC-2026-2447 --ignore-vuln PYSEC-2026-3046
```

## Scope
No real patient data is used or stored. The system does not connect to any
live hospital or EHR system. Guideline coverage starts with a small,
curated set of common diagnoses and expands over time.