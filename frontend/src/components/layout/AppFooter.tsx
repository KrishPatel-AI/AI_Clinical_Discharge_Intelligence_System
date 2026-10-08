"use client";

import React from "react";
import { Divider } from "@heroui/react";
import { ShieldAlert } from "lucide-react";

export function AppFooter() {
  return (
    <footer className="mt-auto w-full">
      <Divider className="opacity-50" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-foreground-500">
        <div className="flex items-center gap-2 text-foreground-600">
          <ShieldAlert className="w-4 h-4 text-warning shrink-0" />
          <span>
            Clinical Second Reviewer: Suggestions are advisory only and require explicit physician confirmation.
          </span>
        </div>
        <div className="flex items-center gap-4 text-foreground-400">
          <span>Deterministic Clinical Evaluation</span>
          <span>•</span>
          <span>Zero PHI Retention Boundary</span>
        </div>
      </div>
    </footer>
  );
}
