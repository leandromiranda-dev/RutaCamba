"""api/main.py — API RutaCamba (FastAPI).

Endpoints:
    POST /verify     → verifica identidad, devuelve token de sesión + rol
    POST /predict    → clasifica landmark + traduce (requiere token)
    POST /place/info → info del lugar en el idioma elegido (requiere token)
    POST /chat       → conversación sobre el lugar (requiere token; 503 sin LLM)
    POST /enroll     → registra nueva persona (requiere token admin)
    POST /normalize  → normaliza una consulta en idioma inesperado

Carga de modelos una sola vez en el startup (lifespan de FastAPI).
Los modelos NUNCA se re-entrenan desde la API.

Modo desarrollo (REID_MOCK=1):
    Como `src/reid/embeddings.py` (parte de Leandro) todavía es NotImplementedError,
    con REID_MOCK=1 el Re-ID y el enrolamiento se simulan para poder desarrollar y
    demostrar el frontend de punta a punta. En producción se deja sin esa variable
    y la verificación usa la galería ArcFace real.
"""
from dotenv import load_dotenv
load_dotenv()  # carga .env antes de que src.config lea os.getenv()

import io
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from src.config import TOKEN_TTL
from src.landmarks.predictor import LandmarkPredictor
from src.reid.access import verify_identity
from src.reid.roles import get_role, set_role
from src.translation.translate import TranslationService

logger = logging.getLogger(__name__)

# ── Modo mock para desarrollo del frontend (sin la parte de Leandro) ──────────
REID_MOCK = os.getenv("REID_MOCK", "").lower() in ("1", "true", "yes")
# Identidades aceptadas en modo mock (declared_id → siempre concede acceso).
# El rol real sale de data/roles.json (get_role).
_MOCK_IDENTITIES = {"jose", "maria", "demo"}

# ── Estado global (cargado una sola vez en startup) ───────────────────────────
_predictor: Optional[LandmarkPredictor] = None
_translator: Optional[TranslationService] = None

# Sesiones en memoria: {token: {"identity": str, "role": str, "expires_at": float}}
# No se usa JWT ni DB porque la demo no requiere persistencia entre reinicios.
_sessions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _predictor, _translator
    _predictor = LandmarkPredictor()
    _translator = TranslationService()
    # Pre-carga los modelos de Re-ID para que el primer /verify no sea lento
    try:
        from src.reid.embeddings import _load_models
        _load_models()
        logger.info("Modelos Re-ID pre-cargados correctamente.")
    except Exception as e:
        logger.warning(f"No se pudieron pre-cargar los modelos Re-ID: {e}. Se cargarán en el primer /verify.")
    yield
    _predictor = None
    _translator = None


