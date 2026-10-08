/**
 * TypeScript contracts mirroring the backend FastAPI / Pydantic schemas.
 */

export type DocumentFormat = "pdf" | "docx" | "txt";

export type SuggestionDecision = "accepted" | "ignored";
export type SuggestionStatus = "pending" | "accepted" | "rejected";
export type AuditDecision = "accepted" | "ignored" | "exported";

export interface DischargeExtraction {
  diagnosis: string;
  medications: string[];
  follow_up_requirements: string[];
  warning_signs: string[];
}

export interface ExtractionResponse {
  filename: string;
  content_type: string | null;
  extraction: DischargeExtraction;
}

export interface GuidelineMatch {
  diagnosis: string;
  diagnosis_slug: string;
  source_url: string;
  passage: string;
  similarity: number;
  document_title?: string | null;
  document_filename?: string | null;
  source_name?: string | null;
  guideline_document_url?: string | null;
}

export interface ComparisonItem {
  section: string;
  status: string;
  extracted_values: string[];
  guideline_passage: string;
}

export type SuggestionAction = "add" | "modify" | "remove";

export interface Suggestion {
  section: string;
  explanation: string;
  guideline_passage: string;
  source_url: string;
  action?: SuggestionAction;
  target_text?: string;
  suggested_text?: string;
  suggestion_id?: number | null;
  decision?: SuggestionDecision | null;
  document_title?: string | null;
  document_filename?: string | null;
  source_name?: string | null;
  guideline_document_url?: string | null;
}

export interface ReviewResponse {
  diagnosis: string;
  status: string;
  message: string;
  guideline?: GuidelineMatch | null;
  comparisons: ComparisonItem[];
  completeness_score?: number | null;
  suggestions: Suggestion[];
  report_id?: number | null;
  source_text?: string;
}

export interface SuggestionStatusRequest {
  status: SuggestionStatus;
}

export interface AuditLogResponse {
  id: number;
  suggestion_id: number | null;
  decision: AuditDecision;
  decided_at: string;
}

export interface PersistedSuggestion {
  id: number;
  section: string;
  explanation: string;
  guideline_passage: string;
  source_url: string;
  action?: SuggestionAction;
  target_text?: string;
  suggested_text?: string;
  status: SuggestionStatus;
  decision?: SuggestionDecision | null;
  decided_at?: string | null;
  document_title?: string | null;
  document_filename?: string | null;
  source_name?: string | null;
  guideline_document_url?: string | null;
}

export interface PersistedReportResponse {
  id: number;
  filename: string;
  diagnosis: string;
  status: string;
  message: string;
  source_text: string;
  completeness_score?: number | null;
  created_at: string;
  suggestions: PersistedSuggestion[];
  audit_logs: AuditLogResponse[];
}

export interface PreviewResponse {
  report_id: number;
  format: DocumentFormat;
  content: string;
  exported: boolean;
}

export interface ReviewHistoryResponse {
  reviews: PersistedReportResponse[];
  total: number;
  offset: number;
  limit: number;
  groups?: Record<string, number[]> | null;
}

export interface HistoryQueryParams {
  search?: string;
  status?: string;
  sort?: "newest" | "oldest" | "score";
  group_by?: "diagnosis" | "status";
  offset?: number;
  limit?: number;
}
