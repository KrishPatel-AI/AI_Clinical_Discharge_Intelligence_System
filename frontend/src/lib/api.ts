import {
  DocumentFormat,
  HistoryQueryParams,
  PersistedReportResponse,
  PreviewResponse,
  ReviewHistoryResponse,
  ReviewResponse,
  SuggestionStatus,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    let details: unknown = null;
    try {
      const errorJson = await response.json();
      details = errorJson;
      if (typeof errorJson.detail === "string") {
        errorMessage = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        errorMessage = errorJson.detail
          .map((item: { msg?: string }) => item.msg || JSON.stringify(item))
          .join(", ");
      } else if (errorJson.message) {
        errorMessage = errorJson.message;
      }
    } catch {
      // response body was not json
    }
    throw new ApiError(errorMessage, response.status, details);
  }
  return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    return await handleResponse<{ status: string }>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Clinical intelligence backend is unreachable. Verify that the API server is active.",
      0
    );
  }
}

export async function createReview(file: File): Promise<ReviewResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/reviews`, {
      method: "POST",
      body: formData,
    });
    return await handleResponse<ReviewResponse>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Unable to process discharge document. Verify network connection and backend status.",
      0
    );
  }
}

export async function getReview(
  reportId: number
): Promise<PersistedReportResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/reviews/${reportId}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    return await handleResponse<PersistedReportResponse>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to load review report #${reportId}. Check network connection.`,
      0
    );
  }
}

export async function updateSuggestionStatus(
  reportId: number,
  suggestionId: number,
  status: SuggestionStatus
): Promise<PersistedReportResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/reviews/${reportId}/suggestions/${suggestionId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ status }),
      }
    );
    return await handleResponse<PersistedReportResponse>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Failed to update suggestion decision. Please retry.",
      0
    );
  }
}

export async function getPreview(
  reportId: number,
  format: DocumentFormat
): Promise<PreviewResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/reviews/${reportId}/preview?format=${format}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      }
    );
    return await handleResponse<PreviewResponse>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      `Failed to generate preview for format ${format.toUpperCase()}.`,
      0
    );
  }
}

export async function exportReview(
  reportId: number,
  format: DocumentFormat
): Promise<{ blob: Blob; filename: string }> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/reviews/${reportId}/export?format=${format}`,
      {
        method: "POST",
      }
    );
    if (!response.ok) {
      let errorMessage = `Export failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) errorMessage = errorJson.detail;
      } catch {
        // non-json
      }
      throw new ApiError(errorMessage, response.status);
    }

    const disposition = response.headers.get("Content-Disposition");
    let filename = `review-${reportId}.${format}`;
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    const blob = await response.blob();
    return { blob, filename };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("Failed to export discharge report.", 0);
  }
}

export async function listReviews(
  params: HistoryQueryParams = {}
): Promise<ReviewHistoryResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.sort) query.set("sort", params.sort);
  if (params.group_by) query.set("group_by", params.group_by);
  if (params.offset !== undefined) query.set("offset", params.offset.toString());
  if (params.limit !== undefined) query.set("limit", params.limit.toString());

  try {
    const queryString = query.toString();
    const url = `${API_BASE_URL}/reviews${queryString ? `?${queryString}` : ""}`;
    const response = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    return await handleResponse<ReviewHistoryResponse>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "Failed to load review history from server.",
      0
    );
  }
}
