// src/lib/api.ts

/**
 * Central API base URL for the GBI-SCIOS backend.
 *
 * The backend FastAPI app exposes everything under `/api/v1`. We centralize
 * the URL here so that NO service file hard-codes `http://127.0.0.1:8000` or
 * `http://localhost:8000`.
 *
 * Production deployments MUST set the `NEXT_PUBLIC_API_URL` environment
 * variable (e.g. `https://api.gbi-scios.example/api/v1`). When unset, we fall
 * back to the local dev URL so the dev server keeps working out of the box.
 */
export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

/**
 * Helper used by apiClient + auth flow to clear auth state on 401 and force a
 * redirect to /login. Centralizing it here keeps the 401 handling logic in one
 * place.
 */
function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    // Expire the access_token cookie.
    document.cookie =
      "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
  } catch {
    // ignore storage/cookie access errors (private mode etc.)
  }
  // Use a hard navigation to avoid router context issues and ensure middleware
  // re-runs without a stale token cookie.
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

/**
 * Serializes the request body for fetch():
 *  - FormData / URLSearchParams → pass through unchanged
 *  - plain objects → JSON.stringify
 *  - null/undefined → undefined
 */
function formatBody(body: unknown): BodyInit {
  if (body === null || body === undefined) return undefined as unknown as BodyInit;
  if (body instanceof URLSearchParams || body instanceof FormData) return body;
  if (typeof body === "object") return JSON.stringify(body);
  // Primitives (string/number/...) — wrap as string for safety.
  return String(body);
}

export const apiClient = {
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...restOptions } = options;

    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    let url = `${API_BASE_URL}${cleanEndpoint}`;

    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const defaultHeaders: Record<string, string> = {};

    // Do not set Content-Type when the body is FormData or URLSearchParams —
    // the browser must compute the multipart boundary itself.
    if (
      restOptions.body &&
      !(restOptions.body instanceof URLSearchParams) &&
      !(restOptions.body instanceof FormData)
    ) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        defaultHeaders["Authorization"] = `Bearer ${token.trim()}`;
      }
    }

    const finalHeaders: Record<string, string> = {
      ...defaultHeaders,
      ...((headers as Record<string, string>) ?? {}),
    };
    Object.keys(finalHeaders).forEach((key) => {
      if (finalHeaders[key] === undefined) {
        delete finalHeaders[key];
      }
    });

    const config: RequestInit = {
      ...restOptions,
      headers: finalHeaders,
    };

    const response = await fetch(url, config);

    // FE-6: central 401 handling. Clear token + cookie + force /login BEFORE
    // throwing so callers stop retrying with an expired token.
    if (response.status === 401) {
      handleUnauthorized();
      throw new Error("Session expired. Please sign in again.");
    }

    // FE-13: empty-body handling.
    //
    // Previously ANY response with content-length:0 (or a 204) was
    // short-circuited to `{}`. That broke GETs on chunked-transfer responses
    // where some servers omit Content-Length entirely — they'd arrive with a
    // `0` content-length header by mistake and we'd swallow the real JSON
    // body. Now:
    //   - 204 No Content → always `{}` (correct per RFC).
    //   - non-GET (POST/PUT/DELETE) with content-length:0 → `{}` (the typical
    //     "create returned nothing useful" case; mirrors DELETE semantics).
    //   - GET responses are NEVER short-circuited on content-length alone —
    //     we fall through to the normal JSON parse path (which gracefully
    //     handles a genuinely empty body via the catch below).
    const contentLength = response.headers.get("content-length");
    const isMethodWithNoBodyExpected =
      restOptions.method !== "GET" && restOptions.method !== "HEAD";
    if (
      response.status === 204 ||
      (isMethodWithNoBodyExpected && contentLength === "0")
    ) {
      return {} as T;
    }

    const contentType = response.headers.get("content-type");

    if (contentType && contentType.includes("application/json")) {
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          typeof errorData.detail === "string"
            ? errorData.detail
            : Array.isArray(errorData.detail)
              ? errorData.detail[0]?.msg
              : `HTTP Error: ${response.status}`;
        throw new Error(errorMessage);
      }
      // FE-13: tolerate genuinely-empty 200/2xx JSON bodies (e.g. an empty
      // list endpoint that returns "" instead of "[]") without throwing
      // "Unexpected end of JSON input".
      const text = await response.text();
      if (!text || text.trim() === "") {
        return {} as T;
      }
      try {
        return JSON.parse(text) as T;
      } catch {
        // Malformed JSON — surface a clear error rather than crashing.
        throw new Error(
          `Server returned malformed JSON (HTTP ${response.status}).`,
        );
      }
    }

    // Non-JSON response (e.g. PDF download stream).
    const textData = await response.text();
    if (!response.ok) {
      throw new Error(`Server status ${response.status}: ${textData.substring(0, 100)}`);
    }
    return textData as unknown as T;
  },

  get<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  },

  post<T>(
    endpoint: string,
    body: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> {
    const formattedBody: BodyInit = formatBody(body);
    return this.request<T>(endpoint, { ...options, method: "POST", body: formattedBody });
  },

  put<T>(
    endpoint: string,
    body: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> {
    const formattedBody: BodyInit = formatBody(body);
    return this.request<T>(endpoint, { ...options, method: "PUT", body: formattedBody });
  },

  delete<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  },
};
