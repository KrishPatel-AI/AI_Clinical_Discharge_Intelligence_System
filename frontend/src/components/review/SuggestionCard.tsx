"use client";

import React from "react";
import {
  Card,
  CardBody,
  CardFooter,
  Button,
  Chip,
  Tooltip,
} from "@heroui/react";
import {
  Check,
  X,
  BookOpen,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import { PersistedSuggestion, SuggestionStatus } from "@/types/api";

interface SuggestionCardProps {
  suggestion: PersistedSuggestion;
  onUpdateStatus: (
    suggestionId: number,
    status: SuggestionStatus
  ) => Promise<void>;
  onViewEvidence: (suggestion: PersistedSuggestion) => void;
  isUpdating: boolean;
}

export function SuggestionCard({
  suggestion,
  onUpdateStatus,
  onViewEvidence,
  isUpdating,
}: SuggestionCardProps) {
  const isAccepted = suggestion.status === "accepted" || suggestion.decision === "accepted";
  const isRejected = suggestion.status === "rejected" || suggestion.decision === "ignored";
  const isPending = !isAccepted && !isRejected;

  const getStatusChip = () => {
    if (isAccepted) {
      return (
        <Chip
          size="sm"
          color="success"
          variant="flat"
          startContent={<CheckCircle2 className="w-3.5 h-3.5" />}
        >
          Accepted
        </Chip>
      );
    }
    if (isRejected) {
      return (
        <Chip
          size="sm"
          color="danger"
          variant="flat"
          startContent={<XCircle className="w-3.5 h-3.5" />}
        >
          Ignored
        </Chip>
      );
    }
    return (
      <Chip
        size="sm"
        color="warning"
        variant="flat"
        startContent={<Clock className="w-3.5 h-3.5" />}
      >
        Pending Review
      </Chip>
    );
  };

  return (
    <Card
      className={`border transition-all ${
        isAccepted
          ? "border-success/40 bg-success/5 shadow-none"
          : isRejected
          ? "border-danger/30 bg-danger/5 opacity-75 shadow-none"
          : "border-default-200 dark:border-default-100 shadow-sm"
      }`}
    >
      <CardBody className="p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Chip
              size="sm"
              variant="flat"
              color="primary"
              className="text-xs font-medium"
            >
              {suggestion.section}
            </Chip>
            <span className="text-xs text-foreground-400">
              #{suggestion.id}
            </span>
          </div>
          {getStatusChip()}
        </div>

        <p className="text-sm text-foreground-800 leading-relaxed">
          {suggestion.explanation}
        </p>

        {suggestion.decided_at && (
          <p className="text-[11px] text-foreground-400">
            Decided: {new Date(suggestion.decided_at).toLocaleString()}
          </p>
        )}
      </CardBody>

      <CardFooter className="px-4 pb-3 pt-0 flex items-center justify-between gap-2">
        <Button
          size="sm"
          variant="light"
          color="default"
          className="text-xs font-medium"
          startContent={<BookOpen className="w-3.5 h-3.5 text-primary" />}
          onPress={() => onViewEvidence(suggestion)}
        >
          View Evidence
        </Button>

        <div className="flex items-center gap-1.5">
          {isPending ? (
            <>
              <Tooltip content="Accept suggestion and append to final discharge document">
                <Button
                  size="sm"
                  color="success"
                  variant="flat"
                  isLoading={isUpdating}
                  isDisabled={isUpdating}
                  startContent={!isUpdating ? <Check className="w-3.5 h-3.5" /> : undefined}
                  onPress={() => onUpdateStatus(suggestion.id, "accepted")}
                >
                  Accept
                </Button>
              </Tooltip>

              <Tooltip content="Ignore suggestion without altering discharge document">
                <Button
                  size="sm"
                  color="danger"
                  variant="flat"
                  isLoading={isUpdating}
                  isDisabled={isUpdating}
                  startContent={!isUpdating ? <X className="w-3.5 h-3.5" /> : undefined}
                  onPress={() => onUpdateStatus(suggestion.id, "rejected")}
                >
                  Ignore
                </Button>
              </Tooltip>
            </>
          ) : (
            <>
              {isAccepted ? (
                <Button
                  size="sm"
                  color="danger"
                  variant="light"
                  isLoading={isUpdating}
                  isDisabled={isUpdating}
                  startContent={!isUpdating ? <X className="w-3.5 h-3.5" /> : undefined}
                  onPress={() => onUpdateStatus(suggestion.id, "rejected")}
                >
                  Change to Ignore
                </Button>
              ) : (
                <Button
                  size="sm"
                  color="success"
                  variant="light"
                  isLoading={isUpdating}
                  isDisabled={isUpdating}
                  startContent={!isUpdating ? <Check className="w-3.5 h-3.5" /> : undefined}
                  onPress={() => onUpdateStatus(suggestion.id, "accepted")}
                >
                  Change to Accept
                </Button>
              )}

              <Tooltip content="Revert this decision back to pending review">
                <Button
                  size="sm"
                  variant="flat"
                  color="default"
                  isLoading={isUpdating}
                  isDisabled={isUpdating}
                  startContent={!isUpdating ? <RotateCcw className="w-3 h-3" /> : undefined}
                  onPress={() => onUpdateStatus(suggestion.id, "pending")}
                >
                  Reset
                </Button>
              </Tooltip>
            </>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
