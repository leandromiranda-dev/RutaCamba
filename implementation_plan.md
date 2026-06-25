# Implementation Plan — RutaCamba (nueva interfaz web + flujo completo)

> Objetivo: reemplazar la UI de Gradio por una interfaz **moderna y profesional en
> React**, e implementar el flujo completo del producto: identificación facial →
> control de acceso por rol → identificación del lugar → información del LLM en el
> idioma elegido → chat conversacional opcional → panel de administración para
> registrar nuevas personas.

---

## 1. Estado actual (lo que ya existe)

| Capa | Componente | Estado |
|------|-----------|--------|
| Backend | `api/main.py` (FastAPI) | `/verify`, `/predict`, `/normalize` funcionando |
| Re-ID | `src/reid/access.py::verify_identity` | Verifica identidad declarada contra galería ArcFace |
| Galería | `src/reid/gallery.py` | `load_gallery` / `save_gallery` / `get_identity_names` (pickle) |
| Embeddings | `src/reid/embeddings.py` | `get_embedding` / `build_gallery` (contrato de Leandro) |
| Landmarks | `src/landmarks/predictor.py` | `LandmarkPredictor.predict` (8 clases) |
| Traducción/LLM | `src/translation/translate.py` | `get_landmark_translations` (es/en/fr/it) + `normalize_input` (Claude + NLLB fallback) |
| UI | `ui/app.py` (**Gradio**) | **A REEMPLAZAR** |
| Sesiones | en memoria en `api/main.py` | tokens con TTL (`TOKEN_TTL`) |

**Lo que NO existe todavía y hay que construir:**
- Concepto de **rol** (`user` / `admin`) por identidad.
- Endpoint de **chat conversacional** sobre el lugar.
- Endpoint de **información del lugar en idioma arbitrario** (hoy solo hay 4 idiomas pre-generados).
- Endpoint de **enrolamiento** (admin agrega persona con foto + nombre + rol).
- Frontend en React.

---

## 2. Stack de la nueva interfaz (DECISIÓN CERRADA)

**Stack elegido: Vite + React + TypeScript + Tailwind CSS + shadcn/ui, como PWA
(mobile-first). Capacitor queda como camino opcional para publicar en tiendas
(Google Play / App Store) reusando el mismo código.**

### Por qué Vite (y no Next.js)

El producto debe ser **web app y, sobre todo, usarse como app móvil** (selfie de
identificación, foto del lugar en la calle, chat). Vite encaja mejor que Next.js
para este caso:

- **Es una app privada tras Re-ID** → no hay contenido público; SSR/SEO (la gran
  ventaja de Next.js) no aporta nada aquí.
- **Todo es client-side** (cámara, sesión en `sessionStorage`, chat) → con
  Next.js casi todo iría marcado como `"use client"` de todas formas.
- **PWA + Capacitor requieren salida estática (SPA)**, que es justo lo que Vite
  produce de forma natural. Next.js gira alrededor del servidor; para empaquetarlo
  habría que forzar *static export* y perder lo que lo hace atractivo.
- **Despliegue más simple y portable**: un único bundle estático corre igual en
  navegador, como PWA instalada y dentro de Capacitor.

### "Web app y app" con un solo código

| Cliente | Cómo | Codebase | Tiendas |
|---------|------|----------|---------|
| Navegador (web app) | bundle estático servido por CDN | el mismo | — |
| App móvil instalable | **PWA** (`vite-plugin-pwa`): ícono, pantalla completa, cámara | el mismo | no (se instala desde el navegador) |
| App en Google Play / App Store | **Capacitor** envuelve la misma SPA → `.apk` / `.ipa` | el mismo | sí |

### Componentes del stack

- **React moderno y profesional** sin construir el sistema de diseño desde cero:
  shadcn/ui da componentes accesibles (botones, cards, dialog, tabs, toast) sobre
  Tailwind, fáciles de personalizar.
