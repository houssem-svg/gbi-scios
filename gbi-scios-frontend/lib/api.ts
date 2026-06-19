// gbi-scios-frontend/lib/api.ts

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    document.cookie =
      "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
  } catch {
    // ignore
  }
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

function formatBody(body: unknown): BodyInit {
  if (body === null || body === undefined) return undefined as unknown as BodyInit;
  if (body instanceof URLSearchParams || body instanceof FormData) return body;
  if (typeof body === "object") return JSON.stringify(body);
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

    if (response.status === 401) {
      handleUnauthorized();
      throw new Error("Session expired. Please sign in again.");
    }

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
      const text = await response.text();
      if (!text || text.trim() === "") {
        return {} as T;
      }
      try {
        return JSON.parse(text) as T;
      } catch {
        throw new Error(
          `Server returned malformed JSON (HTTP ${response.status}).`,
        );
      }
    }

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

  patch<T>(
    endpoint: string,
    body: unknown,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> {
    const formattedBody: BodyInit = formatBody(body);
    return this.request<T>(endpoint, { ...options, method: "PATCH", body: formattedBody });
  },

  delete<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  },
};
