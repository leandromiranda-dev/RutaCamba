"""ranking.py — Ranking por distancia coseno entre probe y galería.

Jose (Fase 2-B): implementa rank_identities.
Dado el embedding de una selfie (probe) y la galería, devuelve el ranking
ordenado de menor a mayor distancia coseno.
"""

import numpy as np
from typing import List, Tuple


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula la distancia coseno entre dos vectores.

    Distancia coseno = 1 - similitud_coseno.
    Rango [0, 2]: 0 = vectores idénticos, 2 = vectores opuestos.
    1 = vectores ortogonales (sin relación).

    Con ArcFace los embeddings suelen estar L2-normalizados, por lo que
    la similitud coseno equivale al producto punto.

    Args:
        a: primer vector de embedding.
        b: segundo vector de embedding.

    Returns:
        Distancia coseno en [0, 2].
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0  # máxima distancia si algún vector es cero
    similarity = np.dot(a, b) / (norm_a * norm_b)
    # Clamp para evitar valores fuera de [-1, 1] por errores de punto flotante
    similarity = float(np.clip(similarity, -1.0, 1.0))
    return 1.0 - similarity


def rank_identities(
    probe_embedding: np.ndarray,
    gallery: dict,
    aggregation: str = "min",
) -> List[Tuple[str, float]]:
    """Rankea identidades de la galería por distancia coseno al probe.

    Para identidades con múltiples fotos (varios embeddings), agrega las
    distancias individuales usando la estrategia indicada.

    DECISIÓN TÉCNICA (✍️ Decisión 002):
    Se usa aggregation="min" (distancia mínima) en lugar del promedio.
    Justificación: si una persona tiene N fotos, queremos saber si su MEJOR
    foto coincide con el probe. El promedio penaliza con fotos de mala calidad
    (mala iluminación, oclusión). En verificación de identidad, UNA buena
    coincidencia es suficiente para confirmar quién es la persona.

    Args:
        probe_embedding: embedding del rostro del probe (selfie del usuario).
        gallery: {identidad: [np.ndarray, ...]} — galería de Leandro.
        aggregation: "min" (recomendado) o "mean".

    Returns:
        Lista de (identidad, distancia) ordenada de MENOR a MAYOR distancia.
        La primera entrada es la identidad más cercana (top-1).
    """
    if aggregation not in ("min", "mean"):
        raise ValueError(f"aggregation debe ser 'min' o 'mean', no '{aggregation}'")

    distances: List[Tuple[str, float]] = []

    for identity, embeddings in gallery.items():
        if not embeddings:
            continue

        # Distancia coseno del probe contra cada foto de esta identidad
        individual_dists = [
            cosine_distance(probe_embedding, np.array(emb))
            for emb in embeddings
        ]

        # Agregar: mínimo = la mejor coincidencia, media = coincidencia promedio
        if aggregation == "min":
            agg_dist = float(min(individual_dists))
        else:  # mean
            agg_dist = float(np.mean(individual_dists))

        distances.append((identity, agg_dist))

    # Ordenar de menor a mayor (el más parecido primero)
    distances.sort(key=lambda x: x[1])
    return distances