- **Cámara**: `react-webcam` (MediaDevices API) funciona en navegador y PWA. Con
  Capacitor se puede sustituir por `@capacitor/camera` (cámara nativa) detrás del
  mismo componente `CameraCapture` — sin tocar el resto de la app.
- **PWA**: `vite-plugin-pwa` (manifest + service worker) para instalación y
  arranque a pantalla completa.
- El backend Python (FastAPI) **se mantiene tal cual** y separado; la app (web,
  PWA o Capacitor) solo le pega por `fetch`. Respeta el principio actual de
  "la UI nunca carga modelos".

### Diseño mobile-first (requisito por ser "más usado por app")

- Layouts pensados primero para pantalla de celular; botones grandes; cámara a
  pantalla completa.
- Manejo explícito de permisos de cámara, con estado claro de "permiso denegado".
- Navegación por pasos pensada para el pulgar (stepper vertical, no tabs densas).

Estructura del frontend (carpeta nueva `web/`):

```
web/                        # app Vite + React (PWA)
  public/
    manifest.webmanifest    # PWA: nombre, íconos, display: standalone
    icons/                  # íconos de la app (instalación móvil)
  src/
    pages/                  # o routes/ con react-router
      Login.tsx             # paso 1: selfie + nombre
      Tour.tsx              # paso 2-4: foto lugar → idioma → info → chat
      Admin.tsx             # panel admin: enrolar personas
    components/
      CameraCapture.tsx     # captura de cámara reutilizable (webcam / Capacitor)
      AccessGate.tsx        # muestra concedido/denegado
      LanguageSelect.tsx
      PlaceInfoCard.tsx
      ChatPanel.tsx
      EnrollForm.tsx
      ui/                   # componentes shadcn
    lib/
      api.ts                # cliente fetch tipado de la API
      session.ts            # token + rol en sessionStorage
    App.tsx
    main.tsx
  vite.config.ts            # incluye vite-plugin-pwa
  capacitor.config.ts       # (opcional) empaquetado nativo para tiendas
  package.json
```

---

## 3. Flujo del producto (UX objetivo)

```
┌─ 1. LOGIN ───────────────────────────────────────────────┐
│  Usuario escribe su nombre + toma selfie con la cámara    │
│  → POST /verify                                           │
│  ├─ access=false → pantalla "Acceso denegado"             │
│  └─ access=true  → guarda {token, identity, role}         │
└───────────────────────────────────────────────────────────┘
        │ role == "admin"                │ role == "user"
        ▼                                ▼
┌─ navegación admin ──────┐      (va directo al tour)
│  [ Turismo ] [ Admin ]  │
└─────────┬───────────────┘
          │ Turismo (ambos roles)
          ▼
┌─ 2. IDENTIFICAR LUGAR ───────────────────────────────────┐
│  Toma foto del lugar → POST /predict                      │
│  → landmark_id + confianza + top-k                        │
└───────────────────────────────────────────────────────────┘
          ▼
┌─ 3. ELEGIR IDIOMA ───────────────────────────────────────┐
│  Selector de idioma (es/en/fr/it/… )                      │
└───────────────────────────────────────────────────────────┘
          ▼
┌─ 4. INFO DEL LUGAR (LLM) ────────────────────────────────┐
│  POST /place/info {landmark_id, language} → descripción   │
└───────────────────────────────────────────────────────────┘
          ▼
┌─ 5. CHAT (OPCIONAL) ─────────────────────────────────────┐
│  Si el LLM está disponible, el usuario sigue preguntando  │
│  POST /chat {landmark_id, language, history, message}     │
│  Si el LLM NO está disponible → se oculta el chat         │
└───────────────────────────────────────────────────────────┘

Solo ADMIN:
┌─ ADMIN: ENROLAR PERSONA ─────────────────────────────────┐
│  Nombre + rol + 1..N fotos del rostro → POST /enroll      │
│  → agrega embedding a la galería y persiste               │
└───────────────────────────────────────────────────────────┘
```

