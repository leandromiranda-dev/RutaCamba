"""embeddings.py — Embeddings faciales con DeepFace/ArcFace.

Leandro (Fase 2-A): implementá get_embedding y build_gallery.

CONTRATO (no cambiar las firmas):
    def get_embedding(image) -> np.ndarray: ...
    def build_gallery(gallery_dir: str) -> dict: ...
"""
import numpy as np

# TODO (Leandro): implementar get_embedding y build_gallery


def get_embedding(image) -> np.ndarray:
    raise NotImplementedError("Leandro (Fase 2-A): implementá get_embedding()")


def build_gallery(gallery_dir: str) -> dict:
    raise NotImplementedError("Leandro (Fase 2-A): implementá build_gallery()")
