"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DocumentUpload } from "@/components/upload/DocumentUpload";
import {
  Card,
  CardBody,
  Chip,
} from "@heroui/react";
import { History, FileText, ArrowRight } from "lucide-react";
import { listReviews } from "@/lib/api";
import { PersistedReportResponse } from "@/types/api";

export default function HomePage() {
  const [recentReviews, setRecentReviews] = useState<PersistedReportResponse[]>([]);
  const [isLoadingRecent, setIsLoadingRecent] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchRecent = async () => {
      try {
        const res = await listReviews({ limit: 3, sort: "newest" });
        if (isMounted) setRecentReviews(res.reviews || []);
      } catch {
        // silent fail on home page quick preview
      } finally {
        if (isMounted) setIsLoadingRecent(false);
      }
    };
    fetchRecent();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="w-full space-y-12">
      <DocumentUpload />

      {/* Recent Reviews Preview */}
      {!isLoadingRecent && recentReviews.length > 0 && (
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-foreground-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground-500">
                Recent Reviews
              </h2>
            </div>
            <Link
              href="/reviews"
              className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
            >
              <span>View all reviews</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2">
            {recentReviews.map((rev) => (
              <Card
                key={rev.id}
                isPressable
                as={Link}
                href={`/reviews/${rev.id}`}
                className="w-full border border-default-200 dark:border-default-100 shadow-none hover:border-primary/50 transition-colors"
              >
                <CardBody className="p-3 sm:p-4 flex flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-3 truncate">
                    <div className="p-2 rounded-medium bg-default-100 text-foreground-600">
                      <FileText className="w-4 h-4 shrink-0" />
                    </div>
                    <div className="truncate text-left">
                      <p className="text-sm font-medium text-foreground truncate">
                        {rev.filename}
                      </p>
                      <p className="text-xs text-foreground-400 truncate">
                        {rev.diagnosis || "Unspecified"} • #{rev.id}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {rev.completeness_score !== null && rev.completeness_score !== undefined && (
                      <Chip
                        size="sm"
                        variant="flat"
                        color={
                          rev.completeness_score >= 80
                            ? "success"
                            : rev.completeness_score >= 50
                            ? "warning"
                            : "danger"
                        }
                        className="text-xs font-mono"
                      >
                        {rev.completeness_score}%
                      </Chip>
                    )}
                    <Chip
                      size="sm"
                      variant="dot"
                      color={
                        rev.status === "complete"
                          ? "success"
                          : rev.status === "no_match"
                          ? "default"
                          : "warning"
                      }
                      className="text-xs capitalize"
                    >
                      {rev.status.replace("_", " ")}
                    </Chip>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