---

## 4. Cambios en el backend

### 4.0 Modelo de persistencia (dos capas) — REQUISITO

Separar explícitamente lo que **persiste en disco** de lo que es **efímero**:

| Dato | Qué representa | Dónde vive | ¿Sobrevive reinicio? |
|------|----------------|-----------|----------------------|
| **Galería** (`data/gallery/gallery_cache.pkl`) | quién puede acceder (embeddings faciales) | **disco** | **Sí** |
| **Roles** (`data/roles.json`) | rol de cada identidad (`user`/`admin`) | **disco** | **Sí** |
| **Sesiones / tokens** (`_sessions` en `api/main.py`) | login activo de un usuario | **memoria** | **No** (mueren al apagar el servidor) |

Esto cumple el requisito: cuando un **admin enrola a una persona**, su rostro y su
rol **quedan registrados en disco**, así que sigue teniendo acceso aunque el
servidor se reinicie. Lo único efímero es el **token de sesión**: al reiniciar,
cada persona vuelve a identificarse con su selfie, pero su **acceso ya está
registrado** y la verificación pasa.

> **Despliegue**: para que esta persistencia funcione en la nube, el backend
> necesita un **disco/volumen persistente** montado donde vive `data/` (ver §7.2).
> En un hosting sin volumen, los archivos se perderían en cada redeploy.

**Escrituras atómicas**: tanto `roles.json` como la galería se guardan escribiendo
a un archivo temporal y haciendo `os.replace()` (rename atómico). Así un corte a
mitad de escritura nunca deja el archivo corrupto.

### 4.1 Roles por identidad (persistentes)

Hoy la galería es `{identidad: [embedding, ...]}` sin metadata de rol. Añadir un
store de roles **persistido en disco**, desacoplado para no romper el formato de
la galería.

- **Nuevo archivo `data/roles.json`**: `{"jose": "admin", "maria": "user", ...}`.
- **Nuevo módulo `src/reid/roles.py`**:
  ```python
  def load_roles() -> dict                   # lee data/roles.json (o {} si no existe)
  def get_role(identity: str) -> str         # "admin" | "user" (default "user")
  def set_role(identity: str, role: str) -> None  # actualiza y reescribe atómicamente el JSON
  ```
- `set_role` **escribe a disco inmediatamente** (temp + `os.replace`), de modo que
  el cambio persiste sin depender de un apagado ordenado.
- Identidades sin entrada explícita → rol `"user"` por defecto.
- Sembrar al menos un admin inicial en `data/roles.json` (commiteado) para poder
  entrar al panel la primera vez.

### 4.2 `/verify` — devolver rol

Modificar `api/main.py::verify` para incluir el rol en la respuesta y en la sesión:

```python
role = get_role(declared_id)
_sessions[token] = {"identity": declared_id, "role": role,
                    "expires_at": time.time() + TOKEN_TTL}
return {"access": True, "token": token, "identity": declared_id, "role": role}
```

`_require_session` debe seguir devolviendo identidad; añadir helper
`_require_admin(token)` que valide `role == "admin"` y lance 403 si no.

### 4.3 `/place/info` — información del lugar en el idioma elegido (NUEVO)

El flujo pide "seleccionar el idioma y que el LLM dé info del lugar". Las 4
traducciones pre-generadas (`get_landmark_translations`) cubren es/en/fr/it sin
red. Para idioma elegido y texto más rico:

```
POST /place/info
  Form: token, landmark_id, language
  → { "landmark_id", "language", "name", "description", "chat_available": bool }
```

- Si `language ∈ {es,en,fr,it}` y existe en `translations.json` → lookup O(1)
  (sin latencia, sin costo). 
- Si no, o si se quiere descripción extendida → llamar al LLM (Claude) con un
  prompt de "guía turística de Santa Cruz" en el idioma pedido.
