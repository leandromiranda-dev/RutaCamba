"""ranking.py — Ranking por distancia coseno entre probe y galería.

Jose (Fase 2-B): implementa rank_identities.

DECISIÓN (ver fase2_decisiones_jose.md Decisión 001):
  Distancia coseno sobre euclidiana porque ArcFace entrena con
  ArcFace loss que maximiza ángulo entre clases — la distancia coseno
  es la métrica natural para ese espacio.

DECISIÓN (ver fase2_decisiones_jose.md Decisión 002):
  Cuando una identidad tiene N fotos en la galería se usa la distancia
  MÍNIMA (best match). Razón: si al menos una foto coincide bien con
  la selfie, el sujeto está físicamente presente. El promedio castigaría
  identidades con fotos de mala calidad/ángulo.
"""

import logging
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Distancia coseno entre dos vectores 1-D normalizados.

    Retorna un valor en [0, 2]: 0 = idénticos, 1 = ortogonales, 2 = opuestos.
    ArcFace embeddings suelen rondar [0.5, 1.0] para distintas personas
    y [0.0, 0.5] para la misma persona.

    Args:
        a: vector de embedding (np.ndarray 1-D).
        b: vector de embedding (np.ndarray 1-D).

    Returns:
        Distancia coseno como float.
    """
    # Normalización L2 para estabilidad numérica
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        logger.warning("Embedding con norma 0 detectado; distancia devuelta = 1.0")
        return 1.0
    similarity = np.dot(a, b) / (norm_a * norm_b)
    # clip para evitar errores numéricos fuera de [-1, 1]
    similarity = float(np.clip(similarity, -1.0, 1.0))
    return 1.0 - similarity


def rank_identities(
    probe_embedding: np.ndarray,
    gallery: dict,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """Rankea identidades de la galería por distancia coseno al probe.

    Para identidades con múltiples fotos usa la distancia MÍNIMA
    (better-match strategy — ver decisión 002).

    Args:
        probe_embedding: embedding 1-D de la selfie del usuario
                         (devuelto por get_embedding de Leandro).
        gallery:         dict ``{identidad: [np.ndarray, ...]}``
                         (devuelto por load_gallery o build_gallery).
        top_k:           número de identidades top a devolver.

    Returns:
        Lista de tuplas ``(identidad, distancia)`` ordenada de menor
        a mayor distancia (el índice 0 es el top-1). Contiene como
        máximo ``min(top_k, len(gallery))`` elementos.

    Raises:
        ValueError: si probe_embedding es None o la galería está vacía.
    """
    if probe_embedding is None:
        raise ValueError("probe_embedding es None — no se detectó ningún rostro.")
    if not gallery:
        raise ValueError("La galería está vacía. Llamá primero a build_gallery().")

    scores: List[Tuple[str, float]] = []

    for identity, embeddings in gallery.items():
        if not embeddings:
            logger.warning(f"La identidad '{identity}' no tiene embeddings — se omite.")
            continue

        # Distancia mínima entre el probe y TODAS las fotos de la identidad
        distances = [cosine_distance(probe_embedding, emb) for emb in embeddings]
        min_dist = float(min(distances))
        scores.append((identity, min_dist))

    # Ordenar de menor a mayor distancia
    scores.sort(key=lambda x: x[1])

    ranked = scores[:top_k]
    if ranked:
        logger.debug(
            f"Top-1: '{ranked[0][0]}' (dist={ranked[0][1]:.4f}) | "
            f"top-{len(ranked)} calculado sobre {len(gallery)} identidades."
        )
    return ranked
