"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Input,
  Select,
  SelectItem,
  Button,
  Chip,
  Pagination,
  Card,
  CardBody,
  Skeleton,
  Alert,
  Tooltip,
} from "@heroui/react";
import {
  Search,
  ArrowUpDown,
  Layers,
  Filter,
  FileText,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Clock,
} from "lucide-react";
import {
  PersistedReportResponse,
  ReviewHistoryResponse,
  HistoryQueryParams,
} from "@/types/api";
import { listReviews, ApiError } from "@/lib/api";

const PAGE_SIZE = 10;

export function HistoryWorkspace() {
  const router = useRouter();

  const [reviews, setReviews] = useState<PersistedReportResponse[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [groups, setGroups] = useState<Record<string, number[]> | null>(null);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortOption, setSortOption] = useState<"newest" | "oldest" | "score">("newest");
  const [groupByOption, setGroupByOption] = useState<"" | "diagnosis" | "status">("");
  const [page, setPage] = useState(1);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: HistoryQueryParams = {
        sort: sortOption,
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      };

      if (debouncedSearch.trim()) {
        params.search = debouncedSearch.trim();
      }
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      if (groupByOption) {
        params.group_by = groupByOption;
      }

      const res: ReviewHistoryResponse = await listReviews(params);
      setReviews(res.reviews || []);
      setTotalCount(res.total || 0);
      setGroups(res.groups || null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to fetch review history. Please verify backend service.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, statusFilter, sortOption, groupByOption, page]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  const getStatusChip = (status: string) => {
    switch (status) {
      case "complete":
        return (
          <Chip
            size="sm"
            color="success"
            variant="flat"
            startContent={<CheckCircle2 className="w-3 h-3" />}
          >
            Complete
          </Chip>
        );
      case "no_match":
        return (
          <Chip
            size="sm"
            color="default"
            variant="flat"
            startContent={<HelpCircle className="w-3 h-3" />}
          >
            No Guideline Match
          </Chip>
        );
      default:
        return (
          <Chip
            size="sm"
            color="warning"
            variant="flat"
            startContent={<Clock className="w-3 h-3" />}
          >
            Needs Review
          </Chip>
        );
    }
  };

  const getScoreDisplay = (score: number | null | undefined, status: string) => {
    if (status === "no_match" || score === null || score === undefined) {
      return <span className="text-xs text-foreground-400 font-mono">-</span>;
    }
    const color =
      score >= 80 ? "text-success" : score >= 50 ? "text-warning" : "text-danger";
    return (
      <div className="flex items-center gap-1">
        <span className={`text-xs font-bold font-mono ${color}`}>{score}</span>
        <span className="text-[10px] text-foreground-400">/ 100</span>
      </div>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Review History
          </h1>
          <p className="text-sm text-foreground-500">
            Search, filter, and audit all processed discharge summary evaluations.
          </p>
        </div>
        <Button
          size="sm"
          color="primary"
          variant="solid"
          startContent={<FileText className="w-4 h-4" />}
          onPress={() => router.push("/")}
        >
          New Review
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card className="border border-default-200 dark:border-default-100 shadow-none bg-default-50/50">
        <CardBody className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <Input
            size="sm"
            placeholder="Search diagnosis, filename..."
            startContent={<Search className="w-4 h-4 text-foreground-400" />}
            value={search}
            onValueChange={setSearch}
            isClearable
            onClear={() => setSearch("")}
            className="w-full"
          />

          {/* Status Filter */}
          <Select
            size="sm"
            labelPlacement="outside"
            placeholder="All Statuses"
            selectedKeys={[statusFilter]}
            onChange={(e) => {
              setStatusFilter(e.target.value || "all");
              setPage(1);
            }}
            startContent={<Filter className="w-3.5 h-3.5 text-foreground-400" />}
            aria-label="Filter by status"
          >
            <SelectItem key="all">
              All Statuses
            </SelectItem>
            <SelectItem key="complete">
              Complete
            </SelectItem>
            <SelectItem key="needs_review">
              Needs Review
            </SelectItem>
            <SelectItem key="no_match">
              No Guideline Match
            </SelectItem>
          </Select>

          {/* Sort By */}
          <Select
            size="sm"
            labelPlacement="outside"
            placeholder="Sort by"
            selectedKeys={[sortOption]}
            onChange={(e) => {
              setSortOption((e.target.value as "newest" | "oldest" | "score") || "newest");
              setPage(1);
            }}
            startContent={<ArrowUpDown className="w-3.5 h-3.5 text-foreground-400" />}
            aria-label="Sort by"
          >
            <SelectItem key="newest">
              Newest First
            </SelectItem>
            <SelectItem key="oldest">
              Oldest First
            </SelectItem>
            <SelectItem key="score">
              Highest Completeness Score
            </SelectItem>
          </Select>

          {/* Group By */}
          <Select
            size="sm"
            labelPlacement="outside"
            placeholder="Group By"
            selectedKeys={[groupByOption || "none"]}
            onChange={(e) => {
              const val = e.target.value;
              setGroupByOption(val === "none" || !val ? "" : (val as "diagnosis" | "status"));
              setPage(1);
            }}
            startContent={<Layers className="w-3.5 h-3.5 text-foreground-400" />}
            aria-label="Group by"
          >
            <SelectItem key="none">
              No Grouping
            </SelectItem>
            <SelectItem key="diagnosis">
              Group by Diagnosis
            </SelectItem>
            <SelectItem key="status">
              Group by Status
            </SelectItem>
          </Select>
        </CardBody>
      </Card>

      {/* Grouping Summary Banner */}
      {groups && Object.keys(groups).length > 0 && (
        <div className="flex flex-wrap items-center gap-2 p-3 rounded-medium bg-default-100/60 text-xs text-foreground-600">
          <span className="font-semibold uppercase text-foreground-400 text-[10px]">
            Server Groups:
          </span>
          {Object.entries(groups).map(([groupName, ids]) => (
            <Chip key={groupName} size="sm" variant="flat" color="default">
              {groupName}: {ids.length}
            </Chip>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert
          color="danger"
          variant="flat"
          title="Error Loading History"
          description={error}
          startContent={<AlertCircle className="w-4 h-4 shrink-0" />}
          endContent={
            <Button
              size="sm"
              variant="flat"
              color="danger"
              startContent={<RefreshCw className="w-3.5 h-3.5" />}
              onPress={fetchHistory}
            >
              Retry
            </Button>
          }
        />
      )}

      {/* Table Content */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-14 w-full rounded-medium" />
            ))}
          </div>
        ) : reviews.length === 0 ? (
          <Card className="border border-default-200 dark:border-default-100 shadow-none">
            <CardBody className="py-16 text-center space-y-2">
              <FileText className="w-8 h-8 text-foreground-300 mx-auto" />
              <p className="text-sm font-medium text-foreground">
                No discharge reviews found
              </p>
              <p className="text-xs text-foreground-400 max-w-sm mx-auto">
                {debouncedSearch || statusFilter !== "all"
                  ? "No reviews match the current search filters. Try adjusting your search query."
                  : "No reviews have been created yet. Upload a discharge summary to begin."}
              </p>
              {(debouncedSearch || statusFilter !== "all") && (
                <Button
                  size="sm"
                  variant="flat"
                  color="default"
                  className="mt-2"
                  onPress={() => {
                    setSearch("");
                    setStatusFilter("all");
                    setGroupByOption("");
                  }}
                >
                  Clear Filters
                </Button>
              )}
            </CardBody>
          </Card>
        ) : (
          <Table
            aria-label="Clinical discharge review history table"
            shadow="none"
            className="border border-default-200 dark:border-default-100 rounded-large"
          >
            <TableHeader>
              <TableColumn>DOCUMENT & ID</TableColumn>
              <TableColumn>DIAGNOSIS</TableColumn>
              <TableColumn>STATUS</TableColumn>
              <TableColumn>SCORE</TableColumn>
              <TableColumn>SUGGESTIONS</TableColumn>
              <TableColumn>DATE</TableColumn>
              <TableColumn align="end">ACTION</TableColumn>
            </TableHeader>
            <TableBody>
              {reviews.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer hover:bg-default-50 transition-colors"
                  onClick={() => router.push(`/reviews/${item.id}`)}
                >
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="text-xs font-semibold text-foreground truncate max-w-[200px]">
                        {item.filename}
                      </span>
                      <span className="text-[10px] text-foreground-400 font-mono">
                        #{item.id}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-foreground-800 font-medium truncate max-w-[180px]">
                      {item.diagnosis || "Unspecified"}
                    </span>
                  </TableCell>
                  <TableCell>{getStatusChip(item.status)}</TableCell>
                  <TableCell>
                    {getScoreDisplay(item.completeness_score, item.status)}
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-foreground-600">
                      {item.suggestions?.length || 0}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-foreground-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Tooltip content="Open Review Workspace">
                      <Button
                        size="sm"
                        variant="light"
                        color="primary"
                        endContent={<ExternalLink className="w-3.5 h-3.5" />}
                        onPress={() => router.push(`/reviews/${item.id}`)}
                      >
                        Open
                      </Button>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        {/* Pagination Bar */}
        {totalCount > PAGE_SIZE && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <span className="text-xs text-foreground-400">
              Showing {(page - 1) * PAGE_SIZE + 1} -{" "}
              {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount} reviews
            </span>
            <Pagination
              size="sm"
              total={totalPages}
              page={page}
              onChange={setPage}
              color="primary"
              variant="flat"
              showControls
            />
          </div>
        )}
      </div>
    </div>
  );
}
