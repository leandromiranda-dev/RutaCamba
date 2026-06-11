"""access.py — Punto de entrada del Módulo A (Re-ID).

Jose (Fase 2-B): implementa verify_identity.

CONTRATO (no cambiar la firma — Nicole la usa desde la API):
    def verify_identity(declared_id: str, probe_image) -> dict:
        # {"access": bool, "distance": float, "top1_identity": str, "topk": [...]}
"""

import logging

from src import config
from src.reid.embeddings import get_embedding
from src.reid.gallery import load_gallery
from src.reid.ranking import rank_identities

logger = logging.getLogger(__name__)

# ── Galería singleton (lazy) ───────────────────────────────────────────────────
# Se carga UNA SOLA VEZ en memoria para no repetir I/O en cada request.
_gallery_cache: dict | None = None


def _get_gallery() -> dict:
    """Carga la galería desde disco la primera vez; reutiliza el cache."""
    global _gallery_cache
    if _gallery_cache is None:
        _gallery_cache = load_gallery()
    return _gallery_cache


def reload_gallery() -> None:
    """Fuerza la recarga de la galería desde disco (útil si se actualizó)."""
    global _gallery_cache
    _gallery_cache = None
    logger.info("Cache de galería invalidado. Se recargará en el próximo request.")


# ── Función principal del contrato ────────────────────────────────────────────

def verify_identity(declared_id: str, probe_image) -> dict:
    """Verifica la identidad del usuario comparando su selfie con la galería.

    Concede acceso SOLO si:
      1. El top-1 de la galería coincide con declared_id.
      2. La distancia coseno es menor al umbral (config.REID_THRESHOLD).

    El umbral fue determinado empíricamente mediante curva ROC/EER en el
    notebook 02b_reid_ranking_metrics.ipynb (✍️ Decisión 003).

    CONTRATO — no modificar la firma:
        declared_id  : identidad que el usuario DECLARA ser (ej: "jose_alfredo").
        probe_image  : ruta al archivo de imagen (str) o PIL.Image de la selfie.

    Returns:
        {
            "access"       : bool,           # True → acceso concedido
            "distance"     : float,          # distancia coseno al top-1
            "top1_identity": str,            # identidad más cercana en la galería
            "topk"         : [(id, dist), ...]  # top-5 para debug / UI
        }
    """
    # ── 1. Obtener embedding del probe ────────────────────────────────────────
    try:
        probe_embedding = get_embedding(probe_image)
    except Exception as exc:
        logger.error(f"Error al obtener embedding del probe: {exc}")
        return _error_response(f"Error al procesar la imagen: {exc}")

    if probe_embedding is None:
        # DeepFace/ArcFace devuelve None si no detecta ningún rostro
        logger.warning("No se detectó ningún rostro en la imagen del probe.")
        return {
            "access": False,
            "distance": float("inf"),
            "top1_identity": "no_face_detected",
            "topk": [],
            "message": "No se detectó ningún rostro en la imagen. "
                       "Asegurate de subir una selfie con tu cara visible.",
        }

    # ── 2. Cargar galería y rankear ────────────────────────────────────────────
    try:
        gallery = _get_gallery()
    except FileNotFoundError as exc:
        logger.error(f"Galería no encontrada: {exc}")
        return _error_response(str(exc))

    if not gallery:
        return {
            "access": False,
            "distance": float("inf"),
            "top1_identity": "empty_gallery",
            "topk": [],
            "message": "La galería está vacía. Contactá al administrador.",
        }

    ranking = rank_identities(probe_embedding, gallery, aggregation="min")

    # ── 3. Decisión de acceso ─────────────────────────────────────────────────
    top1_identity, top1_distance = ranking[0]

    # DECISIÓN TÉCNICA (✍️ Decisión 003): umbral justificado con ROC/EER.
    # El valor 0.65 en config es el punto de partida; se actualiza tras el
    # análisis en el notebook 02b con el EER real del equipo.
    threshold = config.REID_THRESHOLD

    access_granted = (
        top1_identity == declared_id
        and top1_distance < threshold
    )

    if access_granted:
        logger.info(
            f"Acceso CONCEDIDO → declared={declared_id}, "
            f"top1={top1_identity}, dist={top1_distance:.4f}, umbral={threshold}"
        )
    else:
        logger.info(
            f"Acceso DENEGADO → declared={declared_id}, "
            f"top1={top1_identity}, dist={top1_distance:.4f}, umbral={threshold}"
        )

    return {
        "access": access_granted,
        "distance": round(top1_distance, 6),
        "top1_identity": top1_identity,
        "topk": ranking[:5],   # top-5 para visualización en la UI
    }


def _error_response(message: str) -> dict:
    """Respuesta estándar para casos de error irrecuperable."""
    return {
        "access": False,
        "distance": float("inf"),
        "top1_identity": "error",
        "topk": [],
        "message": message,
    }
