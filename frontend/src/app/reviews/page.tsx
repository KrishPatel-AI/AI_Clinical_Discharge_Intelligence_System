import React from "react";
import { Metadata } from "next";
import { HistoryWorkspace } from "@/components/history/HistoryWorkspace";

export const metadata: Metadata = {
  title: "Review History — Clinical Discharge Intelligence System",
  description: "Search, filter, and audit clinical discharge summary reviews.",
};

export default function ReviewsHistoryPage() {
  return <HistoryWorkspace />;
}
