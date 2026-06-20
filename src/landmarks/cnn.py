"""cnn.py — TuristCNN: CNN desde cero para clasificar 8 landmarks.

Alejandro (Fase 3): este es tu archivo principal para B1.
Diseño y justificaciones en docs/ARQUITECTURA_CNN.md.

Tarea: completá count_parameters y export_torchscript si los necesitás,
y documentá tus decisiones de arquitectura en
docs/decisiones/fase3_decisiones_alejandro.md.
"""

import torch
import torch.nn as nn

from src.config import NUM_CLASSES, DROPOUT


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

    Decisiones documentadas en: docs/decisiones/fase3_decisiones_alejandro.md
    Diseño en papel:             docs/ARQUITECTURA_CNN.md
    """

    def __init__(
        self,
        num_blocks: int = 4,
        num_classes: int = NUM_CLASSES,
        dropout: float = DROPOUT
    ):
        super().__init__()

        if num_blocks not in [2, 3, 4]:
            raise ValueError("num_blocks debe ser 2, 3 o 4")

        self.num_blocks = num_blocks

        filters = [32, 64, 128, 256][:num_blocks]

        layers = []
        in_ch = 3

        for out_ch in filters:
            layers.append(_conv_block(in_ch, out_ch))
            in_ch = out_ch

        self.features = nn.Sequential(*layers)

        self.pool = nn.AdaptiveAvgPool2d(1)

        fc_hidden = filters[-1] // 2

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(filters[-1], fc_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout * 0.6),
            nn.Linear(fc_hidden, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.pool(x)
        return self.classifier(x)


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
    for n in [2, 3, 4]:
        model = TuristCNN(num_blocks=n)
        out = model(torch.randn(2, 3, 224, 224))
        p = count_parameters(model)
        print(f"num_blocks={n}  out:{tuple(out.shape)}  params:{p['total']:,}")