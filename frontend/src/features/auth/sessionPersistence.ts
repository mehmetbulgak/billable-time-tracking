const SESSION_KEY = "billable.hasSession";
const LEGACY_TOKEN_KEY = "billable.refreshToken";

export const sessionPersistence = {
  read(): boolean {
    try {
      window.localStorage.removeItem(LEGACY_TOKEN_KEY);
      return window.localStorage.getItem(SESSION_KEY) === "1";
    } catch {
      return false;
    }
  },
  write(): void {
    try {
      window.localStorage.removeItem(LEGACY_TOKEN_KEY);
      window.localStorage.setItem(SESSION_KEY, "1");
    } catch {
      return;
    }
  },
  clear(): void {
    try {
      window.localStorage.removeItem(LEGACY_TOKEN_KEY);
      window.localStorage.removeItem(SESSION_KEY);
    } catch {
      return;
    }
  },
};
