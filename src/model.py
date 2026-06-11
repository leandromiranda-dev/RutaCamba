"""Modelos del proyecto RutaCamba.

- TuristCNN: CNN desde cero (B1). Diseño y justificación en docs/ARQUITECTURA_CNN.md.
- build_transfer_model: backbone preentrenado para Transfer Learning (B2).
"""

import torch
import torch.nn as nn

NUM_CLASSES = 8


def _conv_block(in_ch: int, out_ch: int) -> nn.Sequential:
    """Conv 3x3 + BatchNorm + ReLU + MaxPool 2x2 (reduce la resolución a la mitad)."""
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


class TuristCNN(nn.Module):
    """CNN desde cero para clasificar 8 landmarks (entrada 3x224x224).

    4 bloques conv (32→64→128→256) + AdaptiveAvgPool + cabeza FC con dropout.
    ~430K parámetros.
    """

    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = 0.5):
        super().__init__()
        self.features = nn.Sequential(
            _conv_block(3, 32),    # → 32 x 112 x 112
            _conv_block(32, 64),   # → 64 x 56 x 56
            _conv_block(64, 128),  # → 128 x 28 x 28
            _conv_block(128, 256), # → 256 x 14 x 14
        )
        self.pool = nn.AdaptiveAvgPool2d(1)  # → 256 x 1 x 1
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout * 0.6),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)


def build_transfer_model(num_classes: int = NUM_CLASSES, freeze_backbone: bool = True) -> nn.Module:
    """ResNet18 preentrenado en ImageNet con nueva FC (B2).

    Fase 1: backbone congelado, solo entrena la FC.
    Fase 2 (fine-tuning): descongelar últimas capas con model.layer4.requires_grad_(True).
    """
    from torchvision import models

    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)  # siempre entrenable
    return model


def count_parameters(model: nn.Module) -> dict:
    """Total y entrenables — para la tabla comparativa B1 vs B2 del informe."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable}


def export_torchscript(model: nn.Module, path: str) -> None:
    """Exporta el modelo con TorchScript (requisito del enunciado) y prueba la carga."""
    model.eval()
    scripted = torch.jit.script(model)
    scripted.save(path)
    # Prueba de carga inmediata: si falla, mejor enterarse ahora y no en la API.
    reloaded = torch.jit.load(path)
    with torch.no_grad():
        reloaded(torch.randn(1, 3, 224, 224))


if __name__ == "__main__":
    # Smoke test sin datos: forward con un batch aleatorio.
    model = TuristCNN()
    out = model(torch.randn(2, 3, 224, 224))
    print("TuristCNN  out:", tuple(out.shape), "params:", count_parameters(model))
