"use client";

import React, { useState, useEffect } from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  RadioGroup,
  Radio,
  Progress,
  Alert,
  Divider,
} from "@heroui/react";
import { Download, CheckCircle2, AlertCircle, Eye } from "lucide-react";
import { DocumentFormat } from "@/types/api";
import { getPreview, exportReview, ApiError } from "@/lib/api";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportId: number;
  filename: string;
  onExportSuccess?: () => void;
}

export function ExportModal({
  isOpen,
  onClose,
  reportId,
  filename,
  onExportSuccess,
}: ExportModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<DocumentFormat>("pdf");
  const [previewContent, setPreviewContent] = useState<string>("");
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);

  // Load preview whenever modal opens or format changes
  useEffect(() => {
    if (!isOpen) {
      setExportSuccess(false);
      setExportError(null);
      return;
    }

    let isMounted = true;
    const fetchPreview = async () => {
      setIsLoadingPreview(true);
      setPreviewError(null);
      try {
        const preview = await getPreview(reportId, selectedFormat);
        if (isMounted) {
          setPreviewContent(preview.content);
        }
      } catch (err) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setPreviewError(err.message);
          } else {
            setPreviewError("Failed to fetch export preview.");
          }
        }
      } finally {
        if (isMounted) setIsLoadingPreview(false);
      }
    };

    fetchPreview();
    return () => {
      isMounted = false;
    };
  }, [isOpen, reportId, selectedFormat]);

  const handleExport = async () => {
    setIsExporting(true);
    setExportError(null);
    try {
      const { blob, filename: downloadFilename } = await exportReview(
        reportId,
        selectedFormat
      );

      // Trigger browser file download
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = downloadFilename;
      document.body.appendChild(anchor);
      anchor.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(anchor);

      setExportSuccess(true);
      if (onExportSuccess) {
        onExportSuccess();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setExportError(err.message);
      } else {
        setExportError("Failed to export discharge summary document.");
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="3xl"
      scrollBehavior="inside"
      backdrop="blur"
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1 pb-2">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-primary" />
            <span className="text-base font-semibold text-foreground">
              Preview & Export: {filename}
            </span>
          </div>
          <p className="text-xs text-foreground-400 font-normal">
            Review the final structured document before exporting. Export records
            an audit event in the system.
          </p>
        </ModalHeader>

        <Divider />

        <ModalBody className="py-4 space-y-4">
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground-500">
              Select Output Format
            </span>
            <RadioGroup
              orientation="horizontal"
              value={selectedFormat}
              onValueChange={(val) => setSelectedFormat(val as DocumentFormat)}
              isDisabled={isExporting}
              className="gap-6"
            >
              <Radio value="pdf" description="Standard clinical PDF format">
                PDF
              </Radio>
              <Radio value="docx" description="Editable Word document">
                DOCX
              </Radio>
              <Radio value="txt" description="Plain structured text">
                TXT
              </Radio>
            </RadioGroup>
          </div>

          <Divider />

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-foreground-500">
                <Eye className="w-3.5 h-3.5" />
                <span>Export Preview ({selectedFormat.toUpperCase()})</span>
              </div>
              <span className="text-xs text-foreground-400">
                Includes original content and accepted doctor additions
              </span>
            </div>

            {isLoadingPreview ? (
              <div className="p-8 text-center space-y-3 bg-default-50 rounded-medium border border-default-200">
                <Progress
                  size="sm"
                  isIndeterminate
                  color="primary"
                  aria-label="Generating preview"
                />
                <p className="text-xs text-foreground-400">
                  Formatting reviewed document preview...
                </p>
              </div>
            ) : previewError ? (
              <Alert
                color="danger"
                variant="flat"
                title="Preview Error"
                description={previewError}
                startContent={<AlertCircle className="w-4 h-4 shrink-0" />}
              />
            ) : selectedFormat === "pdf" ? (
              /* PDF A4 Document Sheet Simulation */
              <div className="max-h-80 overflow-y-auto p-6 rounded-medium bg-white dark:bg-zinc-900 border border-default-300 dark:border-zinc-700 shadow-inner font-sans text-xs text-zinc-800 dark:text-zinc-200 space-y-4">
                <div className="border-b-2 border-zinc-300 dark:border-zinc-700 pb-3 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold tracking-wider uppercase text-zinc-900 dark:text-zinc-100">
                      Clinical Discharge Summary
                    </h3>
                    <p className="text-[11px] text-zinc-500 dark:text-zinc-400 font-mono">
                      File: {filename} &bull; Case #{reportId}
                    </p>
                  </div>
                  <div className="text-right text-[10px] text-zinc-400">
                    <div>Format: A4 PDF (ReportLab)</div>
                    <div>Page 1 of 1</div>
                  </div>
                </div>

                <div className="space-y-3 leading-relaxed">
                  {previewContent ? (
                    previewContent.split("\n\n").map((block, idx) => {
                      const lines = block.split("\n").filter(Boolean);
                      if (lines.length === 0) return null;
                      const title = lines[0].replace(/-/g, "").trim();
                      const items = lines.slice(1).filter((l) => !l.trim().match(/^-+$/));
                      const isAddedOnReview = title.toLowerCase().includes("added on review");

                      return (
                        <div key={idx} className="space-y-1">
                          {title && (
                            <h4
                              className={`text-[11px] font-bold uppercase tracking-wider pb-0.5 border-b ${
                                isAddedOnReview
                                  ? "text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800"
                                  : "text-zinc-800 dark:text-zinc-200 border-zinc-200 dark:border-zinc-700"
                              }`}
                            >
                              {title} {isAddedOnReview && "(Physician Approved)"}
                            </h4>
                          )}
                          <ul className="space-y-1 pl-3">
                            {items.map((item, iIdx) => (
                              <li
                                key={iIdx}
                                className={`list-disc ${
                                  isAddedOnReview
                                    ? "text-emerald-900 dark:text-emerald-200 font-medium"
                                    : "text-zinc-700 dark:text-zinc-300"
                                }`}
                              >
                                {item.replace(/^-\s*/, "")}
                              </li>
                            ))}
                          </ul>
                        </div>
                      );
                    })
                  ) : (
                    <p className="italic text-zinc-400">No document content available.</p>
                  )}
                </div>

                <div className="border-t border-zinc-200 dark:border-zinc-800 pt-3 text-[10px] text-zinc-400 text-center flex items-center justify-between">
                  <span>Advisory Clinical Evaluation</span>
                  <span>Verified Completeness Document</span>
                </div>
              </div>
            ) : selectedFormat === "docx" ? (
              /* Microsoft Word Document Sheet Simulation */
              <div className="max-h-80 overflow-y-auto p-6 rounded-medium bg-white dark:bg-zinc-900 border border-blue-200 dark:border-blue-900/50 shadow-inner font-sans text-xs text-zinc-800 dark:text-zinc-200 space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-blue-200 dark:border-blue-900/60">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 bg-blue-600 rounded-xs" />
                    <span className="font-semibold text-blue-700 dark:text-blue-400 text-xs">
                      Microsoft Word Document (.docx)
                    </span>
                  </div>
                  <span className="text-[10px] text-zinc-400 font-mono">
                    1-inch margins &bull; Heading 1 styling
                  </span>
                </div>

                <div className="space-y-3">
                  {previewContent ? (
                    previewContent.split("\n\n").map((block, idx) => {
                      const lines = block.split("\n").filter(Boolean);
                      if (lines.length === 0) return null;
                      const title = lines[0].replace(/-/g, "").trim();
                      const items = lines.slice(1).filter((l) => !l.trim().match(/^-+$/));
                      const isAddedOnReview = title.toLowerCase().includes("added on review");

                      return (
                        <div key={idx} className="space-y-1">
                          {title && (
                            <h4
                              className={`text-xs font-semibold ${
                                isAddedOnReview
                                  ? "text-emerald-700 dark:text-emerald-400"
                                  : "text-blue-700 dark:text-blue-400"
                              }`}
                            >
                              {title}
                            </h4>
                          )}
                          <div className="space-y-1 pl-4">
                            {items.map((item, iIdx) => (
                              <div
                                key={iIdx}
                                className={`flex items-start gap-1.5 ${
                                  isAddedOnReview
                                    ? "text-emerald-800 dark:text-emerald-300 font-medium"
                                    : "text-zinc-700 dark:text-zinc-300"
                                }`}
                              >
                                <span className="text-zinc-400">&bull;</span>
                                <span>{item.replace(/^-\s*/, "")}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <p className="italic text-zinc-400">No document content available.</p>
                  )}
                </div>
              </div>
            ) : (
              /* TXT Monospace Raw Preview */
              <div className="max-h-80 overflow-y-auto p-4 rounded-medium bg-default-50 border border-default-200 text-xs font-mono text-foreground-800 leading-relaxed whitespace-pre-wrap select-text">
                {previewContent || "No preview content available."}
              </div>
            )}
          </div>

          {exportError && (
            <Alert
              color="danger"
              variant="flat"
              title="Export Error"
              description={exportError}
              startContent={<AlertCircle className="w-4 h-4 shrink-0" />}
            />
          )}

          {exportSuccess && (
            <Alert
              color="success"
              variant="flat"
              title="Export Successful"
              description="Discharge summary file downloaded successfully and export event logged to audit trail."
              startContent={<CheckCircle2 className="w-4 h-4 shrink-0" />}
            />
          )}
        </ModalBody>

        <Divider />

        <ModalFooter className="flex items-center justify-between">
          <Button
            color="default"
            variant="flat"
            size="sm"
            onPress={onClose}
            isDisabled={isExporting}
          >
            Cancel
          </Button>

          <Button
            color="primary"
            variant="solid"
            size="md"
            isLoading={isExporting}
            isDisabled={isExporting || isLoadingPreview}
            startContent={!isExporting ? <Download className="w-4 h-4" /> : undefined}
            onPress={handleExport}
          >
            {isExporting
              ? "Generating Export..."
              : `Export & Download ${selectedFormat.toUpperCase()}`}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
