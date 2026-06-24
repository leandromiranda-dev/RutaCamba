"""cnn.py — Arquitecturas CNN desde cero para clasificar 8 landmarks.

Modelos disponibles:
  B1 — TuristCNN      : 4 conv blocks (32→64→128→256) + AdaptiveAvgPool + FC. ~430K params.
  B3 — TuristSECNN    : igual a B1 pero con Squeeze-and-Excitation por bloque. ~500K params.
  BA — TuristResNet   : stem 7×7 + 3 bloques residuales (64→128→256) + FC. ~830K params.

Alejandro (Fase 3): este es tu archivo principal para B1.
Diseño y justificaciones en docs/ARQUITECTURA_CNN.md.
"""

import torch
import torch.nn as nn

from src.config import NUM_CLASSES, DROPOUT


# ── B1: TuristCNN (CNN base desde cero) ────────────────────────────────────

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
    """Exporta el modelo con TorchScript (requisito del enunciado) y prueba la carga.

    Se exporta desde una copia en CPU para que el .pt sea portable (la API puede
    correr en una máquina sin GPU). La prueba de carga se hace sobre el mismo
    device del modelo recargado: así, al entrenar en GPU, el tensor de prueba no
    queda en CPU contra pesos en CUDA (lo que causaba un RuntimeError de device).
    """
    model.eval()
    scripted = torch.jit.script(model.cpu())
    scripted.save(path)
    # Prueba de carga inmediata: si falla, mejor enterarse ahora y no en la API.
    reloaded = torch.jit.load(path)
    device = next(reloaded.parameters()).device
    with torch.no_grad():
        reloaded(torch.randn(1, 3, 224, 224, device=device))


# ── B3: TuristSECNN (Squeeze-and-Excitation CNN) ───────────────────────────

class SEBlock(nn.Module):
    """Recalibra los mapas de características por canal (Squeeze-and-Excitation).

    Squeeze: promedia espacialmente cada canal a un escalar (Global AvgPool).
    Excitation: dos FC aprenden qué canales importan → salida sigmoid ∈ (0,1).
    Cada canal del feature map se multiplica por su peso aprendido.
    """

    def __init__(self, channels: int, reduction: int = 8):
        super().__init__()
        hidden = max(1, channels // reduction)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, hidden, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.size(0)
        c = x.size(1)
        w = self.pool(x).view(b, c)
        w = self.fc(w).view(b, c, 1, 1)
        return x * w


def _se_conv_block(in_ch: int, out_ch: int, reduction: int = 8) -> nn.Sequential:
    """Conv 3x3 + BN + ReLU + MaxPool + SE (atención de canal)."""
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
        SEBlock(out_ch, reduction=reduction),
    )


class TuristSECNN(nn.Module):
    """TuristCNN + Squeeze-and-Excitation por bloque (B3).

    Mismo esquema 32→64→128→256 que B1, pero cada bloque reescala sus canales
    por importancia aprendida. El costo adicional en parámetros es mínimo (~5%)
    pero la red puede enfocarse en los canales más discriminativos por clase.
    ~500K parámetros.
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        dropout: float = DROPOUT,
        reduction: int = 8,
    ):
        super().__init__()
        filters = [32, 64, 128, 256]
        layers = []
        in_ch = 3
        for out_ch in filters:
            layers.append(_se_conv_block(in_ch, out_ch, reduction=reduction))
            in_ch = out_ch
        self.features = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool2d(1)
        fc_hidden = filters[-1] // 2  # 128
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


# ── BA: TuristResNet (bloques residuales desde cero) ───────────────────────

class ResidualBlock(nn.Module):
    """Bloque residual básico: 2×Conv3×3 + BN, con shortcut 1×1 si cambia la dim."""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
        )
        # nn.Sequential() vacío actúa como identidad — mantiene el tipo uniforme
        # para TorchScript (sin condicional de tipo en forward).
        if in_ch != out_ch or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch),
            )
        else:
            self.shortcut = nn.Sequential()
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.conv(x) + self.shortcut(x))


class TuristResNet(nn.Module):
    """ResNet-lite desde cero para 8 landmarks (entrada 3×224×224) — BA.

    Stem 7×7 (stride=2) + MaxPool → 3 bloques residuales (64→128→256) +
    GlobalAvgPool + cabeza FC con dropout. ~830K parámetros.
    Las skip connections permiten profundidad sin degradación del gradiente.
    """

    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = DROPOUT):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(3, stride=2, padding=1),
        )
        self.layer1 = ResidualBlock(64, 64)
        self.layer2 = ResidualBlock(64, 128, stride=2)
        self.layer3 = ResidualBlock(128, 256, stride=2)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout * 0.6),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.pool(x)
        return self.classifier(x)


if __name__ == "__main__":
    # Smoke test sin datos: forward con un batch aleatorio.
    for n in [2, 3, 4]:
        model = TuristCNN(num_blocks=n)
        out = model(torch.randn(2, 3, 224, 224))
        p = count_parameters(model)
        print(f"num_blocks={n}  out:{tuple(out.shape)}  params:{p['total']:,}")

    for name, m in [("SE-CNN", TuristSECNN()), ("ResNet-lite", TuristResNet())]:
        out = m(torch.randn(2, 3, 224, 224))
        p = count_parameters(m)
        print(f"{name}  out:{tuple(out.shape)}  params:{p['total']:,}")