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

interface DocumentComparisonProps {
  originalText: string;
  structuredText: string;
  acceptedCount: number;
  isLoadingPreview: boolean;
  onRefreshPreview?: () => void;
}

export function DocumentComparison({
  originalText,
  structuredText,
  acceptedCount,
  isLoadingPreview,
  onRefreshPreview,
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
              {content}
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