- `chat_available` = `True` solo si el cliente Anthropic está inicializado
  (`TranslationService._anthropic_client is not None`). El frontend usa esto
  para mostrar u ocultar el chat (requisito: el chat es **opcional / solo si se puede**).

Implementar en `src/translation/translate.py` un método nuevo
`get_place_info(landmark_id, language) -> dict` que reutilice el lookup y caiga
al LLM/NLLB según corresponda.

### 4.4 `/chat` — conversación sobre el lugar (NUEVO, opcional)

```
POST /chat
  JSON: { token, landmark_id, language, message,
          history: [{role:"user"|"assistant", content:str}, ...] }
  → { "reply": str }   (o 503 si el LLM no está disponible)
```

- System prompt: "Eres un guía turístico de Santa Cruz de la Sierra. Responde
  SOLO sobre `{nombre del landmark}` en el idioma `{language}`. Si te preguntan
  por otra cosa, redirige amablemente al lugar."
- Mantiene la conversación pasando `history` (la API es stateless respecto al
  chat; el historial lo guarda el frontend).
- Si `_anthropic_client is None` → responder `503` y el frontend nunca muestra
  el chat (se apoya en `chat_available`).
- Usar el modelo Claude vigente (ver `src/translation/translate.py`, hoy
  `claude-sonnet-4-20250514`; revisar/actualizar al id vigente del proyecto).

### 4.5 `/enroll` — registrar nueva persona (NUEVO, solo admin)

```
POST /enroll
  Form: token (admin), name, role ("user"|"admin"), images: UploadFile[]
  → { "ok": true, "identity": name, "embeddings_added": int }
```

Pipeline (todo el registro **persiste en disco** antes de responder):
1. `_require_admin(token)`.
2. Por cada imagen → `get_embedding(img)`; descartar las que no detectan rostro.
3. Si no se obtuvo ningún embedding → 422 "No se detectó rostro".
4. Cargar galería actual, agregar/extender `gallery[name] = [emb, ...]`,
   **`save_gallery(...)` → escribe el pickle a disco** (persistente), y
   `reload_gallery()` (ya existe en `access.py`) para que el nuevo registro tenga
   efecto inmediato sin reiniciar.
5. **`set_role(name, role)` → reescribe `data/roles.json` a disco** (atómico).
6. Recién entonces responder `ok: true`. Si falla el guardado, devolver 500 y no
   dejar el estado a medias (no agregar a la galería en memoria sin persistir).

A partir de aquí, la persona enrolada **puede identificarse y entrar** en
cualquier momento, incluso tras reiniciar el servidor, porque su rostro (galería)
y su rol (roles.json) viven en disco.

> Nota: `get_embedding` / `build_gallery` son el contrato de Leandro
> (`src/reid/embeddings.py`) — hoy `NotImplementedError`. El enrolamiento depende
> de que esa parte esté implementada. Si no lo está, dejar el endpoint y marcar
> la dependencia.

### 4.6 CORS

Como el frontend corre en otro origen (p. ej. `localhost:3000`), añadir
`CORSMiddleware` en `api/main.py` permitiendo el origen del frontend.

### 4.7 Resumen de contratos de API (post-cambios)

| Método | Endpoint | Auth | Propósito |
|--------|----------|------|-----------|
| POST | `/verify` | — | selfie + nombre → `{access, token, identity, role}` |
| POST | `/predict` | token | foto lugar → `{landmark_id, confidence, top_k, translations}` |
| POST | `/place/info` | token | `{landmark_id, language}` → info en idioma elegido + `chat_available` |
| POST | `/chat` | token | conversación sobre el lugar (503 si no hay LLM) |
| POST | `/enroll` | admin | nombre + rol + fotos → agrega a galería |
| POST | `/normalize` | — | (se mantiene) normaliza consulta a español |

---

## 5. Frontend — componentes y pantallas

