"""transfer.py — ResNet18 con Transfer Learning para clasificar 8 landmarks.

Alejandro (Fase 3): archivo para B2.

Dos fases de entrenamiento:
  a) Backbone congelado → solo entrena la FC nueva (lr=1e-3)
  b) Se descongela layer4 → fine-tuning con lr=1e-4

Decisiones documentadas en: docs/decisiones/fase3_decisiones_alejandro.md
"""

import torch
import torch.nn as nn
from torchvision import models

from src.config import NUM_CLASSES


def build_transfer_model(
    num_classes: int = NUM_CLASSES,
    freeze_backbone: bool = True,
) -> nn.Module:
    """ResNet18 preentrenado en ImageNet con nueva FC para B2.

    freeze_backbone=True  → congela TODO el backbone, solo entrena la FC (fase a).
    freeze_backbone=False → deja todo entrenable (no usar directamente — ver unfreeze_layer4).

    Decisión — por qué ResNet18 y no VGG16 o EfficientNet:
        - VGG16 tiene 138M parámetros (102M solo en FC). Excesivo para 8 clases
          y ~560 imágenes de entrenamiento. El fine-tuning sería muy lento y
          propenso a overfitting.
        - EfficientNet-B0 tiene 5.3M parámetros y es más eficiente, pero su
          arquitectura con depthwise separable convolutions es más compleja de
          explicar y justificar en la defensa.
        - ResNet18 tiene 11.7M parámetros, residual connections que resuelven
          el problema del gradiente que desaparece, y converge rápido. Es el
          balance correcto entre capacidad y simplicidad para este dataset.
    """
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    # Reemplazar FC: in_features=512 en ResNet18, out=num_classes=8.
    # La FC nueva siempre es entrenable, independientemente del freeze.
    # Decisión: una sola capa Linear (512→8) en lugar de una cabeza más
    # compleja porque el backbone ya extrae features ricas. Agregar capas
    # ocultas encima con tan pocas imágenes solo aumenta el riesgo de overfitting.
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    return model


def unfreeze_layer4(model: nn.Module, lr: float = 1e-4) -> torch.optim.Optimizer:
    """Descongela layer4 del backbone para fine-tuning (fase b).

    Decisión — por qué solo layer4 y no todo el backbone:
        - layer1 y layer2 aprenden features genéricas (bordes, texturas, colores)
          que son útiles para cualquier imagen y no necesitan ajustarse.
        - layer3 aprende formas intermedias — podrían ajustarse, pero con solo
          ~560 imágenes el riesgo de destruir los pesos preentrenados supera
          el beneficio.
        - layer4 aprende features de alto nivel específicas de la tarea
          (patrones complejos, estructuras). Es la capa más cercana a la FC
          y la que más se beneficia del fine-tuning para landmarks de Santa Cruz.

    Decisión — por qué lr=1e-4 y no lr=1e-3:
        - En la fase (a) la FC se entrenó con lr=1e-3 sobre features congeladas.
        - Si ahora usás el mismo lr sobre layer4, los gradientes grandes van a
          distorsionar los pesos preentrenados que costaron días de entrenamiento
          en ImageNet.
        - lr=1e-4 (10x menor) ajusta suavemente sin destruir lo aprendido.

    Decisión — por qué congelar primero y luego descongelar (y no entrenar todo junto):
        - Al inicio, la FC nueva tiene pesos aleatorios → gradientes grandes.
        - Si el backbone está descongelado desde el principio, esos gradientes
          grandes se propagan hacia atrás y corrompen los pesos preentrenados
          antes de que la FC aprenda algo útil.
        - Congelando primero, la FC converge a pesos razonables. Recién ahí
          tiene sentido afinar layer4 con gradientes pequeños y estables.

    Args:
        model: modelo ya entrenado en fase (a) con backbone congelado.
        lr:    learning rate para el fine-tuning (default 1e-4).

    Returns:
        Nuevo optimizer que incluye layer4 + FC con lr=1e-4.
    """
    # Descongelar solo layer4.
    for param in model.layer4.parameters():
        param.requires_grad = True

    # Verificación: mostramos qué capas están activas para trazabilidad.
    trainable_layers = [
        name for name, param in model.named_parameters() if param.requires_grad
    ]
    print(f"  Capas entrenables tras unfreeze_layer4: {len(trainable_layers)} tensores")
    print(f"  Incluye: layer4 + fc")

    # Optimizer nuevo con lr reducido para no destruir los pesos de layer4.
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )
    return optimizer


def count_transfer_params(model: nn.Module) -> dict:
    """Parámetros totales vs entrenables — para la tabla comparativa B1 vs B2."""
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen    = total - trainable
    return {"total": total, "trainable": trainable, "frozen": frozen}


if __name__ == "__main__":
    import torch

    # Smoke test fase (a): backbone congelado, solo FC entrenable.
    model_a = build_transfer_model(freeze_backbone=True)
    params_a = count_transfer_params(model_a)
    print("-- Fase (a): backbone congelado --")
    print(f"  Total:      {params_a['total']:,}")
    print(f"  Entrenables:{params_a['trainable']:,}  (solo FC)")
    print(f"  Congelados: {params_a['frozen']:,}")

    out = model_a(torch.randn(2, 3, 224, 224))
    print(f"  Forward OK: {tuple(out.shape)}")

    # Smoke test fase (b): descongelar layer4.
    print("\n-- Fase (b): descongelar layer4 --")
    optimizer_b = unfreeze_layer4(model_a, lr=1e-4)
    params_b = count_transfer_params(model_a)
    print(f"  Total:      {params_b['total']:,}")
    print(f"  Entrenables:{params_b['trainable']:,}  (layer4 + FC)")
    print(f"  Congelados: {params_b['frozen']:,}")

    out = model_a(torch.randn(2, 3, 224, 224))
    print(f"  Forward OK: {tuple(out.shape)}")