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

- `OPENROUTER_API_KEY` — habilita el chat e idiomas extra (LLM vía OpenRouter +
  Gemini). Sin clave, el sistema sigue funcionando con las traducciones offline
  (`data/translations.json` / `_STATIC_TRANSLATIONS`) y el chat se oculta solo.
- `CORS_ORIGINS` — orígenes permitidos del frontend (coma-separados). Default:
  `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000`.
- `REID_MOCK=1` — **opcional, solo desarrollo**: simula el Re-ID y el enrolamiento
  para probar el frontend sin cámara/galería. Identidades mock: `jose` (admin),
  `maria`, `demo`. **Por defecto (sin esta variable) se usa el Re-ID real**
  (facenet_pytorch: MTCNN + InceptionResnetV1 / VGGFace2, 512-d).

**Galería de rostros (Re-ID real):** `src/reid/access.py` lee
`data/gallery/gallery_cache.pkl` (`{identidad: [embedding, ...]}`). Al arrancar, la
API genera ese cache automáticamente desde `data/gallery/embeddings_autorizados.pt`
(la base del motor biométrico) si aún no existe. Nuevas personas se agregan en
caliente vía `/enroll` (admin). Para regenerar todo desde imágenes:
`build_gallery()` + `save_gallery()` en `src/reid/`.

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

## Despliegue

**Backend** (Render / Railway / Fly.io / VM) — hay un `Dockerfile` listo:

```bash
docker build -t rutacamba-api .
docker run -p 8000:8000 --env-file .env rutacamba-api
```

Configurar `OPENROUTER_API_KEY`, `CORS_ORIGINS` (origen del frontend) y montar un
volumen en `data/gallery/` + `data/roles.json` para que el enrolamiento sobreviva
reinicios. La imagen respeta `$PORT`.

**Frontend** (Vercel / Netlify / Cloudflare Pages): build con `cd web && npm run build`,
publicar `web/dist/`. El routing SPA ya está resuelto: `web/vercel.json` (rewrites)
y `web/public/_redirects` (Netlify/CF) redirigen todo a `index.html` para que
`/tour` y `/admin` no den 404 al refrescar. Definir `VITE_API_URL` con la URL
pública del backend antes de buildear.

## WandB

Proyecto: `rutacamba`.

## Documentación

- [implementation_plan.md](implementation_plan.md) — plan de la interfaz web.
- [context.md](context.md) — mapa de carpetas y responsables.
