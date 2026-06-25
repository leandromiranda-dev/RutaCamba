// session.ts — token + identidad + rol en sessionStorage.
// Se usa sessionStorage (no localStorage) para que la sesión expire al cerrar
// la pestaña/app, acorde a la naturaleza privada del flujo tras Re-ID.

export type Role = "user" | "admin";

export interface Session {
  token: string;
  identity: string;
  role: Role;
}

const KEY = "rutacamba.session";

export function saveSession(s: Session): void {
  sessionStorage.setItem(KEY, JSON.stringify(s));
}

export function getSession(): Session | null {
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  sessionStorage.removeItem(KEY);
}

export function isAdmin(): boolean {
  return getSession()?.role === "admin";
}
