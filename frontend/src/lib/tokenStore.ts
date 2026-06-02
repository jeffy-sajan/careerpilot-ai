/**
 * In-memory storage for the access token.
 * 
 * Storing the access token in memory instead of localStorage makes it
 * immune to Cross-Site Scripting (XSS) attacks. 
 */

let accessToken: string | null = null;

export const getToken = (): string | null => {
  return accessToken;
};

export const setToken = (token: string): void => {
  accessToken = token;
};

export const clearToken = (): void => {
  accessToken = null;
};