### 5.1 `lib/api.ts`
Cliente tipado con `fetch`. Lee `NEXT_PUBLIC_API_URL` (o `VITE_API_URL`).
Funciones: `verify`, `predict`, `placeInfo`, `chat`, `enroll`. Maneja
`FormData` para subidas de imágenes y `application/json` para chat.

### 5.2 `components/CameraCapture.tsx`
Componente reutilizable basado en `react-webcam`:
- Vista previa de cámara + botón "Capturar".
- Devuelve un `Blob`/`File` (JPEG) para enviar a la API.
- Permite "volver a tomar". Usado en login, en tour y en enrolamiento.

### 5.3 `app/login`
- Input de nombre (shadcn `Input`) + `CameraCapture`.
- Botón "Verificar identidad" → `verify`.
- Resultado:
  - **denegado**: card roja con el `top1_identity` más cercano.
  - **concedido**: guarda sesión y redirige (`admin` → dashboard con tabs;
    `user` → `/tour`).

### 5.4 `app/tour` (flujo turístico, ambos roles)
Wizard de pasos (shadcn `Tabs` o estado local con stepper):
1. **Capturar lugar** → `predict` → muestra `PlaceInfoCard` con landmark + confianza (`Badge` con top-k).
2. **Elegir idioma** → `LanguageSelect` (es/en/fr/it + otros si se habilita LLM).
3. **Info del lugar** → `placeInfo` → render de nombre + descripción.
4. **Chat** → `ChatPanel`, visible **solo si** `chat_available === true`.

### 5.5 `components/ChatPanel.tsx`
- Lista de mensajes (burbujas usuario/asistente).
- Input + envío → `chat` con el `history` acumulado en estado.
- Indicador de "escribiendo…"; deshabilitado si el LLM no está disponible.

### 5.6 `app/admin` (solo admin)
- **Guard de ruta**: si `role !== "admin"` → redirige a `/tour`.
- Navegación con `Tabs`: **Turismo** (reusa `/tour`) y **Administración**.
- `EnrollForm`: nombre + selector de rol + `CameraCapture` (permitir 1..N
  capturas para mejor galería) → `enroll`. Toast de éxito/error.

### 5.7 `lib/session.ts`
Guarda `{token, identity, role}` en `sessionStorage` (no `localStorage`, para
que expire al cerrar). Helper `useSession()` (hook/context). Limpia al expirar
el token (401 de la API).

---

## 6. Plan de ejecución por fases

| # | Fase | Entregable | Depende de |
|---|------|-----------|-----------|
| 0 | Scaffolding frontend | `web/` con Vite + React + TS + Tailwind + shadcn + `vite-plugin-pwa` inicializado (mobile-first) | — |
| 1 | Cliente API + sesión | `lib/api.ts`, `lib/session.ts`, CORS en backend | 0 |
| 2 | Login + Re-ID | `app/login` + `CameraCapture`; `/verify` devolviendo rol; `roles.py` + `data/roles.json` | 1 |
| 3 | Tour: identificar lugar | `app/tour` paso 1-2 contra `/predict` | 2 |
| 4 | Info del lugar | `/place/info` + `get_place_info`; render en frontend | 3 |
| 5 | Chat opcional | `/chat` + `ChatPanel` (gated por `chat_available`) | 4 |
| 6 | Panel admin + enrolamiento | `app/admin`, `EnrollForm`, `/enroll`, guard de rol | 2 (y `get_embedding` de Leandro) |
| 7 | Pulido visual + PWA | tema, mobile-first, estados de carga/error, accesibilidad, manifest + service worker | 3-6 |
| 8 | Despliegue | build estático del frontend + deploy; backend FastAPI desplegado; (opcional) build Capacitor | 7 |
| 9 | Limpieza | retirar/archivar `ui/app.py` (Gradio), actualizar README y `requirements` | todas |

---

## 7. Despliegue

El producto se despliega en **dos piezas independientes**: el frontend estático
(web/PWA) y el backend FastAPI. La app móvil opcional sale del mismo frontend.

