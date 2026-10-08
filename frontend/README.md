# AI Clinical Discharge Intelligence System — Frontend

A clinical review frontend built with Next.js 15 (App Router), React 19, TypeScript, and HeroUI.

## Overview
The frontend provides a clinical review interface for hospital discharge summaries:
- **Upload & Validation:** Drag-and-drop or select PDF, DOCX, and TXT files with client-side file type and size checking.
- **Review Workspace:** Side-by-side split screen showing the original discharge summary alongside the structured final document.
- **Granular Review:** Interactive guideline suggestion cards allowing clinicians to individually Accept or Ignore recommendations via live `PATCH` requests.
- **Authoritative Preview:** Live layout preview matching the backend structuring and accepted suggestions before export.
- **Multi-Format Export:** Commit and download finalized discharge summaries in PDF, DOCX, or TXT formats with audit trail recording.
- **Review History:** Searchable, filterable, sortable, groupable, and paginated review log with persistent status tracking.
- **Theme Support:** Native HeroUI light and dark modes with system preference synchronization.

## Architecture
- `src/app/` — Next.js App Router pages:
  - `page.tsx` — Upload and new review interface.
  - `reviews/page.tsx` — Searchable and filterable history view.
  - `reviews/[id]/page.tsx` — Dedicated review workspace with live split-view.
- `src/components/` — Reusable HeroUI-based components:
  - `upload/` — Document dropzone and format validation.
  - `review/` — Suggestion cards, split-screen document viewer, preview modal.
  - `history/` — History table, filters, and pagination.
  - `layout/` — Navbar, theme switcher, and application shell.
- `src/lib/api.ts` — Typed client interfacing with FastAPI backend.
- `src/types/` — TypeScript interfaces matching backend Pydantic schemas.

## Commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run unit tests
npm test

# Lint code
npm run lint

# Build production bundle
npm run build
```

## Environment Configuration
Set in `.env.local` or environment:
- `NEXT_PUBLIC_API_URL` — Backend API base URL (defaults to `http://localhost:8000`).
