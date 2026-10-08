"use client";

import React from "react";
import { Card, CardBody, Progress, Chip } from "@heroui/react";
import { HelpCircle } from "lucide-react";

interface CompletenessBadgeProps {
  score: number | null | undefined;
  status: string;
}

export function CompletenessBadge({ score, status }: CompletenessBadgeProps) {
  if (status === "no_match" || score === null || score === undefined) {
    return (
      <Card className="border border-default-200 dark:border-default-100 shadow-none bg-default-50/50">
        <CardBody className="p-4 flex flex-row items-center justify-between gap-3">
          <div className="space-y-0.5">
            <span className="text-xs font-semibold text-foreground-400 uppercase tracking-wider">
              Guideline Status
            </span>
            <p className="text-sm font-medium text-foreground">
              No Guideline Match
            </p>
          </div>
          <Chip
            size="sm"
            variant="flat"
            color="default"
            startContent={<HelpCircle className="w-3.5 h-3.5" />}
          >
            Unscored
          </Chip>
        </CardBody>
      </Card>
    );
  }

  const isHigh = score >= 80;
  const isModerate = score >= 50 && score < 80;
  const color = isHigh ? "success" : isModerate ? "warning" : "danger";

  return (
    <Card className="border border-default-200 dark:border-default-100 shadow-none bg-default-50/50">
      <CardBody className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground-400 uppercase tracking-wider">
            Completeness Score
          </span>
          <div className="flex items-center gap-1.5">
            <span className="text-xl font-bold text-foreground">
              {score}
            </span>
            <span className="text-xs text-foreground-400">/ 100</span>
          </div>
        </div>

        <Progress
          size="sm"
          radius="full"
          value={score}
          color={color}
          aria-label={`Completeness score: ${score} percent`}
        />

        <div className="flex items-center justify-between text-xs text-foreground-500 pt-0.5">
          <span>
            {isHigh
              ? "Comprehensive discharge summary"
              : isModerate
              ? "Guideline gaps identified"
              : "Significant guideline gaps"}
          </span>
          <Chip
            size="sm"
            variant="flat"
            color={color}
            className="text-[11px] h-5"
          >
            {score === 100 ? "Complete" : `${100 - score}% Gap`}
          </Chip>
        </div>
      </CardBody>
    </Card>
  );
}
