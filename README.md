# AI Clinical Discharge Intelligence System

An AI-powered second reviewer for hospital discharge summaries. It reads a
discharge summary, retrieves the matching clinical guideline for the
diagnosis, and produces a completeness score plus guideline-grounded
suggestions for missing information (follow-up dates, medicines, warning
signs, etc.). The doctor reviews and approves or ignores every suggestion -
the AI never edits the discharge document itself.

B.Tech Engineering Project - II, Semester VII, AY 2026-27, Group 5-B.

## Status
Phases 0-10 are complete and verified. The system features genuine document
parsing (PDF, DOCX, TXT), an India-sourced clinical guideline knowledge base
(asthma, diabetes, high blood pressure) indexed with FAISS, deterministic
RAG-grounded comparison and scoring, live-interaction APIs (`/reviews`), layout-only
export structuring, complete Langfuse metadata observability, Ragas evaluation gates,
Alembic versioned schema migrations, full Docker Compose containerization, and a
production Next.js 15 + HeroUI clinical review frontend with native dark/light modes.
See [STATUS.md](./STATUS.md) for detailed verification history.

## Documentation map
- [ARCHITECTURE.md](./ARCHITECTURE.md) - system design: the layers, the
  end-to-end flow, and key technical decisions.
- [STATUS.md](./STATUS.md) - completion history, active status, and decision
  log. Read this before starting any work session.
- [AGENTS.md](./AGENTS.md) - instructions for AI agents: approved stack, folder
  structure, commands, boundaries, and regional scope constraints.
- [PROJECT_REPORT.md](./PROJECT_REPORT.md) - comprehensive academic engineering
  project report for University evaluation.

## How to run

### 1. Run full stack via Docker Compose
To launch backend services (FastAPI API, PostgreSQL 16, Ollama, and vector store) with automated migrations and indexing:
```bash
docker compose up
```
The API will be available at `http://localhost:8000` (interactive OpenAPI docs at `http://localhost:8000/docs`).

### 2. Local development

#### Backend (Python 3.11 virtual environment)
```bash
# Apply database migrations
alembic upgrade head

# Ingest / update guideline vector index
python knowledge_base/ingest.py

# Start FastAPI server
uvicorn backend.main:app --reload
```

#### Frontend (Next.js + HeroUI)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start Next.js development server
npm run dev
```
The frontend web application will be accessible at `http://localhost:3000`.

### 3. Verification & testing
```bash
# Backend unit & integration test suite
pytest

# Golden determinism test suite
pytest tests/golden -q

# Ragas evaluation
python tests/eval/run_ragas.py

# Backend lint and type-check
ruff check .
mypy backend

# Frontend tests and lint
cd frontend
npm test
npm run lint
npm run build
cd ..

# Security scan and dependency audit
bandit -r backend
pip-audit --skip-editable --ignore-vuln PYSEC-2026-2447 --ignore-vuln PYSEC-2026-3046
```

## Sample demonstration documents
A dedicated set of 12 realistic, synthetic clinical discharge summaries is available in `sample_documents/` for testing and demonstration:
- `sample_documents/asthma/` — 4 cases (PDF, DOCX, TXT) varying from nearly complete to missing medications and warning signs.
- `sample_documents/diabetes/` — 4 cases (PDF, DOCX, TXT) covering Type 1 and Type 2 diabetes with hypoglycemia and follow-up gaps.
- `sample_documents/hypertension/` — 3 cases (PDF, DOCX) covering Stage 2 hypertension, dosage gaps, and emergency red flags.
- `sample_documents/unsupported_condition/` — 1 case (PDF) covering Acute Appendicitis (out-of-scope diagnosis) demonstrating retrieval guardrails and no-match safe handling.

## Scope
No real patient data is used or stored; all sample records are synthetic. The system does not connect to any live hospital or EHR system. Guideline coverage is currently curated for Asthma, Diabetes, and Hypertension based on ICMR and MoHFW guidelines.