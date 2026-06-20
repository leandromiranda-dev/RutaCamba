"""access.py — Punto de entrada del Módulo A (Re-ID).

Jose (Fase 2-B): implementa verify_identity.

CONTRATO (no cambiar la firma — Nicole la usa desde la API):
    def verify_identity(declared_id: str, probe_image) -> dict:
        # {"access": bool, "distance": float, "top1_identity": str, "topk": [...]}

DECISIÓN (ver fase2_decisiones_jose.md Decisión 003):
    El umbral REID_THRESHOLD = 0.65 es el punto de partida de config.py.
    En el notebook 02b se ajusta con ROC/EER usando los pares reales de la
    galería. Ese valor se actualiza en REID_THRESHOLD antes de la defensa.
    Aquí se carga desde config para que sea el único lugar de verdad.
"""

import logging
from typing import Optional

from src import config
from src.reid.gallery import load_gallery, get_identity_names
from src.reid.ranking import rank_identities

logger = logging.getLogger(__name__)

# ── Singleton de galería ──────────────────────────────────────────────────────
# Se carga una sola vez cuando llega el primer request.
# Evita releer disco en cada llamada a verify_identity.
_gallery: Optional[dict] = None
_gallery_loaded: bool = False


def _get_gallery() -> Optional[dict]:
    """Carga la galería desde disco (singleton, thread-safe en un solo proceso)."""
    global _gallery, _gallery_loaded
    if not _gallery_loaded:
        _gallery = load_gallery(cache_path=config.GALLERY_DIR + "/gallery_cache.pkl")
        _gallery_loaded = True
        if _gallery is None:
            logger.error(
                "⚠️  Galería vacía — verify_identity rechazará todas las solicitudes. "
                "Ejecutá build_gallery() de Leandro (embeddings.py) y luego save_gallery()."
            )
    return _gallery


def reload_gallery() -> None:
    """Fuerza la recarga de la galería desde disco (útil post-build_gallery).

    Llamar cuando Leandro haya regenerado la galería y se quiera actualizar
    sin reiniciar el servidor.
    """
    global _gallery, _gallery_loaded
    _gallery_loaded = False
    _gallery = None
    logger.info("Cache de galería reseteado. Se recargará en el próximo request.")


# ── Función principal del contrato ────────────────────────────────────────────

def verify_identity(declared_id: str, probe_image) -> dict:
    """Verifica si la selfie corresponde a la identidad declarada.

    Pipeline:
        1. Carga la galería (lazy, singleton).
        2. Valida que declared_id existe en la galería.
        3. Extrae el embedding facial de probe_image con DeepFace/ArcFace
           (via get_embedding de Leandro).
        4. Rankea la galería con distancia coseno (ranking.py).
        5. Concede acceso si top-1 == declared_id AND distancia < umbral.

    Args:
        declared_id:  identidad que el usuario dice ser (nombre en la galería).
        probe_image:  imagen de la selfie — puede ser ruta str o PIL.Image.

    Returns:
        dict con las claves:
          - ``access``        (bool)           — True solo si top-1 == declared_id y dist < umbral.
          - ``distance``      (float | None)   — distancia coseno del top-1, o None si no
            se pudo calcular (galería vacía, sin rostro detectado, etc.). None y no
            ``float("inf")`` porque Starlette serializa JSON con ``allow_nan=False``
            y rechaza Infinity.
          - ``top1_identity`` (str)   — identidad más cercana en la galería.
          - ``topk``          (list)  — lista de (identidad, distancia) top-5.
          - ``error``         (str, opcional) — mensaje si algo falló.
    """
    # ── 1. Cargar galería ─────────────────────────────────────────────────────
    gallery = _get_gallery()
    if gallery is None:
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": (
                "Galería no disponible. "
                "Ejecutá build_gallery() y save_gallery() antes de usar el sistema."
            ),
        }

    # ── 2. Validar declared_id ────────────────────────────────────────────────
    known_ids = get_identity_names(gallery)
    if declared_id not in known_ids:
        logger.warning(
            f"declared_id='{declared_id}' no existe en la galería. "
            f"Identidades registradas: {known_ids}"
        )
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": (
                f"La identidad '{declared_id}' no está registrada en el sistema. "
                f"Identidades disponibles: {known_ids}"
            ),
        }

    # ── 3. Extraer embedding de la selfie ─────────────────────────────────────
    # Importación local para no fallar si DeepFace no está instalado
    # y la API se inicia antes de que Leandro haya completado su parte.
    try:
        from src.reid.embeddings import get_embedding  # noqa: F401
    except ImportError as e:
        logger.error(f"No se pudo importar embeddings.py de Leandro: {e}")
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": "Módulo de embeddings no disponible. Verificá la instalación de DeepFace.",
        }

    probe_embedding = get_embedding(probe_image)

    if probe_embedding is None:
        logger.warning("No se detectó ningún rostro en la imagen provista.")
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": (
                "No se detectó ningún rostro en la imagen. "
                "Asegurate de subir una selfie con el rostro visible y bien iluminado."
            ),
        }

    # ── 4. Rankear galería ────────────────────────────────────────────────────
    try:
        ranked = rank_identities(probe_embedding, gallery, top_k=5)
    except ValueError as e:
        logger.error(f"Error en rank_identities: {e}")
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": str(e),
        }

    if not ranked:
        return {
            "access": False,
            "distance": None,
            "top1_identity": "",
            "topk": [],
            "error": "No se obtuvo ningún resultado del ranking.",
        }

    top1_identity, top1_distance = ranked[0]

    # ── 5. Decidir acceso ─────────────────────────────────────────────────────
    # DECISIÓN (Decisión 003): umbral desde config.REID_THRESHOLD.
    # Se actualiza con ROC/EER en el notebook 02b después de tener la galería real.
    threshold = config.REID_THRESHOLD
    identity_match = top1_identity == declared_id
    distance_ok = top1_distance < threshold
    access_granted = identity_match and distance_ok

    logger.info(
        f"verify_identity | declared='{declared_id}' | top1='{top1_identity}' "
        f"| dist={top1_distance:.4f} | threshold={threshold} "
        f"| match={identity_match} | dist_ok={distance_ok} | access={access_granted}"
    )

    return {
        "access": access_granted,
        "distance": float(top1_distance),
        "top1_identity": top1_identity,
        "topk": [(ident, float(dist)) for ident, dist in ranked],
    }
