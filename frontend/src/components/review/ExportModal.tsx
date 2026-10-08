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
            ) : (
              <div className="max-h-72 overflow-y-auto p-4 rounded-medium bg-default-50 border border-default-200 text-xs font-mono text-foreground-800 leading-relaxed whitespace-pre-wrap select-text">
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
