import { apiClient } from "./api";
import { LoginFormData, AuthResponse, UserProfile } from "@/types/auth";

export const authService = {
  /**
   * POST /auth/login (OAuth2PasswordRequestForm: username=email, password)
   * Backend returns { access_token, token_type, user: {...} }. We persist both
   * the token (localStorage + cookie) and the user object (localStorage) so
   * the AuthProvider can hydrate on reload without a /me call.
   */
  async login(data: LoginFormData): Promise<UserProfile> {
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
      // SameSite=Lax (no Secure) so the cookie survives local dev over http.
      document.cookie = `access_token=${response.access_token}; path=/; max-age=3600; SameSite=Lax`;
    }

    const user = response?.user;
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    }
    return user;
  },

  logout(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    document.cookie =
      "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
  },

  isAuthenticated(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("access_token");
  },

  /** Returns the cached user object (if any) — no /me call. */
  getCachedUser(): UserProfile | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem("user");
    if (!raw) return null;
    try {
      return JSON.parse(raw) as UserProfile;
    } catch {
      return null;
    }
  },
};
