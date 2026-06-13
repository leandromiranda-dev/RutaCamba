"""predictor.py — Inferencia con TorchScript.

Alejandro (Fase 3): implementación de LandmarkPredictor.

CONTRATO (no cambiar la firma — Nicole la usa desde la API):
    class LandmarkPredictor:
        def __init__(self, model_path: str = "models/transfer_learning.pt"): ...
        def predict(self, image, k: int = 3) -> dict:
            # {"landmark_id": str, "confidence": float, "top_k": [(id, prob), ...]}

Decisiones documentadas en: docs/decisiones/fase3_decisiones_alejandro.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from src.config import (
    CROP,
    IMAGENET_MEAN,
    IMAGENET_STD,
    LANDMARK_CLASSES,
    RESIZE,
)


# Preprocesamiento idéntico al de evaluación (sin augmentation).
# Se define a nivel de módulo para no reconstruirlo en cada llamada a predict().
_EVAL_TRANSFORM = transforms.Compose([
    transforms.Resize(RESIZE),
    transforms.CenterCrop(CROP),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


class LandmarkPredictor:
    """Carga un modelo TorchScript y expone predict() para la API (Fase 6).

    Decisión de diseño: recibe str (ruta) o PIL.Image para flexibilidad —
    la API puede pasarle una ruta de archivo temporal o una imagen ya abierta.
    Internamente siempre convierte a RGB antes de transformar, porque imágenes
    con canal alpha (RGBA) o en escala de grises romperían la normalización.
    """

    def __init__(self, model_path: str = "models/transfer_learning.pt") -> None:
        """Carga el modelo TorchScript una sola vez en memoria.

        Decisión: torch.jit.load() en lugar de reconstruir la clase TuristCNN
        porque TorchScript es independiente del código fuente — la API no necesita
        importar src.landmarks.cnn para hacer inferencia.
        """
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en '{path}'. "
                "Entrenás primero con train.py y exportás con export_torchscript()."
            )

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = torch.jit.load(str(path), map_location=self._device)
        self._model.eval()
        self._classes = LANDMARK_CLASSES  # lista ordenada de 8 clases

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def predict(self, image: Union[str, "Image.Image"], k: int = 3) -> dict:
        """Clasifica un landmark y devuelve top-k predicciones.

        Args:
            image: ruta al archivo de imagen (str/Path) o PIL.Image ya abierta.
            k:     cuántas predicciones devolver en top_k (default 3).

        Returns:
            {
                "landmark_id": str,              # clase con mayor probabilidad
                "confidence":  float,            # probabilidad del top-1 (0-1)
                "top_k":       [(id, prob), ...]  # k entradas ordenadas desc
            }
        """
        tensor = self._preprocess(image)           # (1, 3, 224, 224)
        probs  = self._run_inference(tensor)        # (NUM_CLASSES,) en CPU

        k = min(k, len(self._classes))             # k no puede superar nº de clases
        top_probs, top_indices = torch.topk(probs, k)

        top_k = [
            (self._classes[idx.item()], round(prob.item(), 4))
            for idx, prob in zip(top_indices, top_probs)
        ]

        return {
            "landmark_id": top_k[0][0],
            "confidence":  top_k[0][1],
            "top_k":       top_k,
        }

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _preprocess(self, image: Union[str, "Image.Image"]) -> torch.Tensor:
        """Convierte str o PIL.Image a tensor (1, 3, 224, 224) normalizado."""
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        # Forzar RGB: maneja RGBA (imágenes con transparencia) y L (escala de grises).
        image = image.convert("RGB")

        tensor = _EVAL_TRANSFORM(image)          # (3, 224, 224)
        return tensor.unsqueeze(0).to(self._device)  # (1, 3, 224, 224)

    def _run_inference(self, tensor: torch.Tensor) -> torch.Tensor:
        """Corre el forward pass y devuelve probabilidades (softmax) en CPU."""
        with torch.no_grad():
            logits = self._model(tensor)         # (1, NUM_CLASSES)
        probs = F.softmax(logits, dim=1)         # (1, NUM_CLASSES)
        return probs.squeeze(0).cpu()            # (NUM_CLASSES,)
