// api.ts — cliente tipado de la API RutaCamba (FastAPI).
import { clearSession, type Role } from "./session";

const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    // Sesión expirada → limpiar para forzar re-login.
    clearSession();
  }
  if (!res.ok) {
    let detail: unknown = null;
    let message = `Error ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body;
      if (typeof detail === "string") message = detail;
      else if (detail && typeof detail === "object" && "hint" in detail)
        message = String((detail as Record<string, unknown>).hint);
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new ApiError(res.status, detail, message);
  }
  return (await res.json()) as T;
}

// ── Tipos de respuesta ────────────────────────────────────────────────────────

export interface VerifyResponse {
  access: boolean;
  token: string;
  identity: string;
  role: Role;
}

export type TopK = [string, number][];

export interface LangPair {
  nombre: string;
  descripcion: string;
}

export interface PredictResponse {
  identity: string;
  landmark_id: string;
  confidence: number;
  top_k: TopK;
  translations: Record<string, LangPair>;
  chat_available: boolean;
}

export interface PlaceInfoResponse {
  landmark_id: string;
  language: string;
  name: string;
  description: string;
  source: "offline" | "llm" | "fallback";
  chat_available: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface EnrollResponse {
  ok: boolean;
  identity: string;
  embeddings_added: number;
  mock?: boolean;
}

// ── Endpoints ──────────────────────────────────────────────────────────────────

export async function verify(
  declaredId: string,
  selfie: Blob
): Promise<VerifyResponse> {
  const fd = new FormData();
  fd.append("declared_id", declaredId);
  fd.append("selfie", selfie, "selfie.jpg");
  const res = await fetch(`${API_URL}/verify`, { method: "POST", body: fd });
  return handle<VerifyResponse>(res);
}

export async function predict(
  token: string,
  image: Blob,
  k = 3
): Promise<PredictResponse> {
  const fd = new FormData();
  fd.append("token", token);
  fd.append("image", image, "place.jpg");
  fd.append("k", String(k));
  const res = await fetch(`${API_URL}/predict`, { method: "POST", body: fd });
  return handle<PredictResponse>(res);
}

export async function placeInfo(
  token: string,
  landmarkId: string,
  language: string
): Promise<PlaceInfoResponse> {
  const fd = new FormData();
  fd.append("token", token);
  fd.append("landmark_id", landmarkId);
  fd.append("language", language);
  const res = await fetch(`${API_URL}/place/info`, { method: "POST", body: fd });
  return handle<PlaceInfoResponse>(res);
}

export async function chat(
  token: string,
  landmarkId: string,
  language: string,
  message: string,
  history: ChatMessage[]
): Promise<{ reply: string }> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token,
      landmark_id: landmarkId,
      language,
      message,
      history,
    }),
  });
  return handle<{ reply: string }>(res);
}

export async function enroll(
  token: string,
  name: string,
  role: Role,
  images: Blob[]
): Promise<EnrollResponse> {
  const fd = new FormData();
  fd.append("token", token);
  fd.append("name", name);
  fd.append("role", role);
  images.forEach((img, i) => fd.append("images", img, `face_${i}.jpg`));
  const res = await fetch(`${API_URL}/enroll`, { method: "POST", body: fd });
  return handle<EnrollResponse>(res);
}
