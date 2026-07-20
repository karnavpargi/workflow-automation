import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ApiClient } from "../api/client";

export type Role = "admin" | "member" | "client";

export interface AuthUser {
  id: number;
  email: string;
  role: Role;
}

export interface AuthContextValue {
  user: AuthUser | null;
  accessToken: string | null;
  api: ApiClient;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setTenantSlug: (slug: string) => void;
  tenantSlug: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "wa.auth.v1";

interface StoredState {
  accessToken: string | null;
  user: AuthUser | null;
  tenantSlug: string | null;
}

function loadStored(): StoredState {
  if (typeof window === "undefined") {
    return { accessToken: null, user: null, tenantSlug: null };
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { accessToken: null, user: null, tenantSlug: null };
    return JSON.parse(raw) as StoredState;
  } catch {
    return { accessToken: null, user: null, tenantSlug: null };
  }
}

function persist(state: StoredState) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const initial = useMemo(loadStored, []);
  const [accessToken, setAccessToken] = useState<string | null>(initial.accessToken);
  const [user, setUser] = useState<AuthUser | null>(initial.user);
  const [tenantSlug, setTenantSlugState] = useState<string | null>(initial.tenantSlug);

  const setTenantSlug = useCallback((slug: string) => {
    setTenantSlugState(slug);
  }, []);

  const api = useMemo(
    () =>
      new ApiClient({
        getAccessToken: () => accessToken,
        getTenantSlug: () => tenantSlug,
      }),
    [accessToken, tenantSlug]
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.post<{ access: string; user: AuthUser }>(
        "/api/auth/token/",
        { username: email, password }
      );
      setAccessToken(tokens.access);
      setUser(tokens.user);
    },
    [api]
  );

  const logout = useCallback(() => {
    setAccessToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    persist({ accessToken, user, tenantSlug });
  }, [accessToken, user, tenantSlug]);

  const value: AuthContextValue = {
    user,
    accessToken,
    api,
    login,
    logout,
    setTenantSlug,
    tenantSlug,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
