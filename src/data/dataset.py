"""dataset.py — PyTorch Dataset para el dataset de landmarks.

Implementado según docs/decisiones/fase1_decisiones_diego.md:
- Lee data/manifest.csv (columnas: path, class, split) y filtra por split.
- El `path` del manifest es el path original de Google Drive/Colab donde se
  hizo el EDA; localmente las imágenes viven en data/<split>/<class>/<archivo>
  (estructura ImageFolder, gitignored — cada quien las coloca ahí).
- Decisión 005: corrige la orientación EXIF con `ImageOps.exif_transpose()`
  antes de aplicar cualquier transform (PIL no rota automáticamente).
"""
import csv
import os
from pathlib import Path

from PIL import Image, ImageOps
from torch.utils.data import Dataset

from src.config import LANDMARK_CLASSES

MANIFEST_PATH = "data/manifest.csv"


def _read_manifest(manifest_path: str, split: str) -> list[tuple[str, str]]:
    """Devuelve [(filename, class_name), ...] para las filas del split pedido."""
    rows = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["split"] != split:
                continue
            filename = Path(row["path"]).name
            rows.append((filename, row["class"]))
    return rows


class LandmarkDataset(Dataset):
    def __init__(self, split: str, root: str = "data", manifest_path: str = MANIFEST_PATH, transform=None):
        if split not in ("train", "val", "test"):
            raise ValueError(f"split debe ser 'train', 'val' o 'test', recibido: {split!r}")

        self.root = root
        self.split = split
        self.transform = transform
        self.samples = _read_manifest(manifest_path, split)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        filename, class_name = self.samples[idx]
        image_path = os.path.join(self.root, self.split, class_name, filename)

        image = Image.open(image_path).convert("RGB")
        image = ImageOps.exif_transpose(image)

        if self.transform is not None:
            image = self.transform(image)

        label = LANDMARK_CLASSES.index(class_name)
        return image, label
