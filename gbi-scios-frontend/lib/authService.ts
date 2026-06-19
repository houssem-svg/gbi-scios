import { apiClient } from "./api";
import { LoginFormData, AuthResponse, UserProfile } from "@/types/auth";

/**
 * FE-12 (HIGH — cookie security):
 *
 * The current flow stores the JWT in BOTH `localStorage` and a
 * `document.cookie` (the cookie exists only so the Next.js middleware
 * can read it for route protection — see middleware.ts). This is
 * inherently less secure than an httpOnly cookie because JS can read
 * the token out of localStorage.
 *
 * The proper fix is a backend change: have the FastAPI `/auth/login`
 * endpoint return the access_token via a `Set-Cookie:
 * access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600`
 * response header. Once that lands, the frontend should:
 *   1. Stop reading the token from the response body into localStorage.
 *   2. Stop setting the cookie here in JS.
 *   3. Rely on the browser auto-sending the httpOnly cookie on every
 *      fetch (which requires `credentials: 'include'` on apiClient).
 *
 * Until the backend ships that change, we tighten the JS-set cookie
 * here by adding `Secure` whenever the page is served over HTTPS
 * (so production HTTPS deployments get the flag, while localhost dev
 * over http:// is not broken).
 */
function buildAuthCookie(token: string, maxAgeSeconds: number): string {
  const isHttps =
    typeof window !== "undefined" &&
    window.location.protocol === "https:";
  const secureFlag = isHttps ? "; Secure" : "";
  // SameSite=Lax kept for dev compatibility (http://localhost).
  return `access_token=${token}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax${secureFlag}`;
}

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
      // FE-12: cookie gets Secure flag when running on HTTPS.
      document.cookie = buildAuthCookie(response.access_token, 3600);
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
    // Expire the cookie on every protocol.
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
