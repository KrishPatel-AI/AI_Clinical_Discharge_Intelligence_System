# AI Clinical Discharge Intelligence System

A guideline-grounded clinical intelligence platform that acts as an automated second reviewer for hospital discharge summaries. The system parses unstructured discharge summaries, identifies clinical entities, retrieves matching clinical guidelines, calculates a deterministic completeness score, and produces passage-grounded recommendations for clinician review.

The system operates under a strict clinician-in-the-loop design: the artificial intelligence never directly edits the discharge document. All suggestions remain advisory until a clinician explicitly accepts or ignores them, with every decision captured in an immutable audit trail.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Workflow and Execution Pipeline](#workflow-and-execution-pipeline)
- [Technology Stack](#technology-stack)
- [Project Directory Structure](#project-directory-structure)
- [Technical Implementation Details](#technical-implementation-details)
  - [Document Ingestion and Parsing](#document-ingestion-and-parsing)
  - [Deterministic LLM Extraction](#deterministic-llm-extraction)
  - [Vector Indexing and Guideline Retrieval](#vector-indexing-and-guideline-retrieval)
  - [Algorithmic Completeness Scoring](#algorithmic-completeness-scoring)
  - [Actionable Recommendations with Fallback](#actionable-recommendations-with-fallback)
  - [Layout-Only Structuring and Content Preservation](#layout-only-structuring-and-content-preservation)
  - [Privacy-Preserving Observability](#privacy-preserving-observability)
- [Knowledge Base & Clinical Guidelines](#knowledge-base--clinical-guidelines)
- [API Documentation](#api-documentation)
- [Database Schema & Migrations](#database-schema--migrations)
- [Frontend Application](#frontend-application)
- [Installation and Setup](#installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [Environment Configuration](#environment-configuration)
  - [Option A: Running with Docker Compose](#option-a-running-with-docker-compose)
  - [Option B: Local Development Setup](#option-b-local-development-setup)
- [Usage Instructions](#usage-instructions)
- [Sample Documents](#sample-documents)
- [Testing and Verification](#testing-and-verification)
- [Verified Project Metrics](#verified-project-metrics)
- [Security Posture & Compliance](#security-posture--compliance)
- [Current Implementation Status](#current-implementation-status)
- [Limitations and Known Constraints](#limitations-and-known-constraints)
- [Future Roadmap](#future-roadmap)
- [Contributing](#contributing)
- [License and Attribution](#license-and-attribution)

---

## Project Overview

Hospital discharge summaries represent the critical information bridge between inpatient care and outpatient recovery. During transition of care, omissions or ambiguous instructions regarding medications, follow-up timelines, and warning signs directly contribute to adverse drug events, medical complications, and avoidable hospital readmissions.

The AI Clinical Discharge Intelligence System provides an objective, automated safety layer. By comparing inpatient discharge records against authoritative Standard Treatment Guidelines (STGs) established by national health authorities (including the Indian Council of Medical Research [ICMR] and the Ministry of Health and Family Welfare [MoHFW]), the system identifies gaps in documentation before the patient leaves the hospital.

### Core System Tenets

1. **Advisory by Design:** The artificial intelligence acts exclusively as an analytical assistant. No clinical suggestion is automatically applied to a patient record.
2. **Zero-Hallucination Grounding:** Every clinical recommendation is mapped directly to an exact retrieved passage from an authenticated clinical guideline document.
3. **Deterministic Scoring:** Completeness scoring is calculated programmatically through mathematical section comparison rather than non-deterministic model generation.
4. **Protected Health Information (PHI) Boundary:** Observability and external tracing receive execution metadata only (stage, latency, status codes, IDs). Raw clinical text and patient identifiers never leave the local environment boundary.
5. **Fidelity Preservation:** Export formatting reorganizes content into standard clinical headings without modifying, paraphrasing, or dropping original sentences.

---

## Problem Statement

In modern clinical environments, physicians and residents routinely prepare discharge paperwork under severe time constraints. Consequently:

- Essential discharge elements—such as drug dosage titration, planned follow-up intervals, and red-flag symptoms—are frequently missed or inadequately documented.
- Generalist large language models (LLMs) used directly for clinical tasks introduce severe risks of medical hallucination, inconsistent scoring, and unverified recommendations.
- Standard generative AI interfaces lack traceability, offering recommendations without citing primary clinical evidence or providing audit trails for clinical governance.
- Automated editing tools risk altering clinician intent or accidentally removing subtle clinical context from legal medical records.

---

## Proposed Solution

This project implements a Retrieval-Augmented Generation (RAG) architecture tailored specifically for clinical discharge governance:

- **Multi-Format Parsing:** Ingests native PDF, DOCX, and plain-text discharge summaries up to 5 MB using format-specific binary parsers.
- **Structured Field Extraction:** Uses a local LLM via a strict provider abstraction operating at temperature 0.0 with Pydantic validation to extract diagnosis, medications, follow-up instructions, and warning signs.
- **Semantic Guideline Retrieval:** Queries a local FAISS vector index of national clinical guidelines, returning the most relevant evidence passage alongside a similarity score.
- **Safety Guardrails:** Enforces a strict retrieval threshold (similarity >= 0.20). Unrecognized or out-of-scope conditions cleanly trigger a `no_match` state without generating speculative recommendations.
- **Mathematical Completeness Evaluation:** Computes an objective score (0 to 100) based on verified section coverage against the retrieved guideline.
- **Granular Decision Interface:** Exposes RESTful endpoints enabling clinicians to review each suggestion, inspect the cited guideline passage, view the original source document, and make an explicit Accept or Ignore choice.
- **Audit-Logged Document Export:** Re-labels the summary into standardized sections (Patient Information, Diagnosis, Hospital Course, Medications, Advice, Follow-up, and Added on review) and exports to PDF, DOCX, or TXT while logging all decisions to a relational database.

---

## Key Features

- **Genuine Document Ingestion:** Full extraction support for PDF (`pypdf`), Word (`python-docx`), and plain text (`.txt`) with sanitization of control characters.
- **Strictly Grounded RAG Pipeline:** LangGraph-orchestrated workflow chaining retrieval, comparison, and scoring.
- **Programmatic Completeness Scoring:** Formula-driven evaluation (`round(100 * matched / compared)`) guaranteeing repeatable results across runs.
- **Live Decision Updates:** Granular `PATCH` endpoint enabling per-suggestion decisions without page reloads or full-case recalculations.
- **Split-Screen Review Workspace:** Modern Next.js + HeroUI web interface providing synchronized comparison between original source text and the structured reviewed document.
- **Pre-Export Document Preview:** Layout-safe endpoint (`GET /reviews/{id}/preview`) validating structuring output before committing to file generation.
- **Lossless Export Structuring:** Integrated verification pass (`verify_content_presence`) confirming that every sentence of the original document remains present in exported files.
- **Metadata-Only Tracing:** Complete pipeline instrumentation via Langfuse capturing latencies and operational metrics while keeping clinical text strictly within the application boundary.
- **Production Containerization:** Multi-stage Docker packaging running as an unprivileged user (`appuser:10001`) with Docker Compose orchestrating FastAPI, PostgreSQL 16, and Ollama.
- **Automated Database Migrations:** Versioned Alembic migrations managing relational schemas without startup race conditions.

---

## System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Presentation Layer (Next.js 14 + HeroUI)"]
        UI_Upload["Document Upload (PDF / DOCX / TXT)"]
        UI_Workspace["Review Workspace (Split-Screen)"]
        UI_History["Review History (Search / Filter / Paginate)"]
        UI_Export["Live Preview & Multi-Format Export"]
    end

    subgraph APILayer["API & Routing Layer (FastAPI)"]
        API_Reviews["/reviews (Upload, History, Detail)"]
        API_Patch["/reviews/{id}/suggestions/{id} (Live PATCH)"]
        API_Preview["/reviews/{id}/preview (Document Preview)"]
        API_Export["/reviews/{id}/export (File Generation)"]
        API_Guidelines["/guidelines (Catalog & Document Serving)"]
    end

    subgraph CoreEngine["Core Processing & RAG Workflow (LangGraph)"]
        ExtractService["Text Extraction & Sanitization (pypdf, python-docx)"]
        LLM_Extract["LLM Extraction (temp=0.0, JSON schema validation)"]
        RetrieveNode["Retrieve Node (FAISS similarity matching)"]
        CompareNode["Compare Node (Token intersection analysis)"]
        ScoreNode["Score Node (Deterministic programmatic calculation)"]
        RecGenerator["Recommendation Generator (LLM + Rule Fallback)"]
    end

    subgraph StorageLayer["Data & Knowledge Layer"]
        FAISS_Index["FAISS Vector Store (2048-d FlatIP Index)"]
        Guidelines_Disk["Clinical Guidelines Knowledge Base (Markdown + PDFs)"]
        Postgres_DB[("PostgreSQL 16 / SQLite (Alembic Migrated)")]
    end

    subgraph ObservabilityLayer["Observability & Evaluation"]
        Langfuse_Tracer["Langfuse (Metadata-only traces: latency, status, counts)"]
        Ragas_Eval["Ragas Framework (Faithfulness, Precision, Relevancy)"]
    end

    UI_Upload --> API_Reviews
    UI_Workspace --> API_Patch
    UI_Workspace --> API_Preview
    UI_Workspace --> API_Export
    UI_History --> API_Reviews

    API_Reviews --> ExtractService
    ExtractService --> LLM_Extract
    LLM_Extract --> RetrieveNode
    RetrieveNode <--> FAISS_Index
    RetrieveNode --> CompareNode
    CompareNode --> ScoreNode
    ScoreNode --> RecGenerator
    RecGenerator --> API_Reviews

    API_Reviews --> Postgres_DB
    API_Patch --> Postgres_DB
    API_Export --> Postgres_DB
    API_Guidelines --> Guidelines_Disk

    ExtractService -.-> Langfuse_Tracer
    RetrieveNode -.-> Langfuse_Tracer
    CompareNode -.-> Langfuse_Tracer
    ScoreNode -.-> Langfuse_Tracer
    API_Export -.-> Langfuse_Tracer
```

---

## Workflow and Execution Pipeline

When a hospital discharge summary is submitted to the system, it traverses an eight-stage pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Doctor / Clinician
    participant UI as Next.js Web App
    participant API as FastAPI Backend
    participant Parser as Extraction Service
    participant LLM as Ollama (llama3.2:3b)
    participant KB as FAISS Vector Store
    participant Engine as LangGraph Workflow
    participant DB as Relational DB (PostgreSQL)

    Clinician->>UI: Uploads discharge summary (PDF/DOCX/TXT)
    UI->>API: POST /reviews (multipart/form-data)
    API->>Parser: Validate format and extract plain text
    Parser->>LLM: Prompt structured extraction (temp=0.0)
    LLM-->>Parser: Validated JSON (diagnosis, meds, follow-up, warnings)
    Parser->>Engine: Run review_extraction()
    Engine->>KB: Query top-5 guideline candidates
    KB-->>Engine: Matching passage + similarity score
    alt Similarity < 0.20 (No Match Guardrail)
        Engine-->>API: status: "no_match", suggestions: []
    else Guideline Confidently Matched
        Engine->>Engine: Compare sections against guideline tokens
        Engine->>Engine: Compute algorithmic score: 100 * (matched / compared)
        Engine->>LLM: Generate actionable suggestion for each gap
        LLM-->>Engine: Action, target text, suggested text, explanation
    end
    Engine->>DB: Persist report, suggestions, and audit records
    DB-->>API: Persisted report ID
    API-->>UI: Return review response with report_id
    UI-->>Clinician: Display split-view workspace & suggestion cards

    Clinician->>UI: Clicks Accept or Ignore on suggestion
    UI->>API: PATCH /reviews/{id}/suggestions/{suggestion_id}
    API->>DB: Update suggestion decision & log timestamped audit event
    API->>DB: Programmatically recalculate completeness score
    DB-->>UI: Updated report state

    Clinician->>UI: Requests preview or download
    UI->>API: GET /reviews/{id}/preview or POST /reviews/{id}/export
    API->>API: Re-label sections into standard clinical layout
    API->>API: verify_content_presence() (assert 100% sentences retained)
    API->>DB: Log export event in audit_logs
    API-->>UI: Return formatted file (PDF / DOCX / TXT)
    UI-->>Clinician: Download finalized document
```

---

## Technology Stack

### Backend Infrastructure

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | >= 3.11 | Core runtime environment |
| Framework | FastAPI | >= 0.115, < 1.0 | Asynchronous REST API framework |
| Server Gateway | Uvicorn (standard) | >= 0.30, < 1.0 | High-performance ASGI production server |
| AI Orchestration | LangGraph | >= 1.0.10, < 2.0 | State-graph pipeline execution |
| Model Integration | Ollama / LangChain Community | >= 0.3.31, < 0.4.0 | Local LLM inference (`llama3.2:3b`) |
| Vector Engine | FAISS (`faiss-cpu`) | >= 1.8, < 2.0 | High-speed local similarity search |
| Database Engine | PostgreSQL / SQLite | PostgreSQL 16 | Relational storage for users, reports, logs |
| Database ORM | SQLAlchemy | >= 2.0, < 3.0 | Type-safe database mapping and queries |
| Migrations | Alembic | >= 1.13, < 2.0 | Versioned schema migration management |
| PDF Processing | pypdf | >= 5.0, < 7.0 | Binary text extraction from clinical PDFs |
| DOCX Processing | python-docx | >= 1.1, < 2.0 | Native Word document parsing and rendering |
| PDF Generation | ReportLab | >= 4.2, < 5.0 | Programmatic clinical PDF export generation |
| Data Validation | Pydantic | >= 2.9, < 3.0 | Runtime schema enforcement and validation |
| Observability | Langfuse | >= 4.7.0, < 5.0 | Operational metadata tracing |

### Frontend Infrastructure

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Framework | Next.js (App Router) | 14.2.24 | Full-stack React web framework |
| Core Library | React | ^18.0.0 | Declarative UI rendering |
| Component System | HeroUI (`@heroui/react`) | ^2.7.5 | Authoritative accessible clinical UI library |
| UI Styling | Tailwind CSS | ^3.4.1 | Utility-first CSS styling framework |
| Animations | Framer Motion | ^11.18.2 | Fluid layout transitions |
| Icons | Lucide React | ^1.52.0 | Consistent iconography |
| Theme Provider | next-themes | ^0.4.6 | Native dark and light mode synchronization |
| Language | TypeScript | ^5.0.0 | End-to-end type safety |
| Client Testing | Node Test Runner + tsx | ^4.23.15 | Fast, zero-dependency unit tests |

### Quality & Containerization

| Tool | Version | Responsibility |
|---|---|---|
| Pytest | >= 9.0.3, < 10.0 | Backend unit and integration test runner |
| Ragas | >= 0.4.3, < 0.5.0 | Retrieval, faithfulness, and relevancy evaluation |
| Ruff | >= 0.8, < 1.0 | Fast Python linter and code formatter |
| Mypy | >= 1.13, < 2.0 | Strict static type checking |
| Bandit | >= 1.7, < 2.0 | AST-based security vulnerability scanner |
| Pip-audit | >= 2.7, < 3.0 | Known vulnerability scanner for dependencies |
| Docker | Docker Engine 20+ | Multi-stage production container build |
| Docker Compose | Compose v2 | Local multi-service orchestration |

---

## Project Directory Structure

```
.
├── .env.example                               # Safe environment variable configuration template
├── .github/
│   └── workflows/
│       └── ci.yml                             # Automated CI quality, testing, and security gates
├── .streamlit/
│   └── config.toml                            # Early prototype theme configuration
├── AGENTS.md                                  # Operational specifications and project rules
├── alembic.ini                                # Alembic migration configuration
├── alembic/
│   ├── env.py                                 # Alembic environment runner
│   └── versions/
│       ├── cc7a5170229d_initial_schema.py     # Base relational tables migration
│       └── a8b2c3d4e5f6_add_initial_score_... # Initial score & actionable fields migration
├── ARCHITECTURE.md                            # Architectural design decisions and revision log
├── backend/
│   ├── config.py                              # Central environment and settings boundary
│   ├── db.py                                  # SQLAlchemy engine and session initialization
│   ├── formatting/
│   │   ├── export.py                          # Multi-format rendering (PDF, DOCX, TXT)
│   │   └── structuring.py                     # Layout-only structuring & sentence preservation check
│   ├── llm/
│   │   ├── prompts.py                         # Versioned extraction and recommendation prompts
│   │   └── provider.py                        # LLM provider protocol, Ollama adapter, rule fallback
│   ├── main.py                                # FastAPI application entrypoint and middleware
│   ├── models/
│   │   ├── database.py                        # SQLAlchemy ORM models (User, Report, Suggestion, Audit)
│   │   └── schemas.py                         # Pydantic request and response schemas
│   ├── observability/
│   │   └── tracing.py                         # Privacy-preserving Langfuse tracing context manager
│   ├── rag/
│   │   └── workflow.py                        # LangGraph workflow (retrieve, compare, score)
│   ├── routers/
│   │   ├── discharge.py                       # Review, PATCH, preview, export, and history endpoints
│   │   └── guidelines.py                      # Guideline catalog and document serving endpoints
│   └── services/
│       ├── extraction.py                      # Document validation and text extraction
│       ├── guidelines.py                      # Guideline resolution and presentation metadata
│       └── persistence.py                     # Report persistence, metrics recalculation, and audit logs
├── docker/
│   ├── Dockerfile                             # Hardened, unprivileged container image definition
│   ├── docker-compose.yml                     # Root docker-compose mirror
│   └── entrypoint.sh                          # Container boot script (DB wait, indexing, migrations)
├── docker-compose.yml                         # Orchestration for API, PostgreSQL 16, and Ollama
├── frontend/
│   ├── package.json                           # Frontend dependencies and npm scripts
│   ├── tailwind.config.ts                     # Tailwind CSS and HeroUI plugin configuration
│   ├── tsconfig.json                          # TypeScript compilation configuration
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                     # Root App Router layout with navbar and footer
│       │   ├── page.tsx                       # Upload interface and entry point
│       │   ├── reviews/
│       │   │   ├── page.tsx                   # Filterable review history workspace
│       │   │   └── [id]/page.tsx              # Granular review workspace with split-screen view
│       ├── components/
│       │   ├── history/HistoryWorkspace.tsx   # History table, search, filters, pagination
│       │   ├── layout/                        # AppNavbar, AppFooter, ThemeToggle
│       │   ├── review/                        # SuggestionCard, DocumentComparison, Modals
│       │   └── upload/DocumentUpload.tsx      # Drag-and-drop file upload with validation
│       ├── lib/
│       │   ├── api.ts                         # Strongly typed API client
│       │   └── api.test.ts                    # Unit tests for API client and error handling
│       └── types/api.ts                       # TypeScript interfaces mirroring backend schemas
├── knowledge_base/
│   ├── .faiss/                                # Generated FAISS vector index and chunk metadata
│   ├── ingest.py                              # Idempotent indexing script for Markdown guidelines
│   └── guidelines/                            # Clinical guideline repositories with metadata
│       ├── asthma/                            # Lung India & ICMR Asthma guidelines
│       ├── diabetes/                          # ICMR Type 1 & Type 2 Diabetes guidelines
│       └── high-blood-pressure/               # ICMR & MoHFW Hypertension guidelines
├── pyproject.toml                             # Python package build configuration and dependencies
├── sample_documents/                          # 12 synthetic clinical test cases
│   ├── asthma/                                # 4 cases across PDF, DOCX, TXT
│   ├── diabetes/                              # 4 cases across PDF, DOCX, TXT
│   ├── hypertension/                          # 3 cases across PDF, DOCX
│   └── unsupported_condition/                 # 1 case (Acute Appendicitis) for negative guardrail testing
├── SECURITY_NOTES.md                          # Scoped dependency audit exceptions and rationale
├── STATUS.md                                  # Verification history, phase tracking, and decision log
└── tests/
    ├── eval/                                  # Ragas evaluation runner and test configurations
    ├── golden/                                # Fixed golden datasets for extraction and scoring
    ├── test_extraction.py                     # Document upload and parsing tests
    ├── test_formatting.py                     # Document structuring and export tests
    ├── test_guidelines.py                     # Guideline resolution and serving tests
    ├── test_health.py                         # Health check endpoint test
    ├── test_ingest.py                         # Vector indexing idempotency tests
    ├── test_migrations.py                     # Alembic migration lifecycle tests
    ├── test_observability.py                  # Langfuse privacy and metadata tests
    ├── test_persistence.py                    # Database persistence and review lifecycle tests
    └── test_workflow.py                       # LangGraph review workflow and guardrail tests
```

---

## Technical Implementation Details

### Document Ingestion and Parsing

The document extraction service in `backend/services/extraction.py` enforces strict file validation:
- Supported extensions: `.pdf`, `.docx`, `.txt`.
- Size ceiling: Exactly 5 MB (`5 * 1024 * 1024` bytes). Exceeding this boundary raises an explicit `400 Bad Request`.
- Text sanitization: Strips non-printable ASCII control characters (`[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]`) and normalizes line breaks while preserving clinical structure.
- Empty text check: Rejects files containing zero readable characters.

### Deterministic LLM Extraction

Field extraction is performed by `backend/llm/provider.py`:
- Temperature is fixed at `0.0`.
- Ollama is instructed via `format="json"` to output an exact schema: `diagnosis` (string), `medications` (array), `follow_up_requirements` (array), and `warning_signs` (array).
- Outputs are validated against the `DischargeExtraction` Pydantic model.
- If validation fails, the provider automatically retries up to 2 times (`get_llm_validation_retries()`) before raising an explicit exception.

### Vector Indexing and Guideline Retrieval

The vector subsystem in `knowledge_base/ingest.py`:
- Ingests structured Markdown files derived from clinical guidelines.
- Chunks text into 1200-character segments with a 150-character sliding overlap.
- Computes 2048-dimensional normalized term-hash embedding vectors.
- Stores vectors in a FAISS inner-product index (`faiss.IndexFlatIP`) alongside JSON metadata.
- Re-indexing is strictly idempotent: existing records are hashed and preserved without duplication.
- Retrieval guardrail: When querying the index, candidate matches must meet a minimum similarity threshold of `0.20`. Diagnoses falling below this threshold trigger an immediate `no_match` state, returning zero generated suggestions.

### Algorithmic Completeness Scoring

To eliminate scoring drift and non-deterministic variations, scoring is calculated purely through algorithmic code in `backend/rag/workflow.py`:
- The system evaluates four primary clinical dimensions:
  1. `diagnosis`
  2. `medications`
  3. `follow_up_requirements`
  4. `warning_signs`
- Each section's extracted tokens are compared against the retrieved guideline passage tokens.
- If a section contains tokens intersecting with the guideline context, it is marked as `matched`. If values are missing or have zero token intersection, it is marked as `gap`.
- The initial completeness score is calculated as:
  $$\text{Completeness Score} = \text{round}\left(100 \times \frac{\text{matched\_sections}}{\text{total\_sections}}\right)$$
- If the clinician later accepts suggestions, the score is dynamically recalculated by `backend/services/persistence.py`:
  $$\text{Recalculated Score} = \min\left(100, \text{round}\left(100 \times \frac{\text{base\_matched} + \text{accepted\_count}}{\text{total\_criteria}}\right)\right)$$

### Actionable Recommendations with Fallback

For each identified section gap:
- An LLM call (`generate_recommendation`) analyzes the gap section, source text, and guideline passage to produce:
  - `action`: `"add"` | `"modify"` | `"remove"`
  - `target_text`: The exact sentence or heading in the summary that is deficient.
  - `suggested_text`: The exact clinical phrasing recommended for inclusion.
  - `explanation`: Clinical justification referencing the guideline.
- **Deterministic Rule Fallback:** If Ollama is unreachable, times out, or produces unparseable output, `deterministic_guideline_recommendation()` activates automatically. It parses relevant guideline sentences and constructs high-fidelity clinical recommendations deterministically without crashing.

### Layout-Only Structuring and Content Preservation

The export formatter in `backend/formatting/structuring.py`:
- Partitions the original summary into standard clinical sections:
  1. Patient Information
  2. Diagnosis
  3. Hospital Course
  4. Medications
  5. Advice
  6. Follow-up
  7. Added on review (reserved exclusively for accepted AI suggestions)
- **Content Preservation Verification:** Before any export or preview is finalized, `verify_content_presence()` normalizes and checks every single sentence of the original document against the structured output. If even one original sentence was dropped or corrupted during structuring, the operation immediately aborts with an HTTP 500 error.

### Privacy-Preserving Observability

Observability in `backend/observability/tracing.py`:
- Context manager wrapping all critical operations (`observation()`).
- Communicates with Langfuse if credentials are provided; degrades cleanly to a no-op if credentials are absent.
- **Zero-PHI Guarantee:** The tracing payload contains only stage names, duration latencies, character counts, status codes, and observation IDs. Raw clinical text, patient names, and guideline text are strictly prohibited from being passed to the tracer.

---

## Knowledge Base & Clinical Guidelines

The knowledge base contains 7 authoritative clinical guideline documents across 3 major non-communicable conditions, sourced from Indian national health agencies (ICMR and MoHFW).

| Condition | Document Title | Authoritative Source | Source URL | Ingested Format |
|---|---|---|---|---|
| **Asthma** | Guidelines for Diagnosis and Management of Bronchial Asthma | Lung India / Indian Chest Society (Vol 32, 2015) | [Lung India](https://journals.lww.com/lungindia/toc/2015/32001) | PDF, Markdown |
| **Asthma** | Standard Treatment Workflow (STW) for Management of Asthma | ICMR / Department of Health Research, MoHFW | [ICMR STW](https://stw.icmr.org.in/) | PDF, Markdown |
| **Diabetes** | Standard Treatment Workflow (STW) Diabetes Mellitus Type 2 | ICMR / Department of Health Research, MoHFW | [ICMR STW](https://stw.icmr.org.in/) | PDF, Markdown |
| **Diabetes** | ICMR Guidelines for Management of Type 2 Diabetes 2018 | Indian Council of Medical Research | [ICMR Portal](https://main.icmr.nic.in/) | PDF, Markdown |
| **Diabetes** | Guidelines for Management of Type 1 Diabetes (2022) | Indian Council of Medical Research | [ICMR Portal](https://main.icmr.nic.in/) | PDF, Markdown |
| **Hypertension** | Standard Treatment Workflow (STW) Hypertension in Adults | ICMR / Department of Health Research, MoHFW | [ICMR STW](https://stw.icmr.org.in/) | PDF, Markdown |
| **Hypertension** | Screening, Diagnosis, Assessment & Management of Primary Hypertension | Ministry of Health and Family Welfare, Govt. of India | [National Health Mission](https://nhm.gov.in/) | PDF, Markdown |

Per-diagnosis metadata is documented in `knowledge_base/guidelines/<diagnosis-slug>/metadata.json`.

---

## API Documentation

Interactive OpenAPI documentation is automatically served at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the backend is active.

### Primary Endpoints

| Method | Endpoint | Description | Request Payload | Response Schema |
|---|---|---|---|---|
| `GET` | `/health` | Service health status check | None | `{"status": "ok"}` |
| `POST` | `/reviews` | Upload, extract, compare, and persist a discharge review | Multipart file (`file`) | `ReviewResponse` |
| `GET` | `/reviews/{id}` | Retrieve persisted review state, suggestions, and audit log | None | `PersistedReportResponse` |
| `PATCH` | `/reviews/{id}/suggestions/{suggestion_id}` | Update decision on a suggestion (`pending`, `accepted`, `rejected`) | `{"status": "accepted"}` | `PersistedReportResponse` |
| `GET` | `/reviews/{id}/preview` | Fetch layout-structured preview without committing export | Query `?format=pdf\|docx\|txt` | `PreviewResponse` |
| `POST` | `/reviews/{id}/export` | Generate finalized document, commit export, and log audit event | Query `?format=pdf\|docx\|txt` | Binary attachment file |
| `GET` | `/reviews` | Search, filter, sort, and paginate review history | Query parameters (see below) | `ReviewHistoryResponse` |
| `GET` | `/guidelines` | List all ingested clinical guidelines and document counts | None | `list[dict]` |
| `GET` | `/guidelines/{slug}/metadata` | Retrieve authoritative metadata record for a guideline | None | `dict` |
| `GET` | `/guidelines/{slug}/document` | Stream original guideline document (PDF, DOCX, MD) | Query `?filename=...&source_url=...` | FileResponse |

### History Query Parameters (`GET /reviews`)

- `search` (string, optional): Case-insensitive match on filename, diagnosis, or message.
- `status` (string, optional): Filter by `needs_review`, `complete`, or `no_match`.
- `sort` (string, default: `newest`): Sort ordering: `newest`, `oldest`, or `score`.
- `group_by` (string, optional): Cluster response IDs by `diagnosis` or `status`.
- `offset` (integer, default: `0`): Pagination offset.
- `limit` (integer, default: `20`, max: `100`): Page size limit.

---

## Database Schema & Migrations

The relational database is managed using versioned Alembic migrations (`alembic/versions/`).

```mermaid
erDiagram
    USERS ||--o{ REPORTS : "creates"
    REPORTS ||--o{ SUGGESTIONS : "generates"
    REPORTS ||--o{ AUDIT_LOGS : "tracks"
    SUGGESTIONS ||--o{ AUDIT_LOGS : "logs"

    USERS {
        int id PK
        string username UK
        datetime created_at
    }

    REPORTS {
        int id PK
        int user_id FK
        string filename
        string diagnosis
        string status
        text message
        text source_text
        int completeness_score
        int initial_score
        string langfuse_trace_id
        string langfuse_parent_observation_id
        datetime created_at
    }

    SUGGESTIONS {
        int id PK
        int report_id FK
        string section
        text explanation
        text guideline_passage
        text source_url
        string action
        text target_text
        text suggested_text
        string decision
        datetime decided_at
    }

    AUDIT_LOGS {
        int id PK
        int report_id FK
        int suggestion_id FK
        string decision
        datetime decided_at
    }
```

### Applied Migrations

1. `cc7a5170229d_initial_schema.py`: Creates `users`, `reports`, `suggestions`, and `audit_logs` tables.
2. `a8b2c3d4e5f6_add_initial_score_and_actionable_fields.py`: Adds `initial_score` to `reports`, and `action`, `target_text`, and `suggested_text` to `suggestions`.

---

## Frontend Application

The user interface in `/frontend` is built with Next.js 14 (App Router) and HeroUI, providing a clean, noise-free clinical review experience with native dark and light mode theming.

### Application Pages

- `/` (`src/app/page.tsx`): Document upload portal. Features drag-and-drop file selection with client-side format and file-size validation, showing clear loading states and error notifications.
- `/reviews/[id]` (`src/app/reviews/[id]/page.tsx`): Dedicated clinician review workspace:
  - Header: Displays case metadata, extracted diagnosis, and a color-coded completeness badge.
  - Suggestion Cards: Granular cards displaying the gap section, recommended action (`add`, `modify`, `remove`), clinical explanation, and cited guideline passage. Clinicians can click **Accept** or **Ignore** to immediately update state via live `PATCH`.
  - Split-Screen Comparison: Side-by-side synchronized view presenting the original unedited summary on the left and the structured document on the right.
  - Modals:
    - Evidence Modal: View full guideline text and download official reference PDFs.
    - Preview & Export Modal: Toggle between PDF, DOCX, and TXT previews before downloading.
    - Audit Trail Modal: Displays an immutable history of every clinician decision with UTC timestamps.
- `/reviews` (`src/app/reviews/page.tsx`): Case management portal. Features live search, status filtering, score sorting, diagnosis grouping, and pagination.

---

## Installation and Setup

### Prerequisites

- **Python:** Version 3.11 or higher.
- **Node.js:** Version 20.x or 22.x LTS with `npm`.
- **Docker & Docker Compose:** Required for containerized execution.
- **Ollama:** Required for local inference when running outside Docker Compose.

### Environment Configuration

Create a `.env` file in the project root:

```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EVAL_EMBEDDING_MODEL=nomic-embed-text:v1.5

# Database Configuration (PostgreSQL in Docker, SQLite locally)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/clinical_discharge
# For local development without PostgreSQL, omit or use:
# DATABASE_URL=sqlite:///./clinical_discharge.db

# Optional Langfuse Observability (leaves PHI local)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# CORS Allowed Origins
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

For the frontend, create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Option A: Running with Docker Compose

The complete backend stack (FastAPI, PostgreSQL 16, Ollama, vector index, and migrations) can be started with a single command:

```bash
docker compose up
```

The container entrypoint (`docker/entrypoint.sh`):
1. Verifies PostgreSQL connectivity.
2. Builds the FAISS vector index from `knowledge_base/guidelines/`.
3. Applies Alembic migrations (`alembic upgrade head`).
4. Pulls the specified Ollama model (`llama3.2:3b`).
5. Launches the Uvicorn application server on port `8000`.

Start the frontend in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Access the applications:
- Frontend Web App: `http://localhost:3000`
- FastAPI REST API: `http://localhost:8000`
- Swagger Documentation: `http://localhost:8000/docs`

---

### Option B: Local Development Setup

#### 1. Setup Ollama

Ensure Ollama is installed and running locally:

```bash
ollama serve
ollama pull llama3.2:3b
ollama pull nomic-embed-text:v1.5
```

#### 2. Backend Setup

```bash
# Create and activate Python 3.11 virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# Install packaging tools and dependencies
pip install --upgrade pip "setuptools>=83.0.0"
pip install -e ".[dev,evaluation]"

# Apply database migrations
alembic upgrade head

# Ingest and index clinical guidelines into FAISS
python knowledge_base/ingest.py

# Launch FastAPI development server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Usage Instructions

1. **Submit Discharge Document:**
   - Navigate to `http://localhost:3000`.
   - Drag and drop or browse to select a discharge summary (PDF, DOCX, or TXT).
   - Click **Review Discharge Document**.
2. **Inspect Review Findings:**
   - The review workspace displays the identified diagnosis, calculated completeness score, and suggestion cards.
   - For each suggestion, review the recommended clinical addition, the explanation, and the cited guideline passage.
   - Click **View Evidence** on any card to view the authoritative source guideline.
3. **Accept or Ignore Suggestions:**
   - Click **Accept** to approve a recommendation, incorporating it into the final document under "Added on review".
   - Click **Ignore** to dismiss the recommendation.
   - Watch the completeness score update dynamically in real time.
4. **Preview and Export:**
   - Click **Export Document** to open the preview modal.
   - Switch between **PDF**, **DOCX**, and **TXT** tabs to inspect formatting.
   - Click **Download Final Document** to obtain the finalized clinical discharge summary and commit the action to the audit log.

---

## Sample Documents

Twelve realistic, synthetic clinical discharge summaries are provided in `sample_documents/` for testing and evaluation. None contain real patient information.

- **Asthma (`sample_documents/asthma/`):**
  - `01_asthma_nearly_complete.pdf`: Full documentation demonstrating a high completeness score.
  - `02_asthma_missing_followup_and_warning_signs.docx`: Missing revisit intervals and red flags.
  - `03_asthma_missing_medications_dosage.pdf`: Incomplete medication dosage instructions.
  - `04_asthma_partially_documented_instructions.txt`: Baseline inpatient slip lacking warning signs.
- **Diabetes (`sample_documents/diabetes/`):**
  - `05_type2_diabetes_nearly_complete.docx`: Comprehensive Type 2 diabetes regimen.
  - `06_type2_diabetes_missing_hypoglycemia_warning.pdf`: Lacks hypoglycemia warning signs.
  - `07_type2_diabetes_missing_medications_dosage.txt`: Missing oral hypoglycemic dosages.
  - `08_type1_diabetes_missing_warning_and_followup.docx`: Type 1 diabetes discharge lacking diabetic ketoacidosis red flags.
- **Hypertension (`sample_documents/hypertension/`):**
  - `09_hypertension_nearly_complete.pdf`: Complete Stage 2 hypertension summary.
  - `10_hypertension_missing_medications_and_warning.docx`: Omitted antihypertensive dosages.
  - `11_hypertension_missing_followup_and_lifestyle.pdf`: Missing lifestyle advice and follow-up.
- **Unsupported Condition (`sample_documents/unsupported_condition/`):**
  - `12_acute_appendicitis_unsupported_scope.pdf`: Surgical case used to verify the negative retrieval guardrail (`status: "no_match"`, zero suggestions generated).

---

## Testing and Verification

### Backend Test Suite

Run the full pytest suite:

```bash
pytest
```

Run golden determinism tests:

```bash
# Verify schema contracts and repeatability
pytest tests/golden -q

# Run live golden tests against local Ollama (requires live Ollama service)
RUN_LIVE_GOLDEN=1 pytest tests/golden -q
```

Run Ragas evaluation benchmarks:

```bash
python tests/eval/run_ragas.py
```

### Static Analysis and Security Audits

```bash
# Python linter
ruff check .

# Static type checker
mypy backend

# Security scanner (AST checks)
bandit -r backend

# Dependency vulnerability audit
pip-audit --skip-editable --ignore-vuln PYSEC-2026-2447 --ignore-vuln PYSEC-2026-3046
```

### Frontend Test Suite

```bash
cd frontend

# Run unit tests
npm test

# Run ESLint
npm run lint

# Validate production build
npm run build
```

---

## Verified Project Metrics

The following metrics reflect verified execution evidence from the project repository:

### Test Suite Execution Evidence

- **Backend Tests:** 45 total test cases collected across unit, integration, migration, formatting, and workflow modules.
  - **44 Passed, 1 Skipped** (live Ollama golden test skipped unless `RUN_LIVE_GOLDEN=1` is explicitly set).
- **Frontend Tests:** 10 test cases in `src/lib/api.test.ts`.
  - **10 Passed, 0 Failed** across API error normalization, query parameter serialization, multipart uploads, and status patch flows.
- **Alembic Migrations:** Verified bidirectional migration execution (`upgrade head` -> `downgrade base` -> `upgrade head`).

### Ragas Evaluation Scores (CI Enforced)

Tested against the evaluation set defined in `tests/eval/ragas_cases.json`:

| Metric | Measured Score | Minimum Required Floor | Status |
|---|---|---|---|
| **Context Precision** | 0.919 | 0.500 | Passed |
| **Faithfulness** | 1.000 | 0.500 | Passed |
| **Answer Relevancy** | 0.504 - 0.760 | 0.500 | Passed |

*Source: CI workflow runs and `STATUS.md` records.*

---

## Security Posture & Compliance

- **No PHI Crosses the Application Boundary:** Observability instruments metadata only. Raw clinical summaries, patient names, and extracted entities are not transmitted to third-party endpoints.
- **Strict Parameterized Queries:** All database transactions use SQLAlchemy ORM or parameterized statements, mitigating SQL injection risks.
- **Safe XML/HTML Parsing:** XML ingestion uses `defusedxml.ElementTree` to prevent XML entity expansion (Billion Laughs) and external entity injection (XXE).
- **Container Hardening:** The Docker image runs as an unprivileged user (`appuser`, UID `10001`) with no root privileges.
- **Input Sanitization:** Binary file uploads are checked for file size (5 MB limit), format extensions, and control character sanitization.
- **Dependency Audit Policy:** Two advisories are explicitly tracked in `SECURITY_NOTES.md`:
  - `PYSEC-2026-2447` (`diskcache` 5.6.3): Relates to optional DiskCache deserialization. DiskCache is not used or instantiated by this application.
  - `PYSEC-2026-3046` (`ragas` 0.4.3): Relates to multimodal media resolvers. The test runner only exercises pure text evaluation metrics.

---

## Current Implementation Status

| Milestone / Component | Planned Scope | Current Status | Verification Source |
|---|---|---|---|
| **Phase 0: Scaffold & Setup** | Project structure, CI, Ollama integration | Complete | Merged to `main` |
| **Phase 1: Guideline Sourcing** | Curate national clinical guidelines with metadata | Complete | 7 documents in `knowledge_base/` |
| **Phase 2: Ingestion & Indexing** | FAISS vector store with idempotent updates | Complete | `test_ingest.py` |
| **Phase 3: Extraction Pipeline** | Multi-format parser (PDF/DOCX/TXT), temp=0.0 | Complete | `test_extraction.py` |
| **Phase 4: RAG Retrieval** | LangGraph retrieval and section comparison | Complete | `test_workflow.py` |
| **Phase 5: Completeness Scoring** | Algorithmic scoring, guardrails, golden cases | Complete | `test_golden_scoring.py` |
| **Phase 6: Persistence & Audit** | PostgreSQL schema, live PATCH API, audit trail | Complete | `test_persistence.py` |
| **Phase 7: Layout Structuring** | Lossless structuring, content preservation check | Complete | `test_formatting.py` |
| **Phase 8: Observability & Evals** | Langfuse metadata tracing, Ragas evaluation | Complete | `run_ragas.py`, CI workflow |
| **Phase 9: Containerization** | Alembic migrations, Dockerfile, Docker Compose | Complete | `test_migrations.py`, Docker |
| **Phase 10: Clinical Frontend** | Next.js 14 + HeroUI review workspace | Complete | `frontend/`, `npm test` |
| **Phase 11: Cloud Deployment** | Cloud host deployment (Render/Railway), Cloud LLM swap | Planned | Deferred to future scope |

---

## Limitations and Known Constraints

1. **Curated Clinical Scope:** The knowledge base currently covers three primary non-communicable conditions (Asthma, Diabetes Mellitus, and Hypertension). Other clinical conditions correctly trigger the `no_match` guardrail.
2. **Local Model Dependency:** Local execution requires an active Ollama instance with `llama3.2:3b` pulled. When Ollama is unavailable, the backend falls back to deterministic rule-based recommendations.
3. **Single Tenant Review Context:** The persistence model currently utilizes a default user identifier (`local-doctor`) suitable for standalone hospital deployment. Multi-tenant role-based access control (RBAC) is planned for future iterations.
4. **No Electronic Health Record (EHR) Integration:** The current system operates on uploaded summary files and does not connect directly to live hospital EHR or HL7/FHIR systems.

---

## Future Roadmap

- **Phase 11 Cloud Provider Swap:** Validate switching LLM provider from Ollama to cloud models (e.g., Google Gemini) via `backend/llm/provider.py` without business logic modification.
- **Guideline Expansion:** Ingest additional clinical specialties, including cardiology, gastroenterology, and infectious disease management.
- **FHIR / HL7 Ingestion:** Support direct ingestion of HL7 FHIR Composition resources from hospital information systems.
- **Drug-Drug Interaction Verification:** Introduce clinical pharmacology interaction screening alongside guideline documentation gap detection.

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feature/clinical-enhancement`).
2. Implement code changes adhering to the established rules:
   - Ensure all LLM judgment calls maintain a sampling temperature of `0.0`.
   - Never send raw patient text or clinical passages to observability traces.
   - Provide unit tests for both success and failure execution paths.
3. Ensure all quality gates pass:
   ```bash
   ruff check .
   mypy backend
   pytest
   cd frontend && npm test && npm run lint
   ```
4. Submit a pull request with an explicit description of changes and test results.

---

## License and Attribution

This project is developed as an academic engineering design project.

### Clinical Guideline Attribution

- **Indian Council of Medical Research (ICMR):** Standard Treatment Workflows (STWs) and Clinical Guidelines for Asthma, Type 1 Diabetes, Type 2 Diabetes, and Hypertension in Adults.
- **Ministry of Health and Family Welfare (MoHFW) / National Health Mission (NHM):** Standard Treatment Guidelines for Primary Hypertension in Adults in India.
- **Lung India:** Guidelines for Diagnosis and Management of Bronchial Asthma (Indian Chest Society / National College of Chest Physicians).

*Notice: In accordance with publication notices from original issuing authorities, clinical guidelines included within the knowledge base are utilized for reference, evaluation, and educational validation. Public distribution or redistribution should confirm specific permissions with the respective publisher or issuing department.*
