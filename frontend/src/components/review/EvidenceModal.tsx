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
import { ExternalLink, BookOpen, Quote } from "lucide-react";
import { PersistedSuggestion } from "@/types/api";

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
              Clinical Guideline Evidence
            </span>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <Chip size="sm" variant="flat" color="primary">
              {suggestion.section}
            </Chip>
            <span className="text-xs text-foreground-400">
              Suggestion #{suggestion.id}
            </span>
          </div>
        </ModalHeader>

        <Divider />

        <ModalBody className="py-4 space-y-4">
          <div className="space-y-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground-400">
              Recommendation Summary
            </span>
            <p className="text-sm text-foreground-700 leading-relaxed bg-default-50 p-3 rounded-medium border border-default-200">
              {suggestion.explanation}
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-foreground-400">
              <Quote className="w-3.5 h-3.5" />
              <span>Authoritative Guideline Passage</span>
            </div>
            <div className="p-4 rounded-medium bg-default-100/70 border border-default-200 text-sm font-mono text-foreground-800 leading-relaxed whitespace-pre-wrap">
              {suggestion.guideline_passage}
            </div>
          </div>

          {suggestion.source_url && (
            <div className="space-y-1 pt-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-foreground-400">
                Source Document Reference
              </span>
              <div className="flex items-center gap-2 text-xs">
                <ExternalLink className="w-3.5 h-3.5 text-primary shrink-0" />
                <Link
                  href={suggestion.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  isExternal
                  showAnchorIcon
                  className="text-xs break-all text-primary hover:underline"
                >
                  {suggestion.source_url}
                </Link>
              </div>
            </div>
          )}
        </ModalBody>

        <Divider />

        <ModalFooter>
          <Button color="default" variant="flat" size="sm" onPress={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
