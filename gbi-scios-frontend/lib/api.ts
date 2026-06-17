// src/lib/api.ts

const BASE_URL = "http://127.0.0.1:8000/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

export const apiClient = {
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...restOptions } = options;
    
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    let url = `${BASE_URL}${cleanEndpoint}`;
    
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const defaultHeaders: Record<string, string> = {};
    
    // 🚨 التعديل الحاسم الأول: عدم وضع application/json إذا كانت البيانات ملفات (FormData)
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

    // تنظيف الهيدرز من أي قيم undefined
    const finalHeaders = { ...defaultHeaders, ...headers };
    Object.keys(finalHeaders).forEach(key => {
      if ((finalHeaders as any)[key] === undefined) {
        delete (finalHeaders as any)[key];
      }
    });

    const config: RequestInit = {
      ...restOptions,
      headers: finalHeaders,
    };

    const response = await fetch(url, config);

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return {} as T;
    }

    const contentType = response.headers.get("content-type");
    let errorData: any = {};
    
    if (contentType && contentType.includes("application/json")) {
      if (!response.ok) {
        errorData = await response.json().catch(() => ({}));
        const errorMessage = typeof errorData.detail === "string" 
          ? errorData.detail 
          : Array.isArray(errorData.detail)
            ? errorData.detail[0]?.msg
            : `HTTP Error: ${response.status}`;
        throw new Error(errorMessage);
      }
      return response.json() as Promise<T>;
    } else {
      const textData = await response.text();
      if (!response.ok) {
        throw new Error(`Server status ${response.status}: ${textData.substring(0, 100)}`);
      }
      return textData as unknown as T;
    }
  },

  get<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  },

  post<T>(endpoint: string, body: any, options?: Omit<RequestOptions, "method" | "body">): Promise<T> {
    // 🚨 التعديل الحاسم الثاني: حماية الـ FormData من التحويل العشوائي إلى نص فارغ
    const formattedBody = typeof body === "object" && !(body instanceof URLSearchParams) && !(body instanceof FormData)
      ? JSON.stringify(body) 
      : body;

    return this.request<T>(endpoint, { ...options, method: "POST", body: formattedBody });
  },

  put<T>(endpoint: string, body: any, options?: Omit<RequestOptions, "method" | "body">): Promise<T> {
    const formattedBody = typeof body === "object" && !(body instanceof URLSearchParams) && !(body instanceof FormData)
      ? JSON.stringify(body) 
      : body;

    return this.request<T>(endpoint, { ...options, method: "PUT", body: formattedBody });
  },

  delete<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  },
};