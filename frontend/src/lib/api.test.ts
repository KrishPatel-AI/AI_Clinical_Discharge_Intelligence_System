import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  ApiError,
  checkHealth,
  createReview,
  getReview,
  updateSuggestionStatus,
  getPreview,
  exportReview,
  listReviews,
} from "./api";

describe("Frontend API Client Tests", () => {
  it("ApiError correctly preserves status, message and details", () => {
    const error = new ApiError("Validation failed", 400, { field: "file" });
    assert.equal(error.name, "ApiError");
    assert.equal(error.status, 400);
    assert.equal(error.message, "Validation failed");
    assert.deepEqual(error.details, { field: "file" });
  });

  it("checkHealth parses successful health payload", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ status: "ok" }), { status: 200 });

    try {
      const res = await checkHealth();
      assert.equal(res.status, "ok");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("checkHealth converts network failure to descriptive ApiError", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new TypeError("Failed to fetch");
    };

    try {
      await assert.rejects(
        async () => {
          await checkHealth();
        },
        (err: unknown) => {
          assert(err instanceof ApiError);
          assert.equal(err.status, 0);
          assert(err.message.includes("backend is unreachable"));
          return true;
        }
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("createReview sends multipart file and parses response", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (_url, init) => {
      assert.equal(init?.method, "POST");
      assert(init?.body instanceof FormData);
      return new Response(
        JSON.stringify({
          diagnosis: "Asthma",
          status: "needs_review",
          message: "Guideline gaps identified",
          report_id: 12,
          suggestions: [],
          comparisons: [],
        }),
        { status: 200 }
      );
    };

    try {
      const file = new File(["Sample clinical text"], "discharge.txt", {
        type: "text/plain",
      });
      const review = await createReview(file);
      assert.equal(review.diagnosis, "Asthma");
      assert.equal(review.report_id, 12);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("getReview fetches persisted report by ID", async () => {
    const originalFetch = globalThis.fetch;
    let requestedUrl = "";

    globalThis.fetch = async (url) => {
      requestedUrl = url.toString();
      return new Response(
        JSON.stringify({
          id: 12,
          filename: "discharge.txt",
          diagnosis: "Asthma",
          status: "needs_review",
          message: "Guideline gaps identified",
          source_text: "Sample clinical text",
          suggestions: [],
          audit_logs: [],
          created_at: new Date().toISOString(),
        }),
        { status: 200 }
      );
    };

    try {
      const report = await getReview(12);
      assert(requestedUrl.includes("/reviews/12"));
      assert.equal(report.id, 12);
      assert.equal(report.diagnosis, "Asthma");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("updateSuggestionStatus sends PATCH with status and parses updated report", async () => {
    const originalFetch = globalThis.fetch;
    let requestedUrl = "";
    let requestedBody = "";

    globalThis.fetch = async (url, init) => {
      requestedUrl = url.toString();
      requestedBody = init?.body?.toString() || "";
      return new Response(
        JSON.stringify({
          id: 5,
          filename: "summary.pdf",
          diagnosis: "Asthma",
          status: "complete",
          message: "Review complete",
          source_text: "Original discharge",
          suggestions: [
            {
              id: 101,
              section: "Medications",
              explanation: "Inhaled corticosteroids",
              guideline_passage: "Prescribe ICS",
              source_url: "https://example.com",
              status: "accepted",
              decision: "accepted",
            },
          ],
          audit_logs: [],
        }),
        { status: 200 }
      );
    };

    try {
      const updated = await updateSuggestionStatus(5, 101, "accepted");
      assert(requestedUrl.includes("/reviews/5/suggestions/101"));
      assert.equal(JSON.parse(requestedBody).status, "accepted");
      assert.equal(updated.suggestions[0].status, "accepted");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("getPreview queries preview endpoint with format parameter", async () => {
    const originalFetch = globalThis.fetch;
    let requestedUrl = "";

    globalThis.fetch = async (url) => {
      requestedUrl = url.toString();
      return new Response(
        JSON.stringify({
          report_id: 8,
          format: "txt",
          content: "Structured Preview Text",
          exported: false,
        }),
        { status: 200 }
      );
    };

    try {
      const preview = await getPreview(8, "txt");
      assert(requestedUrl.includes("/reviews/8/preview?format=txt"));
      assert.equal(preview.content, "Structured Preview Text");
      assert.equal(preview.exported, false);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("exportReview returns blob and extracted filename from disposition", async () => {
    const originalFetch = globalThis.fetch;

    globalThis.fetch = async () =>
      new Response(new Blob(["mock-pdf-bytes"]), {
        status: 200,
        headers: {
          "Content-Disposition": 'attachment; filename="discharge-report-8.pdf"',
          "Content-Type": "application/pdf",
        },
      });

    try {
      const result = await exportReview(8, "pdf");
      assert.equal(result.filename, "discharge-report-8.pdf");
      assert(result.blob instanceof Blob);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("listReviews formats query parameters correctly", async () => {
    const originalFetch = globalThis.fetch;
    let requestedUrl = "";

    globalThis.fetch = async (url) => {
      requestedUrl = url.toString();
      return new Response(
        JSON.stringify({
          reviews: [],
          total: 0,
          offset: 10,
          limit: 10,
          groups: null,
        }),
        { status: 200 }
      );
    };

    try {
      await listReviews({
        search: "asthma",
        status: "complete",
        sort: "score",
        group_by: "diagnosis",
        offset: 10,
        limit: 10,
      });

      assert(requestedUrl.includes("search=asthma"));
      assert(requestedUrl.includes("status=complete"));
      assert(requestedUrl.includes("sort=score"));
      assert(requestedUrl.includes("group_by=diagnosis"));
      assert(requestedUrl.includes("offset=10"));
      assert(requestedUrl.includes("limit=10"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
