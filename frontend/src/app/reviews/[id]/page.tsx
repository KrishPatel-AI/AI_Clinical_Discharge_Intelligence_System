import React from "react";
import { Metadata } from "next";
import { ReviewWorkspace } from "@/components/review/ReviewWorkspace";

interface ReviewDetailPageProps {
  params: {
    id: string;
  };
}

export function generateMetadata({ params }: ReviewDetailPageProps): Metadata {
  return {
    title: `Review #${params.id} — Clinical Discharge Intelligence System`,
    description: `Clinical discharge review workspace and guideline evaluation for report #${params.id}.`,
  };
}

export default function ReviewDetailPage({ params }: ReviewDetailPageProps) {
  const reportId = parseInt(params.id, 10);

  if (isNaN(reportId)) {
    return (
      <div className="w-full max-w-md mx-auto py-16 text-center space-y-4">
        <h1 className="text-xl font-semibold text-danger">Invalid Report ID</h1>
        <p className="text-sm text-foreground-500">
          The requested review report identifier is not a valid number.
        </p>
      </div>
    );
  }

  return <ReviewWorkspace reportId={reportId} />;
}
