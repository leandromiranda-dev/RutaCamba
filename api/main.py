"""api/main.py — API RutaCamba (Nicole, Fase 6).

Endpoints:
    POST /verify     → verifica identidad, devuelve token de sesión
    POST /predict    → clasifica landmark + traduce (requiere token)
    POST /normalize  → normaliza una consulta en idioma inesperado

Carga de modelos una sola vez en el startup (lifespan de FastAPI).
Los modelos NUNCA se re-entrenan desde la API.
"""
from dotenv import load_dotenv
load_dotenv()  # carga .env antes de que src.config lea os.getenv()

import io
import secrets
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image

from src.config import TOKEN_TTL
from src.landmarks.predictor import LandmarkPredictor
from src.reid.access import verify_identity
from src.translation.translate import TranslationService

# ── Estado global (cargado una sola vez en startup) ───────────────────────────
_predictor: Optional[LandmarkPredictor] = None
_translator: Optional[TranslationService] = None

# Sesiones en memoria: {token: {"identity": str, "expires_at": float}}
# No se usa JWT ni DB porque la demo no requiere persistencia entre reinicios.
_sessions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _predictor, _translator
    _predictor = LandmarkPredictor()
    _translator = TranslationService()
    yield
    _predictor = None
    _translator = None


app = FastAPI(title="RutaCamba API", version="1.0.0", lifespan=lifespan)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_session(token: str) -> str:
    """Valida el token y devuelve la identidad. Lanza 401 si es inválido/expirado."""
    session = _sessions.get(token)
    if not session or time.time() > session["expires_at"]:
        _sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Token inválido o sesión expirada.")
    return session["identity"]


def _read_image(upload: UploadFile) -> Image.Image:
    data = upload.file.read()
    return Image.open(io.BytesIO(data)).convert("RGB")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/verify")
async def verify(
    declared_id: str = Form(..., description="Nombre de identidad declarado por el usuario"),
    selfie: UploadFile = File(..., description="Foto del rostro del usuario"),
):
    """Verifica la identidad del usuario con Re-ID.

    - Devuelve `{"access": true, "token": "...", "identity": "..."}` si el rostro
      coincide con `declared_id` en la galería.
    - Devuelve 403 si el acceso es denegado.
    """
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

    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "identity": declared_id,
        "expires_at": time.time() + TOKEN_TTL,
    }
    return {"access": True, "token": token, "identity": declared_id}


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
    identity = _require_session(token)
    pil_image = _read_image(image)

    prediction = _predictor.predict(pil_image, k=k)
    translations = _translator.get_landmark_translations(prediction["landmark_id"])

    return {
        "identity": identity,
        "landmark_id": prediction["landmark_id"],
        "confidence": prediction["confidence"],
        "top_k": prediction["top_k"],
        "translations": translations,
    }


@app.post("/normalize")
async def normalize(
    query: str = Form(..., description="Consulta en cualquier idioma"),
):
    """Normaliza una consulta en idioma inesperado al español."""
    return _translator.normalize_input(query)
