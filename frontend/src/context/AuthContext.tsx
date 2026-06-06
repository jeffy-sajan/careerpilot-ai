import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { User, TokenResponse } from "../types/auth";
import { authApi } from "../lib/api/auth";
import {
  getToken,
  setToken,
  clearToken,
  setRefreshToken,
  clearRefreshToken,
} from "../lib/tokenStore";

// ─────────────────────────────────────────────────────────────────────────────
// Context Shape
// ─────────────────────────────────────────────────────────────────────────────
interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (tokens: TokenResponse) => void;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ─────────────────────────────────────────────────────────────────────────────
// JWT Decode utility — reads exp without verifying signature (that's the
// backend's job). Used only to schedule a proactive refresh.
// ─────────────────────────────────────────────────────────────────────────────
const getTokenExpiry = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 : null; // Convert seconds → ms
  } catch {
    return null;
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// AuthProvider
// ─────────────────────────────────────────────────────────────────────────────
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Step 1: On mount, attempt to fetch the authenticated user ──────────────
  // If an access token exists in memory, the request interceptor attaches it.
  // If it gets a 401, the response interceptor silently tries to refresh.
  const { isLoading, data, isError } = useQuery({
    queryKey: ["authUser"],
    queryFn: authApi.getMe,
    retry: false,
    refetchOnWindowFocus: false,
    // Initialise with an existing token from memory, if present
    enabled: true,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data]);

  useEffect(() => {
    if (isError) setUser(null);
  }, [isError]);

  // ── Step 2 (Phase 5): Schedule a proactive refresh before token expires ────
  const scheduleProactiveRefresh = (accessToken: string) => {
    // Cancel any existing timer
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);

    const expiry = getTokenExpiry(accessToken);
    if (!expiry) return;

    // Refresh 60 seconds before the token expires
    const delay = expiry - Date.now() - 60_000;
    if (delay <= 0) return;

    refreshTimerRef.current = setTimeout(async () => {
      try {
        const tokens = await authApi.refresh();
        setToken(tokens.access_token);
        if (tokens.refresh_token) {
          setRefreshToken(tokens.refresh_token);
        }
        scheduleProactiveRefresh(tokens.access_token); // schedule the next refresh
      } catch {
        // Proactive refresh failed — reactive interceptor will catch the next 401
      }
    }, delay);
  };

  // ── Actions ───────────────────────────────────────────────────────────────
  const login = (tokens: TokenResponse) => {
    setToken(tokens.access_token);
    if (tokens.refresh_token) {
      setRefreshToken(tokens.refresh_token);
    }
    scheduleProactiveRefresh(tokens.access_token);
    // Refetch the user profile with the new token
    queryClient.invalidateQueries({ queryKey: ["authUser"] });
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore — we always clear client state regardless
    } finally {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      clearToken();
      clearRefreshToken();
      setUser(null);
      queryClient.setQueryData(["authUser"], null);
      queryClient.clear();
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []);

  // Also schedule proactive refresh on first load if a token is already in memory
  useEffect(() => {
    const token = getToken();
    if (token) scheduleProactiveRefresh(token);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ─────────────────────────────────────────────────────────────────────────────
// useAuth hook — throws if used outside AuthProvider
// ─────────────────────────────────────────────────────────────────────────────
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