app = FastAPI(title="RutaCamba API", version="2.0.0", lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────────────────────────────
# El frontend (Vite) corre en otro origen (p. ej. localhost:5173). Se permite vía
# variable de entorno CORS_ORIGINS (lista separada por comas). Default: orígenes
# típicos de desarrollo de Vite.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_session(token: str) -> dict:
    """Valida el token y devuelve la sesión. Lanza 401 si es inválido/expirado."""
    session = _sessions.get(token)
    if not session or time.time() > session["expires_at"]:
        _sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Token inválido o sesión expirada.")
    return session


def _require_admin(token: str) -> dict:
    """Valida el token y exige rol admin. Lanza 403 si no lo es."""
    session = _require_session(token)
    if session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador.")
    return session


def _read_image(upload: UploadFile) -> Image.Image:
    data = upload.file.read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def _new_session(identity: str, role: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "identity": identity,
        "role": role,
        "expires_at": time.time() + TOKEN_TTL,
    }
    return token


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/verify")
async def verify(
    declared_id: str = Form(..., description="Nombre de identidad declarado por el usuario"),
    selfie: UploadFile = File(..., description="Foto del rostro del usuario"),
):
    """Verifica la identidad del usuario con Re-ID y devuelve token + rol.

    - `{"access": true, "token": "...", "identity": "...", "role": "user"|"admin"}`
      si el rostro coincide con `declared_id` en la galería.
    - 403 si el acceso es denegado.
    """
    declared_id = declared_id.strip()

    # ── Modo mock (desarrollo del frontend) ───────────────────────────────────
    if REID_MOCK:
        if declared_id.lower() not in _MOCK_IDENTITIES:
            raise HTTPException(
                status_code=403,
                detail={"access": False, "top1_identity": "", "distance": None,
                        "hint": f"En modo mock las identidades válidas son {sorted(_MOCK_IDENTITIES)}."},
            )
        role = get_role(declared_id)
        token = _new_session(declared_id, role)
        return {"access": True, "token": token, "identity": declared_id, "role": role}

    # ── Modo real (galería ArcFace) ───────────────────────────────────────────
    image = _read_image(selfie)
    result = verify_identity(declared_id, image)

    if not result["access"]:
        raise HTTPException(
            status_code=403,
            detail={
                "access": False,
                "top1_identity": result["top1_identity"],
                "distance": result["distance"],
            },
        )

    role = get_role(declared_id)
    token = _new_session(declared_id, role)
    return {"access": True, "token": token, "identity": declared_id, "role": role}


@app.post("/predict")
async def predict(
    token: str = Form(..., description="Token de sesión obtenido en /verify"),
    image: UploadFile = File(..., description="Foto del lugar a identificar"),
    k: int = Form(3, ge=1, le=8, description="Número de predicciones top-k"),
):
    """Clasifica el landmark en la imagen y devuelve las traducciones.

    Requiere un token válido de /verify. Devuelve landmark top-1, top-k con
    probabilidades, y traducciones en ES/EN/FR/IT.
    """
    session = _require_session(token)
    pil_image = _read_image(image)

    prediction = _predictor.predict(pil_image, k=k)
    translations = _translator.get_landmark_translations(prediction["landmark_id"])

    return {
        "identity": session["identity"],
        "landmark_id": prediction["landmark_id"],
        "confidence": prediction["confidence"],
        "top_k": prediction["top_k"],
        "translations": translations,
        "chat_available": _translator.chat_available,
    }


@app.post("/place/info")
async def place_info(
    token: str = Form(..., description="Token de sesión obtenido en /verify"),
    landmark_id: str = Form(..., description="ID del landmark identificado"),
    language: str = Form("es", description="Idioma deseado (es, en, fr, it, ...)"),
):
    """Devuelve la información del lugar en el idioma elegido.

    Lookup O(1) para es/en/fr/it; para otros idiomas usa el LLM si está
    disponible. `chat_available` indica si el frontend debe mostrar el chat.
    """
    _require_session(token)
    return _translator.get_place_info(landmark_id, language)


@app.post("/chat")
async def chat(payload: dict = Body(...)):
    """Conversación sobre el lugar. 503 si el LLM no está disponible.

    Body JSON: { token, landmark_id, language, message,
                 history: [{role, content}, ...] }
    """
    token = payload.get("token", "")
    _require_session(token)

    landmark_id = payload.get("landmark_id", "")
    language = payload.get("language", "es")
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []

    if not message:
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacío.")

    reply = _translator.chat_reply(landmark_id, language, message, history)
    if reply is None:
        raise HTTPException(
            status_code=503,
            detail="El chat no está disponible (LLM no configurado).",
        )
    return {"reply": reply}


@app.post("/enroll")
async def enroll(
    token: str = Form(..., description="Token de sesión de un administrador"),
    name: str = Form(..., description="Nombre de la nueva identidad"),
    role: str = Form("user", description="Rol: 'user' o 'admin'"),
    images: list[UploadFile] = File(..., description="1..N fotos del rostro"),
):
    """Registra una nueva persona (solo admin): agrega su rostro a la galería.

    En modo mock solo registra el rol (no hay embeddings reales). En modo real
    usa `get_embedding` de Leandro para extender la galería ArcFace.
    """
    _require_admin(token)
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío.")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=422, detail="Rol inválido (use 'user' o 'admin').")

    # ── Modo mock: registra identidad + rol sin embeddings ────────────────────
    if REID_MOCK:
        _MOCK_IDENTITIES.add(name.lower())
        set_role(name, role)
        return {"ok": True, "identity": name, "embeddings_added": 0, "mock": True}

    # ── Modo real: extiende la galería con embeddings ArcFace ─────────────────
    from src.reid.embeddings import get_embedding
    from src.reid.gallery import load_gallery, save_gallery
    from src.reid.access import reload_gallery
    from src.config import GALLERY_DIR

    cache_path = GALLERY_DIR + "/gallery_cache.pkl"
    embeddings = []
    for upload in images:
        pil = _read_image(upload)
        emb = get_embedding(pil)
        if emb is not None:
            embeddings.append(emb)

    if not embeddings:
        raise HTTPException(
            status_code=422,
            detail="No se detectó ningún rostro en las imágenes provistas.",
        )

    gallery = load_gallery(cache_path) or {}
    gallery.setdefault(name, [])
    gallery[name].extend(embeddings)
    save_gallery(gallery, cache_path)
    reload_gallery()
    set_role(name, role)

    return {"ok": True, "identity": name, "embeddings_added": len(embeddings)}


@app.post("/normalize")
async def normalize(
    query: str = Form(..., description="Consulta en cualquier idioma"),
):
    """Normaliza una consulta en idioma inesperado al español."""
    return _translator.normalize_input(query)


@app.get("/health")
async def health():
    """Healthcheck simple para el despliegue."""
    return {
        "status": "ok",
        "mock": REID_MOCK,
        "chat_available": _translator.chat_available if _translator else False,
    }
