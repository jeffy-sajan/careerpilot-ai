import { apiClient } from "../axios";
import {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  RefreshRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from "../../types/auth";

/**
 * Raw API call functions for Authentication.
 * These functions abstract away the HTTP methods and paths.
 */
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>("/auth/register", data);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  refresh: async (data: RefreshRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/refresh", data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    // You noted POST /auth/logout in your endpoints list.
    // If it's not fully implemented in the backend yet, this will just hit the route.
    // It is primarily used to invalidate the refresh token on the server.
    await apiClient.post("/auth/logout").catch(() => {
      // Ignore errors on logout (e.g., if token is already expired/invalid)
    });
  },

  forgotPassword: async (
    data: ForgotPasswordRequest,
  ): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(
      "/auth/forgot-password",
      data,
    );
    return response.data;
  },

  resetPassword: async (
    data: ResetPasswordRequest,
  ): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(
      "/auth/reset-password",
      data,
    );
    return response.data;
  },
};
