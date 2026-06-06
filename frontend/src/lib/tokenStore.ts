/**
 * In-memory storage for the access token.
 *
 * Storing the access token in memory instead of localStorage makes it
 * immune to Cross-Site Scripting (XSS) attacks.
 */

let accessToken: string | null = null;
const REFRESH_TOKEN_KEY = "careerpilot_refresh_token";

export const getToken = (): string | null => {
  return accessToken;
};

export const setToken = (token: string): void => {
  accessToken = token;
};

export const clearToken = (): void => {
  accessToken = null;
};

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

export const clearRefreshToken = (): void => {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};
