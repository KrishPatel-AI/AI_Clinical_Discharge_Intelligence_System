"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardBody,
  Button,
  Chip,
  Tabs,
  Tab,
  Alert,
  Skeleton,
} from "@heroui/react";
import {
  Download,
  History,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import {
  PersistedReportResponse,
  PersistedSuggestion,
  SuggestionStatus,
} from "@/types/api";
import {
  getReview,
  updateSuggestionStatus,
  getPreview,
  ApiError,
} from "@/lib/api";
import { CompletenessBadge } from "./CompletenessBadge";
import { SuggestionCard } from "./SuggestionCard";
import { EvidenceModal } from "./EvidenceModal";
import { DocumentComparison } from "./DocumentComparison";
import { ExportModal } from "./ExportModal";
import { AuditHistoryModal } from "./AuditHistoryModal";

interface ReviewWorkspaceProps {
  reportId: number;
}

export function ReviewWorkspace({ reportId }: ReviewWorkspaceProps) {
  const router = useRouter();

  const [report, setReport] = useState<PersistedReportResponse | null>(null);
  const [structuredPreview, setStructuredPreview] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [updatingSuggestionId, setUpdatingSuggestionId] = useState<number | null>(
    null
  );
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // Filter state for suggestions
  const [suggestionFilter, setSuggestionFilter] = useState<
    "all" | "pending" | "accepted" | "rejected"
  >("all");

  // Modals state
  const [activeEvidenceSuggestion, setActiveEvidenceSuggestion] =
    useState<PersistedSuggestion | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  const fetchStructuredPreview = useCallback(async (id: number) => {
    setIsLoadingPreview(true);
    try {
      const preview = await getPreview(id, "txt");
      setStructuredPreview(preview.content);
    } catch {
      // preview error non-blocking
    } finally {
      setIsLoadingPreview(false);
    }
  }, []);

  const loadReportData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getReview(reportId);
      setReport(data);
      await fetchStructuredPreview(reportId);
    } catch (err) {
      if (err instanceof ApiError) {
        setLoadError(err.message);
      } else {
        setLoadError(
          "Failed to load the requested review report. Verify backend connectivity."
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [reportId, fetchStructuredPreview]);

  useEffect(() => {
    loadReportData();
  }, [loadReportData]);

  const handleUpdateSuggestion = async (
    suggestionId: number,
    status: SuggestionStatus
  ) => {
    setUpdatingSuggestionId(suggestionId);
    try {
      const updatedReport = await updateSuggestionStatus(
        reportId,
        suggestionId,
        status
      );
      setReport(updatedReport);
      // Synchronize structured preview immediately
      await fetchStructuredPreview(reportId);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Failed to update suggestion status.";
      alert(message);
    } finally {
      setUpdatingSuggestionId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-24 rounded-medium" />
          <Skeleton className="h-8 w-64 rounded-medium" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-28 rounded-large" />
          <Skeleton className="h-28 rounded-large" />
          <Skeleton className="h-28 rounded-large" />
        </div>
        <Skeleton className="h-96 rounded-large" />
      </div>
    );
  }

  if (loadError || !report) {
    return (
      <div className="w-full max-w-xl mx-auto py-12 space-y-6 text-center">
        <Alert
          color="danger"
          variant="flat"
          title="Review Not Found or Error"
          description={
            loadError || `Review report #${reportId} could not be loaded.`
          }
          startContent={<AlertCircle className="w-5 h-5 shrink-0" />}
        />
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="flat"
            color="default"
            startContent={<ArrowLeft className="w-4 h-4" />}
            onPress={() => router.push("/reviews")}
          >
            Back to History
          </Button>
          <Button
            variant="solid"
            color="primary"
            startContent={<RefreshCw className="w-4 h-4" />}
            onPress={loadReportData}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const suggestions = report.suggestions || [];
  const acceptedSuggestions = suggestions.filter(
    (s) => s.status === "accepted" || s.decision === "accepted"
  );
  const rejectedSuggestions = suggestions.filter(
    (s) => s.status === "rejected" || s.decision === "ignored"
  );
  const pendingSuggestions = suggestions.filter(
    (s) => s.status === "pending" && !s.decision
  );

  const filteredSuggestions = suggestions.filter((s) => {
    if (suggestionFilter === "pending")
      return s.status === "pending" && !s.decision;
    if (suggestionFilter === "accepted")
      return s.status === "accepted" || s.decision === "accepted";
    if (suggestionFilter === "rejected")
      return s.status === "rejected" || s.decision === "ignored";
    return true;
  });

  const isNoMatch = report.status === "no_match";

  return (
    <div className="w-full space-y-6">
      {/* Top Header / Context Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-default-200 dark:border-default-100">
        <div className="flex items-center gap-3">
          <Button
            isIconOnly
            size="sm"
            variant="light"
            aria-label="Back to history"
            onPress={() => router.push("/reviews")}
          >
            <ArrowLeft className="w-4 h-4 text-foreground-500" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                {report.filename}
              </h1>
              <Chip size="sm" variant="flat" color="default" className="text-xs">
                #{report.id}
              </Chip>
            </div>
            <p className="text-xs text-foreground-400">
              Created: {new Date(report.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="flat"
            color="default"
            startContent={<History className="w-3.5 h-3.5" />}
            onPress={() => setIsAuditModalOpen(true)}
          >
            Audit Log ({report.audit_logs?.length || 0})
          </Button>

          <Button
            size="sm"
            color="primary"
            variant="solid"
            startContent={<Download className="w-3.5 h-3.5" />}
            onPress={() => setIsExportModalOpen(true)}
          >
            Preview & Export
          </Button>
        </div>
      </div>

      {/* Overview Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Diagnosis & Guideline Match */}
        <Card className="border border-default-200 dark:border-default-100 shadow-none bg-default-50/50">
          <CardBody className="p-4 space-y-1">
            <span className="text-xs font-semibold text-foreground-400 uppercase tracking-wider">
              Diagnosed Condition
            </span>
            <p className="text-base font-semibold text-foreground">
              {report.diagnosis || "Unspecified Diagnosis"}
            </p>
            <div className="pt-1 flex items-center gap-2">
              {isNoMatch ? (
                <Chip
                  size="sm"
                  color="default"
                  variant="flat"
                  startContent={<HelpCircle className="w-3.5 h-3.5" />}
                >
                  No Matching Guideline
                </Chip>
              ) : (
                <Chip
                  size="sm"
                  color="success"
                  variant="flat"
                  startContent={<CheckCircle2 className="w-3.5 h-3.5" />}
                >
                  Clinical Guideline Matched
                </Chip>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Completeness Score */}
        <CompletenessBadge
          score={report.completeness_score}
          status={report.status}
        />

        {/* Suggestion Summary */}
        <Card className="border border-default-200 dark:border-default-100 shadow-none bg-default-50/50">
          <CardBody className="p-4 space-y-1">
            <span className="text-xs font-semibold text-foreground-400 uppercase tracking-wider">
              Recommendations Review
            </span>
            <div className="flex items-center gap-2 text-base font-semibold text-foreground">
              <span>{suggestions.length} Recommendations</span>
            </div>
            <div className="pt-1 flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-success font-medium">
                {acceptedSuggestions.length} Accepted
              </span>
              <span>•</span>
              <span className="text-danger font-medium">
                {rejectedSuggestions.length} Ignored
              </span>
              <span>•</span>
              <span className="text-warning-600 font-medium">
                {pendingSuggestions.length} Pending
              </span>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* No Guideline Match State Notice */}
      {isNoMatch && (
        <Alert
          color="default"
          variant="flat"
          title="Clinical Guideline Not Found"
          description={`The system does not have an indexed clinical guideline matching "${report.diagnosis}". As an advisory safety guardrail, ungrounded recommendations are suppressed. You can still inspect the original discharge document, review structured formatting, and export.`}
          startContent={<HelpCircle className="w-5 h-5 text-foreground-500 shrink-0" />}
        />
      )}

      {/* Main Review Section: Split into Suggestions List & Document Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Suggestions List (or notice if no_match) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <h2 className="text-base font-semibold text-foreground">
              Guideline Recommendations
            </h2>
            <div className="flex items-center gap-1">
              <Tabs
                size="sm"
                variant="light"
                selectedKey={suggestionFilter}
                onSelectionChange={(key) =>
                  setSuggestionFilter(
                    key as "all" | "pending" | "accepted" | "rejected"
                  )
                }
              >
                <Tab key="all" title={`All (${suggestions.length})`} />
                <Tab key="pending" title={`Pending (${pendingSuggestions.length})`} />
                <Tab key="accepted" title={`Accepted (${acceptedSuggestions.length})`} />
                <Tab key="rejected" title={`Ignored (${rejectedSuggestions.length})`} />
              </Tabs>
            </div>
          </div>

          {suggestions.length === 0 ? (
            <div className="p-8 text-center rounded-medium bg-default-50 border border-default-200 text-xs text-foreground-400 space-y-1">
              <p className="font-medium text-foreground-600">
                {isNoMatch
                  ? "No recommendations generated."
                  : "No guideline gaps identified."}
              </p>
              <p>
                {isNoMatch
                  ? "Ungrounded suggestions are withheld for unindexed diagnoses."
                  : "The discharge document comprehensively covers the matched guideline requirements."}
              </p>
            </div>
          ) : filteredSuggestions.length === 0 ? (
            <div className="p-6 text-center rounded-medium bg-default-50 border border-default-200 text-xs text-foreground-400">
              No recommendations match the selected filter ({suggestionFilter}).
            </div>
          ) : (
            <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
              {filteredSuggestions.map((suggestion) => (
                <SuggestionCard
                  key={suggestion.id}
                  suggestion={suggestion}
                  onUpdateStatus={handleUpdateSuggestion}
                  onViewEvidence={setActiveEvidenceSuggestion}
                  isUpdating={updatingSuggestionId === suggestion.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Original vs Structured Document Comparison */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <h2 className="text-base font-semibold text-foreground">
              Document Comparison
            </h2>
            <span className="text-xs text-foreground-400">
              Live Structured Synchronization
            </span>
          </div>

          <DocumentComparison
            originalText={report.source_text || ""}
            structuredText={structuredPreview}
            acceptedCount={acceptedSuggestions.length}
            isLoadingPreview={isLoadingPreview}
            onRefreshPreview={() => fetchStructuredPreview(report.id)}
          />
        </div>
      </div>

      {/* Evidence Modal */}
      <EvidenceModal
        isOpen={!!activeEvidenceSuggestion}
        onClose={() => setActiveEvidenceSuggestion(null)}
        suggestion={activeEvidenceSuggestion}
      />

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportId={report.id}
        filename={report.filename}
        onExportSuccess={loadReportData}
      />

      {/* Audit History Modal */}
      <AuditHistoryModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        auditLogs={report.audit_logs || []}
        reportId={report.id}
      />
    </div>
  );
}
