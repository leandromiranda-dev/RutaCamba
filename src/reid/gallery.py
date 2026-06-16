"""gallery.py — Carga y gestión de la galería de identidades.

Jose (Fase 2-B): carga y guarda la galería cacheada en disco para no
recalcular embeddings con DeepFace en cada arranque del servidor.

La galería es el dict {identidad: [embedding, embedding, ...]}
que construye build_gallery() de Leandro (embeddings.py).

DECISIÓN (ver fase2_decisiones_jose.md Decisión 001):
  Se persiste con pickle porque los embeddings son np.ndarray de
  dimensión fija (ArcFace 512-d). JSON no es apto para arrays numéricos
  grandes. pickle es O(1) de carga vs recalcular con DeepFace (~1s/imagen).
"""

import logging
import os
import pickle
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Ruta por defecto del cache de la galería
_DEFAULT_CACHE = "data/gallery/gallery_cache.pkl"


def load_gallery(cache_path: str = _DEFAULT_CACHE) -> Optional[dict]:
    """Carga la galería cacheada desde disco.

    Lee el archivo .pkl generado por save_gallery (o directamente por
    build_gallery de Leandro si él ya serializa).

    Args:
        cache_path: ruta al archivo pickle. Por defecto usa
                    ``data/gallery/gallery_cache.pkl``.

    Returns:
        dict ``{identidad: [np.ndarray, ...]}`` con los embeddings por
        identidad, o ``None`` si el archivo no existe todavía
        (primera ejecución antes de llamar a build_gallery).
    """
    if not os.path.exists(cache_path):
        logger.warning(
            f"Galería no encontrada en '{cache_path}'. "
            "Llamá primero a build_gallery() de embeddings.py y luego a save_gallery()."
        )
        return None

    try:
        with open(cache_path, "rb") as f:
            gallery: dict = pickle.load(f)

        # Validación básica: cada valor debe ser lista de np.ndarray
        for identity, embeddings in gallery.items():
            if not isinstance(embeddings, list) or len(embeddings) == 0:
                raise ValueError(
                    f"La galería tiene formato incorrecto para identidad '{identity}'."
                )

        n_identities = len(gallery)
        n_embeddings = sum(len(v) for v in gallery.values())
        logger.info(
            f"Galería cargada: {n_identities} identidades, "
            f"{n_embeddings} embeddings totales — desde '{cache_path}'"
        )
        return gallery

    except (pickle.UnpicklingError, ValueError, EOFError) as e:
        logger.error(f"Error al cargar la galería desde '{cache_path}': {e}")
        return None


def save_gallery(gallery: dict, cache_path: str = _DEFAULT_CACHE) -> None:
    """Persiste la galería en disco como archivo pickle.

    Llama a esta función después de build_gallery() de Leandro para no
    recalcular embeddings en cada arranque.

    Args:
        gallery:    dict ``{identidad: [np.ndarray, ...]}`` devuelto por
                    build_gallery().
        cache_path: ruta de destino. El directorio se crea si no existe.

    Raises:
        TypeError: si gallery no es un dict con listas de np.ndarray.
    """
    if not isinstance(gallery, dict):
        raise TypeError(f"gallery debe ser un dict, no {type(gallery).__name__}.")

    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)

    with open(cache_path, "wb") as f:
        pickle.dump(gallery, f, protocol=pickle.HIGHEST_PROTOCOL)

    n_identities = len(gallery)
    n_embeddings = sum(len(v) for v in gallery.values())
    logger.info(
        f"Galería guardada: {n_identities} identidades, "
        f"{n_embeddings} embeddings — en '{cache_path}'"
    )


def get_identity_names(gallery: dict) -> list:
    """Devuelve la lista de identidades registradas en la galería.

    Útil para validar que el ``declared_id`` del usuario existe antes
    de computar el embedding de la selfie.

    Args:
        gallery: dict devuelto por load_gallery() o build_gallery().

    Returns:
        Lista de strings con los nombres/IDs de identidades.
    """
    return list(gallery.keys())
