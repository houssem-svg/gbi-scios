"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { authService } from "@/lib/authService";
import { UserProfile } from "@/types/auth";

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  login: (data: any) => Promise<void>;
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
    async function initializeAuth() {
      if (authService.isAuthenticated()) {
        // تم تجاوز getCurrentUser مؤقتاً لعدم وجود مسار /me في الباكيند
        setUser({ id: "executive-user", email: "admin@gbi-scios.com", role: "admin" });
      } else if (pathname.startsWith("/dashboard")) {
        router.push("/login");
      }
      setLoading(false);
    }
    initializeAuth();
  }, [pathname, router]);

  const login = async (data: any) => {
    setLoading(true);
    try {
      await authService.login(data);
      // حقن كائن مستخدم محلي لتجاوز قيد الـ Null ومتابعة التحويل
      setUser({ id: "executive-user", email: data.email, role: "admin" });
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