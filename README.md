# RutaCamba — Sistema de Asistencia Turística Inteligente

Sistema de clasificación de landmarks de Santa Cruz de la Sierra con verificación
de identidad facial (Re-ID), control de acceso por rol, información multilingüe
generada/curada por LLM y chat conversacional sobre cada lugar.

El producto son **dos piezas independientes**:

| Pieza | Carpeta | Stack | Rol |
|-------|---------|-------|-----|
| **Frontend** | [`web/`](web) | Vite + React + TS + Tailwind + PWA | App web e instalable (mobile-first) |
| **Backend**  | [`api/`](api) | FastAPI + PyTorch + DeepFace + Anthropic | API de inferencia y sesión |

La interfaz Gradio anterior quedó archivada en [`ui/`](ui) (legacy).

## Flujo del producto

```
1. LOGIN     selfie + nombre  → POST /verify  → {token, identity, role}
             ├─ access=false → "Acceso denegado"
             └─ access=true  → user → /tour   |   admin → /admin
2. LUGAR     foto del lugar   → POST /predict    → landmark + top-k
3. IDIOMA    selector es/en/fr/it (+ más si hay LLM)
4. INFO      POST /place/info  → descripción en el idioma elegido
5. CHAT      POST /chat        → conversación (solo si chat_available)
ADMIN        nombre + rol + fotos → POST /enroll → agrega a la galería
```

## Backend (API)

```bash
pip install -r requirements.txt

# Arranque (puerto 8000)
uvicorn api.main:app --reload
```

Variables de entorno (`.env`):

- `ANTHROPIC_API_KEY` — habilita el chat e idiomas extra. Sin clave, el sistema
  sigue funcionando con las 4 traducciones offline (`data/translations.json`) y
  el chat se oculta automáticamente.
- `CORS_ORIGINS` — orígenes permitidos del frontend (coma-separados). Default:
  `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000`.
- `REID_MOCK=1` — **modo desarrollo**: simula el Re-ID y el enrolamiento para
  probar el frontend de punta a punta sin la galería ArcFace real. Identidades
  válidas en mock: `jose` (admin), `maria`, `demo`. Sin esta variable se usa la
  galería real (`src/reid/embeddings.py` — parte de Leandro).

### Endpoints

| Método | Endpoint | Auth | Propósito |
|--------|----------|------|-----------|
| POST | `/verify` | — | selfie + nombre → `{access, token, identity, role}` |
| POST | `/predict` | token | foto lugar → `{landmark_id, confidence, top_k, translations}` |
| POST | `/place/info` | token | `{landmark_id, language}` → info + `chat_available` |
| POST | `/chat` | token | conversación sobre el lugar (503 si no hay LLM) |
| POST | `/enroll` | admin | nombre + rol + fotos → agrega a la galería |
| POST | `/normalize` | — | normaliza una consulta a español |
| GET  | `/health` | — | healthcheck |

## Frontend (web/)

```bash
cd web
npm install
cp .env.example .env        # ajustá VITE_API_URL si el backend no está en :8000
npm run dev                 # desarrollo (http://localhost:5173)
npm run build               # build estático en web/dist/ (incluye PWA)
```

Requiere **HTTPS** en producción (obligatorio para cámara y PWA). Se sirve desde
cualquier hosting estático (Vercel, Netlify, Cloudflare Pages) o como estáticos
del propio FastAPI. Opcionalmente se empaqueta para tiendas con Capacitor.

## WandB

Proyecto: `rutacamba`.

## Documentación

- [implementation_plan.md](implementation_plan.md) — plan de la interfaz web.
- [context.md](context.md) — mapa de carpetas y responsables.
