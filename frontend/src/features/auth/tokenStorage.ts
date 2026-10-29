const REFRESH_TOKEN_KEY = "billable.refreshToken";

export const tokenStorage = {
  read(): string | null {
    try {
      return window.localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch {
      return null;
    }
  },
  write(token: string): void {
    try {
      window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } catch {
      return;
    }
  },
  clear(): void {
    try {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch {
      return;
    }
  },
};
