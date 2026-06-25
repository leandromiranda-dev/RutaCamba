"""embeddings.py — Embeddings faciales con facenet_pytorch (VGGFace2).

Usa InceptionResnetV1 (VGGFace2) + MTCNN, mismo modelo con el que se generó
la galería en data/gallery/biometria.py. Embedding 512-d, misma métrica coseno.
"""
import logging
import os
import pickle

import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

logger = logging.getLogger(__name__)

_mtcnn: MTCNN = None
_resnet: InceptionResnetV1 = None


def _load_models() -> None:
    global _mtcnn, _resnet
    if _mtcnn is None:
        _mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20)
        _resnet = InceptionResnetV1(pretrained="vggface2").eval()
        logger.info("Modelos facenet_pytorch cargados (VGGFace2, 512-d).")


def get_embedding(image) -> np.ndarray:
    """Detecta el rostro en `image` y devuelve su embedding 512-d.

    Args:
        image: ruta (str), PIL.Image, o np.ndarray RGB.

    Returns:
        np.ndarray de forma (512,), o None si no se detecta ningún rostro.
    """
    _load_models()

    if isinstance(image, str):
        img = Image.open(image).convert("RGB")
    elif isinstance(image, Image.Image):
        img = image.convert("RGB")
    else:
        img = Image.fromarray(np.array(image)).convert("RGB")

    face = _mtcnn(img)
    if face is None:
        logger.warning("MTCNN no detectó ningún rostro en la imagen.")
        return None

    with torch.no_grad():
        embedding = _resnet(face.unsqueeze(0))

    return embedding.squeeze().numpy()


def build_gallery(gallery_dir: str) -> dict:
    """Construye la galería escaneando imágenes en `gallery_dir`.

    Cada subdirectorio es una identidad; sus imágenes generan embeddings.
    Si no hay subdirectorios, todas las imágenes en la raíz se agrupan
    bajo el nombre de archivo sin extensión.

    Args:
        gallery_dir: directorio raíz con imágenes o subdirectorios.

    Returns:
        dict ``{identidad: [np.ndarray, ...]}`` listo para save_gallery().
    """
    _load_models()
    gallery: dict = {}
    supported = {".jpg", ".jpeg", ".png", ".webp"}

    entries = os.listdir(gallery_dir)
    subdirs = [e for e in entries if os.path.isdir(os.path.join(gallery_dir, e))]

    if subdirs:
        for identity in subdirs:
            folder = os.path.join(gallery_dir, identity)
            embeddings = []
            for fname in os.listdir(folder):
                if os.path.splitext(fname)[1].lower() in supported:
                    emb = get_embedding(os.path.join(folder, fname))
                    if emb is not None:
                        embeddings.append(emb)
            if embeddings:
                gallery[identity] = embeddings
                logger.info(f"Identidad '{identity}': {len(embeddings)} embeddings.")
    else:
        for fname in entries:
            if os.path.splitext(fname)[1].lower() in supported:
                identity = os.path.splitext(fname)[0]
                emb = get_embedding(os.path.join(gallery_dir, fname))
                if emb is not None:
                    gallery[identity] = [emb]
                    logger.info(f"Identidad '{identity}': 1 embedding.")

    return gallery
