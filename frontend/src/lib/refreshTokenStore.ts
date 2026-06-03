/**
 * Temporary storage for the refresh token using localStorage.
 *
 * IMPORTANT: This is a development-phase approach.
 * TODO (Production): Remove this file entirely. The backend should set the
 * refresh token as an HttpOnly cookie via the Set-Cookie response header.
 * When that's done, the browser will send it automatically and JS will
 * never be able to read it, eliminating the XSS risk.
 */

const REFRESH_TOKEN_KEY = "careerpilot_rt";

export const getRefreshToken = (): string | null =>
  localStorage.getItem(REFRESH_TOKEN_KEY);

export const setRefreshToken = (token: string): void =>
  localStorage.setItem(REFRESH_TOKEN_KEY, token);

export const clearRefreshToken = (): void =>
  localStorage.removeItem(REFRESH_TOKEN_KEY);