### 7.1 Frontend (web app + PWA)
- `npm run build` → genera `web/dist/` (estático: HTML/JS/CSS + service worker).
- Se sirve desde cualquier hosting estático / CDN: **Vercel, Netlify o Cloudflare
  Pages** (deploy directo desde el repo). También puede servirlo Nginx o el propio
  FastAPI como estáticos.
- Variable de entorno `VITE_API_URL` apuntando a la URL pública del backend.
- Al ser PWA, desde el navegador móvil se puede **"Instalar app"** (ícono en la
  pantalla de inicio, arranque a pantalla completa).
- Requiere **HTTPS** (obligatorio para acceso a cámara y para PWA) — los hostings
  citados lo dan por defecto.

### 7.2 Backend (FastAPI + modelos)
- Se despliega aparte en un servidor Python con CPU suficiente (los modelos
  ArcFace/landmarks corren ahí): **Render, Railway, Fly.io o una VM**.
- Configurar `ANTHROPIC_API_KEY` (habilita chat e idiomas extra) y CORS con el
  origen del frontend.
- Persistir `data/gallery/` y `data/roles.json` (volumen) para que el
  enrolamiento sobreviva reinicios.

### 7.3 App en tiendas (opcional, Capacitor)
- `npx cap add android` / `npx cap add ios` sobre el `web/dist/` ya construido.
- `npx cap sync` tras cada build; genera `.apk` / `.ipa` para Google Play / App
  Store. No requiere reescribir la app — reusa el mismo bundle.

---

## 8. Decisiones abiertas / riesgos

1. **`get_embedding` / `build_gallery` sin implementar** (`src/reid/embeddings.py`):
   el login Re-ID y el enrolamiento **dependen** de la parte de Leandro. Hasta
   que esté, se puede mockear para desarrollar el frontend.
2. **Idiomas del chat/info**: las 4 traducciones pre-generadas son offline; más
   idiomas o descripción conversacional requieren `ANTHROPIC_API_KEY`. Sin clave,
   el chat se oculta automáticamente (degradación elegante, ya contemplada).
3. **Persistencia de roles/galería** (REQUISITO, ver §4.0): galería (pickle) y
   roles (JSON) **persisten en disco** con escritura atómica → el enrolamiento
   sobrevive reinicios. En la nube **requiere un volumen persistente** (§7.2); sin
   él, un redeploy borraría los registros. Si más adelante se requiere
   multiusuario concurrente o escritura desde varias réplicas, migrar a una DB
   (p. ej. SQLite → Postgres) — el archivo local no es seguro con concurrencia alta.
4. **Seguridad / sesiones**: los **tokens de sesión son en memoria** (sin JWT/DB),
   por diseño: la sesión activa dura hasta que el servidor se apaga, pero el
   **acceso (galería + rol) persiste**. Al reiniciar, el usuario solo vuelve a
   identificarse con su selfie. Documentarlo como limitación conocida.
5. **Modelo Claude**: verificar el id de modelo vigente en `translate.py` antes
   de la entrega.
6. **Capacitor (tiendas)**: solo si se decide publicar en Google Play / App
   Store. La web app + PWA cubren el uso "como app" sin pasar por tiendas.

---

## 9. Criterios de aceptación

- [ ] Un usuario `user` se autentica con selfie + nombre y, si el Re-ID coincide,
      accede; si no, ve "acceso denegado".
- [ ] Tras acceder, toma foto de un lugar y obtiene su identificación.
- [ ] Selecciona idioma y recibe información del lugar en ese idioma.
- [ ] Si el LLM está disponible, puede conversar sobre el lugar; si no, el chat
      no aparece (no rompe el flujo).
- [ ] Un `admin` ve además el panel de administración y puede registrar a una
      persona nueva (nombre + rol + foto), que luego puede autenticarse.
- [ ] La UI es React, moderna y responsive; Gradio queda retirado.
```

