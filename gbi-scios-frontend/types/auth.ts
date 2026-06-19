export interface LoginFormData {
  email: string;
  password: string;
}

/** Mirrors the backend TokenResponse.user object. */
export interface UserProfile {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active?: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
