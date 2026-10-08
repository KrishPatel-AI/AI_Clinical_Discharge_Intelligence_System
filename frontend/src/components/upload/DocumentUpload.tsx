"use client";

import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Chip,
  Progress,
  Alert,
} from "@heroui/react";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  RefreshCw,
  FileCheck,
} from "lucide-react";
import { createReview, ApiError } from "@/lib/api";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export function DocumentUpload() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    setValidationError(null);
    setApiError(null);

    const name = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) =>
      name.endsWith(ext)
    );

    if (!hasValidExtension) {
      setValidationError(
        `Unsupported file type. Please upload a PDF, DOCX, or plain text (.txt) document.`
      );
      return false;
    }

    if (file.size === 0) {
      setValidationError("The selected file is empty. Please choose a valid document.");
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError(
        `File size exceeds 10MB limit. Current file size: ${(
          file.size /
          (1024 * 1024)
        ).toFixed(2)} MB.`
      );
      return false;
    }

    return true;
  };

  const handleFileSelect = (file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isProcessing) setIsDragging(true);
  };

  const onDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (isProcessing) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleStartReview = async () => {
    if (!selectedFile || isProcessing) return;

    setIsProcessing(true);
    setApiError(null);

    try {
      const result = await createReview(selectedFile);
      if (result.report_id) {
        router.push(`/reviews/${result.report_id}`);
      } else {
        throw new ApiError(
          "Review completed but no report identifier was returned by the server.",
          500
        );
      }
    } catch (err) {
      setIsProcessing(false);
      if (err instanceof ApiError) {
        setApiError(err.message);
      } else {
        setApiError(
          "An unexpected error occurred during review processing. Please retry."
        );
      }
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setValidationError(null);
    setApiError(null);
    setIsProcessing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
          New Clinical Discharge Review
        </h1>
        <p className="text-sm text-foreground-500 max-w-lg mx-auto">
          Upload a patient discharge summary in PDF, DOCX, or TXT format.
          The system will retrieve the matching guideline, score completeness,
          and identify recommendations for physician review.
        </p>
      </div>

      <Card className="border border-default-200 dark:border-default-100 shadow-sm">
        <CardHeader className="pb-2 px-6 pt-6 flex-col items-start gap-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-foreground-400">
            Document Upload
          </span>
          <p className="text-sm text-foreground-600">
            Select or drag a discharge summary file below.
          </p>
        </CardHeader>

        <CardBody className="px-6 pb-6 pt-2 space-y-5">
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-large p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? "border-primary bg-primary/5"
                : selectedFile
                ? "border-success/50 bg-success/5"
                : "border-default-300 hover:border-default-400 bg-default-50/50"
            } ${isProcessing ? "opacity-60 cursor-not-allowed pointer-events-none" : ""}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={onInputChange}
              disabled={isProcessing}
            />

            <div className="flex flex-col items-center justify-center space-y-3">
              {selectedFile ? (
                <div className="w-12 h-12 rounded-full bg-success/10 text-success flex items-center justify-center">
                  <FileCheck className="w-6 h-6" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-full bg-default-100 text-foreground-500 flex items-center justify-center">
                  <UploadCloud className="w-6 h-6" />
                </div>
              )}

              {selectedFile ? (
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-foreground">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-foreground-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB • Ready for analysis
                  </p>
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-foreground">
                    Click to select or drag and drop document
                  </p>
                  <p className="text-xs text-foreground-400">
                    Supported formats: PDF, DOCX, TXT (up to 10MB)
                  </p>
                </div>
              )}

              <div className="flex items-center gap-2 pt-1">
                {ALLOWED_EXTENSIONS.map((ext) => (
                  <Chip key={ext} size="sm" variant="flat" color="default" className="text-[11px]">
                    {ext.toUpperCase().replace(".", "")}
                  </Chip>
                ))}
              </div>
            </div>
          </div>

          {validationError && (
            <Alert
              color="danger"
              variant="flat"
              title="File Validation Error"
              description={validationError}
              startContent={<AlertCircle className="w-4 h-4 shrink-0" />}
            />
          )}

          {apiError && (
            <Alert
              color="danger"
              variant="flat"
              title="Review Processing Failed"
              description={apiError}
              startContent={<AlertCircle className="w-4 h-4 shrink-0" />}
              endContent={
                <Button
                  size="sm"
                  variant="flat"
                  color="danger"
                  startContent={<RefreshCw className="w-3.5 h-3.5" />}
                  onPress={handleStartReview}
                >
                  Retry
                </Button>
              }
            />
          )}

          {isProcessing && (
            <div className="space-y-3 p-4 rounded-medium bg-default-50 border border-default-200">
              <div className="flex items-center justify-between text-xs text-foreground-600">
                <span className="font-medium">Analyzing Discharge Document</span>
                <span className="text-foreground-400">Processing with clinical RAG...</span>
              </div>
              <Progress
                size="sm"
                isIndeterminate
                color="primary"
                aria-label="Analyzing discharge document"
              />
              <p className="text-xs text-foreground-400 leading-relaxed">
                Extracting clinical sections, matching against authoritative clinical guidelines, and calculating completeness score...
              </p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            {selectedFile ? (
              <Button
                variant="light"
                color="default"
                size="sm"
                isDisabled={isProcessing}
                onPress={handleReset}
              >
                Clear Selection
              </Button>
            ) : (
              <div className="text-xs text-foreground-400">
                No file currently selected
              </div>
            )}

            <Button
              color="primary"
              variant="solid"
              size="md"
              className="w-full sm:w-auto font-medium"
              isDisabled={!selectedFile || isProcessing || !!validationError}
              isLoading={isProcessing}
              startContent={!isProcessing ? <FileText className="w-4 h-4" /> : undefined}
              onPress={handleStartReview}
            >
              {isProcessing ? "Processing Document..." : "Start Review"}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
