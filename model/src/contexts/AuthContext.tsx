import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi, type AuthResponse, type LoginData } from "@/api/auth";

export type UserRole = "student" | "staff" | "admin";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (data: LoginData) => Promise<void>;
  logout: () => void;
  setAuthFromResponse: (resp: AuthResponse) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>(() => {
    const saved = localStorage.getItem("laundry_auth");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return { ...parsed, isAuthenticated: !!parsed.token };
      } catch { /* ignore */ }
    }
    return { token: null, refreshToken: null, role: null, isAuthenticated: false };
  });

  useEffect(() => {
    if (auth.token) {
      localStorage.setItem("laundry_auth", JSON.stringify(auth));
    } else {
      localStorage.removeItem("laundry_auth");
    }
  }, [auth]);

  const setAuthFromResponse = useCallback((resp: AuthResponse) => {
    setAuth({
      token: resp.access_token,
      refreshToken: resp.refresh_token,
      role: resp.role as UserRole,
      isAuthenticated: true,
    });
  }, []);

  const login = useCallback(async (data: LoginData) => {
    const resp = await authApi.login(data);
    setAuthFromResponse(resp);
  }, [setAuthFromResponse]);

  const logout = useCallback(() => {
    setAuth({ token: null, refreshToken: null, role: null, isAuthenticated: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...auth, login, logout, setAuthFromResponse }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
