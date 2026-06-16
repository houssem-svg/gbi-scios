const BASE_URL = "http://127.0.0.1:8000/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

export const apiClient = {
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...restOptions } = options;
    
    // تأمين إضافة الـ Slash النهائي لمنع إعادة التوجيه وإسقاط التوكن
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    let url = `${BASE_URL}${cleanEndpoint}`;
    
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const defaultHeaders: Record<string, string> = {};
    
    if (!(restOptions.body instanceof URLSearchParams)) {
      defaultHeaders["Content-Type"] = "application/json";
    }
    
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        defaultHeaders["Authorization"] = `Bearer ${token.trim()}`;
      }
    }

    const config: RequestInit = {
      ...restOptions,
      headers: {
        ...defaultHeaders,
        ...headers,
      },
    };

    const response = await fetch(url, config);

    // 1. معالجة حالات الاستجابة الفارغة (مثل حذف مشروع بنجاح 204) لمنع تفجير الـ JSON Decoder
    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return {} as T;
    }

    // 2. التحقق مما إذا كانت الاستجابة القادمة من السيرفر هي فعلياً JSON أم نص عادي
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
      // إذا أرجع السيرفر نصاً عادياً أو خطأ HTML
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
    // 🛠️ الإصلاح الحاسم: تحويل الـ body إلى نص JSON نقي إذا لم يكن محولاً بالفعل
    const formattedBody = typeof body === "object" && !(body instanceof URLSearchParams) 
      ? JSON.stringify(body) 
      : body;

    return this.request<T>(endpoint, { ...options, method: "POST", body: formattedBody });
  },

  put<T>(endpoint: string, body: any, options?: Omit<RequestOptions, "method" | "body">): Promise<T> {
    // 🛠️ الإصلاح الحاسم: تحويل الـ body إلى نص JSON نقي إذا لم يكن محولاً بالفعل
    const formattedBody = typeof body === "object" && !(body instanceof URLSearchParams) 
      ? JSON.stringify(body) 
      : body;

    return this.request<T>(endpoint, { ...options, method: "PUT", body: formattedBody });
  },

  delete<T>(endpoint: string, options?: Omit<RequestOptions, "method">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  },
};
