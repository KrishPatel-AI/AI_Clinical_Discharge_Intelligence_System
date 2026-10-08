"use client";

import React, { useState } from "react";
import {
  Card,
  CardBody,
  CardHeader,
  Tabs,
  Tab,
  Button,
  Chip,
  Tooltip,
} from "@heroui/react";
import { Copy, Check, FileText, RefreshCw } from "lucide-react";

import { PersistedSuggestion } from "@/types/api";

interface DocumentComparisonProps {
  originalText: string;
  structuredText: string;
  acceptedCount: number;
  isLoadingPreview: boolean;
  onRefreshPreview?: () => void;
  suggestions?: PersistedSuggestion[];
}

export function DocumentComparison({
  originalText,
  structuredText,
  acceptedCount,
  isLoadingPreview,
  onRefreshPreview,
  suggestions = [],
}: DocumentComparisonProps) {
  const [copiedOriginal, setCopiedOriginal] = useState(false);
  const [copiedStructured, setCopiedStructured] = useState(false);

  const handleCopy = (text: string, isOriginal: boolean) => {
    navigator.clipboard.writeText(text);
    if (isOriginal) {
      setCopiedOriginal(true);
      setTimeout(() => setCopiedOriginal(false), 2000);
    } else {
      setCopiedStructured(true);
      setTimeout(() => setCopiedStructured(false), 2000);
    }
  };

  const renderHighlightedOriginal = (text: string) => {
    if (!text || !suggestions || suggestions.length === 0) {
      return text;
    }

    const targets = suggestions
      .filter((s) => s.target_text && s.target_text.trim().length > 2)
      .map((s) => {
        const rawTarget = s.target_text!.trim();
        const cleanTarget = rawTarget.replace(/^["']|["']$/g, "").trim();
        const status =
          s.status === "accepted" || s.decision === "accepted"
            ? "accepted"
            : s.status === "rejected" || s.decision === "ignored"
            ? "rejected"
            : "pending";
        return {
          id: s.id,
          section: s.section,
          target: cleanTarget,
          status,
        };
      })
      .filter((item) => text.toLowerCase().includes(item.target.toLowerCase()));

    if (targets.length === 0) {
      return text;
    }

    targets.sort((a, b) => b.target.length - a.target.length);

    const escaped = targets.map((t) =>
      t.target.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    );
    const regex = new RegExp(`(${escaped.join("|")})`, "gi");

    const parts = text.split(regex);
    return parts.map((part, index) => {
      const match = targets.find(
        (t) => t.target.toLowerCase() === part.toLowerCase()
      );
      if (!match) {
        return <React.Fragment key={index}>{part}</React.Fragment>;
      }

      const styleClass =
        match.status === "accepted"
          ? "bg-success-100 dark:bg-success-950/60 text-success-900 dark:text-success-200 border-b-2 border-success-500 font-semibold px-1 py-0.5 rounded-xs"
          : match.status === "rejected"
          ? "bg-danger-50 dark:bg-danger-950/40 text-danger-800 dark:text-danger-300 line-through px-1 py-0.5 rounded-xs opacity-75"
          : "bg-warning-100 dark:bg-warning-950/60 text-warning-900 dark:text-warning-200 border-b-2 border-warning-400 font-semibold px-1 py-0.5 rounded-xs";

      return (
        <mark
          key={index}
          className={`${styleClass} transition-colors`}
          title={`[${match.status.toUpperCase()}] Suggestion #${match.id}: ${match.section}`}
        >
          {part}
        </mark>
      );
    });
  };

  const renderHighlightedReviewed = (text: string) => {
    if (!text) return text;
    const lines = text.split("\n");
    let inAddedOnReview = false;

    return lines.map((line, idx) => {
      if (line.includes("Added on review")) {
        inAddedOnReview = true;
        return (
          <div key={idx} className="font-semibold text-primary mt-2">
            {line}
          </div>
        );
      }
      if (inAddedOnReview && line.startsWith("- ")) {
        return (
          <div
            key={idx}
            className="bg-success-100/70 dark:bg-success-950/40 text-success-900 dark:text-success-200 border-l-3 border-success-500 pl-2 my-1 py-0.5 rounded-xs font-medium"
            title="Clinically approved suggestion addition"
          >
            {line}
          </div>
        );
      }
      if (inAddedOnReview && line.trim() && !line.startsWith("-")) {
        inAddedOnReview = false;
      }
      return (
        <div key={idx} className="min-h-[1.25rem]">
          {line}
        </div>
      );
    });
  };

  const renderDocumentView = (
    content: string,
    title: string,
    subtitle: string,
    isOriginal: boolean
  ) => {
    const isCopied = isOriginal ? copiedOriginal : copiedStructured;

    return (
      <Card className="h-full border border-default-200 dark:border-default-100 shadow-none flex flex-col">
        <CardHeader className="py-3 px-4 border-b border-default-200 dark:border-default-100 flex items-center justify-between bg-default-50/50">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-foreground-500" />
            <div>
              <p className="text-xs font-semibold text-foreground">{title}</p>
              <p className="text-[11px] text-foreground-400">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!isOriginal && onRefreshPreview && (
              <Tooltip content="Refresh preview from server">
                <Button
                  isIconOnly
                  size="sm"
                  variant="light"
                  isLoading={isLoadingPreview}
                  onPress={onRefreshPreview}
                  aria-label="Refresh preview"
                >
                  <RefreshCw className="w-3.5 h-3.5 text-foreground-500" />
                </Button>
              </Tooltip>
            )}
            <Tooltip content={isCopied ? "Copied" : "Copy to clipboard"}>
              <Button
                size="sm"
                variant="flat"
                color="default"
                className="text-xs h-7"
                startContent={
                  isCopied ? (
                    <Check className="w-3 h-3 text-success" />
                  ) : (
                    <Copy className="w-3 h-3 text-foreground-500" />
                  )
                }
                onPress={() => handleCopy(content, isOriginal)}
              >
                {isCopied ? "Copied" : "Copy"}
              </Button>
            </Tooltip>
          </div>
        </CardHeader>

        <CardBody className="p-4 flex-1 overflow-auto bg-background">
          {content ? (
            <div className="text-xs sm:text-sm font-mono text-foreground-800 leading-relaxed whitespace-pre-wrap select-text">
              {isOriginal
                ? renderHighlightedOriginal(content)
                : renderHighlightedReviewed(content)}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs text-foreground-400 italic">
              Document content is currently unavailable.
            </div>
          )}
        </CardBody>
      </Card>
    );
  };

  return (
    <div className="w-full space-y-3">
      {/* Mobile/Tablet tabbed interface */}
      <div className="lg:hidden">
        <Tabs aria-label="Document view options" fullWidth size="sm" color="primary">
          <Tab
            key="reviewed"
            title={
              <div className="flex items-center gap-2">
                <span>Final Reviewed</span>
                {acceptedCount > 0 && (
                  <Chip size="sm" color="success" variant="flat" className="h-4 text-[10px] px-1">
                    +{acceptedCount}
                  </Chip>
                )}
              </div>
            }
          >
            <div className="pt-2 min-h-[400px]">
              {renderDocumentView(
                structuredText || originalText,
                "Reviewed Document",
                acceptedCount > 0
                  ? `Structured with ${acceptedCount} accepted addition(s)`
                  : "Structured layout without AI additions",
                false
              )}
            </div>
          </Tab>
          <Tab key="original" title="Original Document">
            <div className="pt-2 min-h-[400px]">
              {renderDocumentView(
                originalText,
                "Original Document",
                "Source text as uploaded by user",
                true
              )}
            </div>
          </Tab>
        </Tabs>
      </div>

      {/* Desktop Side-by-Side Split View */}
      <div className="hidden lg:grid lg:grid-cols-2 gap-4 h-[640px]">
        {renderDocumentView(
          originalText,
          "Original Document",
          "Source text as uploaded by user",
          true
        )}
        {renderDocumentView(
          structuredText || originalText,
          "Reviewed Document (Live Preview)",
          acceptedCount > 0
            ? `Structured layout with ${acceptedCount} accepted addition(s)`
            : "Structured layout (no AI additions accepted)",
          false
        )}
      </div>
    </div>
  );
}
