import { apiClient } from "./api";
import { LoginFormData, AuthResponse, UserProfile } from "@/types/auth";

export const authService = {
  async login(data: LoginFormData): Promise<AuthResponse> {
    const formBody = new URLSearchParams();
    formBody.append("username", data.email);
    formBody.append("password", data.password);

    const response = await apiClient.post<AuthResponse>("/auth/login", formBody, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    if (response && response.access_token) {
      localStorage.setItem("access_token", response.access_token);
      // تم إزالة Secure وتعديل SameSite إلى Lax لكي يُحفظ الكوكيز بنجاح محلياً
      document.cookie = `access_token=${response.access_token}; path=/; max-age=3600; SameSite=Lax`;
    }
    return response;
  },

  logout(): void {
    localStorage.removeItem("access_token");
    // تحديث الإعدادات هنا أيضاً لتنظيف الجلسة بشكل صحيح
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
  },

  isAuthenticated(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("access_token");
  },
};