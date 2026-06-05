import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { getToken, setToken, clearToken } from "./tokenStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  timeout: 10000,
});

// ─────────────────────────────────────────────────────────────────────────────
// Phase 5: Token Refresh Deduplication State
// When multiple requests fail with 401 simultaneously, only ONE refresh call
// is made. All other requests are queued and retried after the refresh.
// ─────────────────────────────────────────────────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token!);
  });
  failedQueue = [];
};

// ─────────────────────────────────────────────────────────────────────────────
// REQUEST INTERCEPTOR: Attach access token to every outgoing request
// ─────────────────────────────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ─────────────────────────────────────────────────────────────────────────────
// RESPONSE INTERCEPTOR: Handle 401 Unauthorized with silent token refresh
// ─────────────────────────────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    const is401 = error.response?.status === 401;
    const isRefreshEndpoint = originalRequest?.url?.includes("/auth/refresh");
    const alreadyRetried = originalRequest?._retry;

    if (!is401 || isRefreshEndpoint || alreadyRetried) {
      return Promise.reject(error);
    }

    // If a refresh is already in progress, queue this request
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((newToken) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return apiClient(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    // No refresh in progress — start one
    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Make the refresh call using a plain axios call (not apiClient) to
      // avoid triggering this interceptor recursively.
      const { data } = await axios.post(
        `${API_URL}/auth/refresh`,
        {},
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        },
      );

      // Store the new access token
      setToken(data.access_token);

      // Attach new token to the original failed request and retry it
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      }

      processQueue(null, data.access_token);
      return apiClient(originalRequest);
    } catch (refreshError) {
      // Refresh failed — clear everything and force logout
      processQueue(refreshError, null);
      clearToken();
      if (
        window.location.pathname !== "/login" &&
        window.location.pathname !== "/register" &&
        window.location.pathname !== "/auth/google/callback" &&
        window.location.pathname !== "/forgot-password" &&
        window.location.pathname !== "/reset-password"
      ) {
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
