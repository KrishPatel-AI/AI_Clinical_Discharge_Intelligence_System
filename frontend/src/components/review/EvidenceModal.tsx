"use client";

import React from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Chip,
  Link,
  Divider,
} from "@heroui/react";
import { ExternalLink, BookOpen, Quote, FileText, ArrowRight, ShieldCheck } from "lucide-react";
import { PersistedSuggestion } from "@/types/api";
import { getGuidelineDocumentUrl } from "@/lib/api";

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  suggestion: PersistedSuggestion | null;
}

export function EvidenceModal({
  isOpen,
  onClose,
  suggestion,
}: EvidenceModalProps) {
  if (!suggestion) return null;

  const docUrl = suggestion.guideline_document_url
    ? getGuidelineDocumentUrl(suggestion.guideline_document_url)
    : null;

  const actionColor =
    suggestion.action === "modify"
      ? "warning"
      : suggestion.action === "remove"
      ? "danger"
      : "primary";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
      scrollBehavior="inside"
      backdrop="blur"
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1 pb-2">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <span className="text-base font-semibold text-foreground">
              Clinical Guideline Evidence & Traceability
            </span>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <Chip size="sm" variant="flat" color="primary">
              {suggestion.section}
            </Chip>
            {suggestion.action && (
              <Chip size="sm" variant="flat" color={actionColor} className="uppercase text-[10px]">
                {suggestion.action}
              </Chip>
            )}
            <span className="text-xs text-foreground-400">
              Suggestion #{suggestion.id}
            </span>
          </div>
        </ModalHeader>

        <Divider />

        <ModalBody className="py-4 space-y-4">
          {/* Sourced Guideline Document */}
          <div className="p-3 rounded-medium bg-primary-50/40 dark:bg-primary-950/20 border border-primary-200/60 dark:border-primary-800/40 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary shrink-0" />
                <span className="text-xs font-semibold uppercase tracking-wider text-primary-700 dark:text-primary-300">
                  Authoritative Sourced Guideline
                </span>
              </div>
              {docUrl && (
                <Button
                  as="a"
                  href={docUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  size="sm"
                  color="primary"
                  variant="flat"
                  className="text-xs h-7 font-medium"
                  endContent={<ExternalLink className="w-3 h-3" />}
                >
                  Open Original Document (PDF)
                </Button>
              )}
            </div>

            <div>
              <p className="text-sm font-semibold text-foreground">
                {suggestion.document_title || "Official Standard Treatment Guideline"}
              </p>
              {suggestion.source_name && (
                <p className="text-xs text-foreground-500 mt-0.5">
                  Authority: {suggestion.source_name}
                </p>
              )}
            </div>

            {suggestion.source_url && (
              <div className="flex items-center gap-1.5 text-[11px] text-foreground-400 pt-0.5">
                <ShieldCheck className="w-3.5 h-3.5 text-success-600 shrink-0" />
                <span className="truncate">
                  Source verification:{" "}
                  <Link
                    href={suggestion.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    isExternal
                    className="text-[11px] text-primary hover:underline"
                  >
                    {suggestion.source_url}
                  </Link>
                </span>
              </div>
            )}
          </div>

          {/* AI Clinical Recommendation & Rationale */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground-400">
              Clinical Recommendation & Rationale
            </span>
            <div className="p-3 rounded-medium bg-default-50 border border-default-200 space-y-2">
              <p className="text-sm text-foreground-800 leading-relaxed font-medium">
                {suggestion.suggested_text || suggestion.explanation}
              </p>
              {suggestion.suggested_text && suggestion.explanation && (
                <p className="text-xs text-foreground-600 leading-relaxed pt-1 border-t border-default-200">
                  <span className="font-semibold text-foreground-700">Rationale: </span>
                  {suggestion.explanation}
                </p>
              )}
            </div>
          </div>

          {/* Relationship to Discharge Text */}
          {suggestion.target_text && (
            <div className="space-y-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-foreground-400">
                Target Section in Discharge Document
              </span>
              <div className="flex items-start gap-2 p-2.5 rounded-medium bg-default-100/70 border border-default-200 text-xs text-foreground-700">
                <ArrowRight className="w-3.5 h-3.5 text-foreground-400 mt-0.5 shrink-0" />
                <div>
                  <span className="font-semibold text-foreground-900">Target context: </span>
                  <span className="italic font-mono">{suggestion.target_text}</span>
                </div>
              </div>
            </div>
          )}

          {/* Authoritative Guideline Passage (RAG Evidence) */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-foreground-400">
              <Quote className="w-3.5 h-3.5 text-primary" />
              <span>Retrieved Guideline Passage (Evidence Grounding)</span>
            </div>
            <div className="p-3.5 rounded-medium bg-default-100/70 border border-default-200 text-xs sm:text-sm font-mono text-foreground-800 leading-relaxed whitespace-pre-wrap select-text max-h-56 overflow-y-auto">
              {suggestion.guideline_passage}
            </div>
          </div>
        </ModalBody>

        <Divider />

        <ModalFooter>
          {docUrl && (
            <Button
              as="a"
              href={docUrl}
              target="_blank"
              rel="noopener noreferrer"
              color="primary"
              variant="flat"
              size="sm"
              endContent={<ExternalLink className="w-3 h-3" />}
            >
              Open PDF
            </Button>
          )}
          <Button color="default" variant="flat" size="sm" onPress={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
