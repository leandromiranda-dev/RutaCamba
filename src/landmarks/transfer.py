"""transfer.py — ResNet18 con Transfer Learning para clasificar 8 landmarks.

Alejandro (Fase 3): este es tu archivo para B2.

Dos fases de entrenamiento (documentá ambas en docs/decisiones/fase3_decisiones_alejandro.md):
  a) Congelá el backbone → entrenás solo la FC nueva (lr=1e-3)
  b) Descongelá layer4 → fine-tuning con lr=1e-4

Ver: docs/fases/fase3_landmarks_alejandro.md → sección B2
"""

import torch.nn as nn
from torchvision import models

from src.config import NUM_CLASSES


def build_transfer_model(num_classes: int = NUM_CLASSES, freeze_backbone: bool = True) -> nn.Module:
    """ResNet18 preentrenado en ImageNet con nueva FC (B2).

    freeze_backbone=True  → solo entrena la FC (fase a).
    freeze_backbone=False → fine-tuning completo (fase b: descongelar layer4 aparte).

    Decisiones documentadas en: docs/decisiones/fase3_decisiones_alejandro.md
    """
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False
    # La FC nueva siempre es entrenable, independientemente del freeze.
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model
