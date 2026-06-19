"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { authService } from "@/lib/authService";
import { LoginFormData, UserProfile } from "@/types/auth";

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  login: (data: LoginFormData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    function initializeAuth() {
      const hasToken = authService.isAuthenticated();
      const cachedUser = authService.getCachedUser();

      if (hasToken && cachedUser) {
        setUser(cachedUser);
      } else if (hasToken && !cachedUser) {
        // Token present but no user cached — clear token to force a re-login.
        authService.logout();
        setUser(null);
      } else if (!hasToken && pathname?.startsWith("/dashboard")) {
        router.push("/login");
      }
      setLoading(false);
    }
    initializeAuth();
    // Run only once on mount — the fake-user re-injection on every pathname
    // change (audit finding FE-4/MEDIUM) has been removed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (data: LoginFormData) => {
    setLoading(true);
    try {
      const loggedInUser = await authService.login(data);
      setUser(loggedInUser);
      router.push("/dashboard");
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
