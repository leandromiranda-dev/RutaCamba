"""gallery.py — Carga y gestión de la galería de identidades.

Jose (Fase 2-B): implementa load_gallery y save_gallery.
La galería es el dict {identidad: [embedding, ...]} que construye build_gallery de Leandro.
"""

import os
import pickle
import logging

import numpy as np

logger = logging.getLogger(__name__)

# Ruta por defecto para el cache de la galería
_DEFAULT_CACHE = os.path.join("data", "gallery", "gallery_cache.pkl")


def load_gallery(cache_path: str = _DEFAULT_CACHE) -> dict:
    """Carga la galería de embeddings desde un archivo .pkl cacheado.

    La galería es construida por Leandro (build_gallery en embeddings.py) y
    serializada con save_gallery. Esta función levanta ese cache para que no
    se recalculen los embeddings en cada request.

    Args:
        cache_path: ruta al archivo .pkl (default: data/gallery/gallery_cache.pkl).

    Returns:
        dict: {identidad: [np.ndarray, ...]} — lista de embeddings por persona.

    Raises:
        FileNotFoundError: si el cache no existe aún.
    """
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"No se encontró la galería en '{cache_path}'.\n"
            "Paso necesario: correr build_gallery (Leandro, embeddings.py) "
            "y luego save_gallery() para generar el cache."
        )

    with open(cache_path, "rb") as f:
        gallery: dict = pickle.load(f)

    identities = list(gallery.keys())
    total_embeddings = sum(len(v) for v in gallery.values())
    logger.info(
        f"Galería cargada: {len(identities)} identidades, "
        f"{total_embeddings} embeddings totales. Ruta: {cache_path}"
    )
    return gallery


def save_gallery(gallery: dict, cache_path: str = _DEFAULT_CACHE) -> None:
    """Serializa la galería de embeddings a disco como .pkl.

    Llamar después de build_gallery (Leandro) para que load_gallery funcione.

    Args:
        gallery: {identidad: [np.ndarray, ...]} construido por build_gallery.
        cache_path: ruta de salida del .pkl.
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    with open(cache_path, "wb") as f:
        pickle.dump(gallery, f)

    total_embeddings = sum(len(v) for v in gallery.values())
    logger.info(
        f"Galería guardada: {len(gallery)} identidades, "
        f"{total_embeddings} embeddings → {cache_path}"
    )
