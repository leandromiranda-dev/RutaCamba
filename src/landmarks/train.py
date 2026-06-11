"""train.py — Loop de entrenamiento para CNN y Transfer Learning.

Alejandro (Fase 3): este es tu archivo de entrenamiento.
Adaptado de la versión original para importar desde los módulos correctos
de la nueva estructura de carpetas.

Uso:
    python -m src.landmarks.train --model cnn --epochs 30
    python -m src.landmarks.train --model transfer --epochs 15
    python -m src.landmarks.train --model cnn --epochs 2 --limit-batches 5   # smoke test

Loggea por época: train/val loss y accuracy, lr. Guarda el mejor checkpoint
(menor val loss) en models/ y lo sube a WandB como artifact.

Decisiones a documentar en: docs/decisiones/fase3_decisiones_alejandro.md
"""

import argparse
from pathlib import Path

import torch
import torch.nn as nn

from src.landmarks.cnn import TuristCNN, count_parameters
from src.landmarks.transfer import build_transfer_model
from src.config import (
    BATCH_SIZE, LR, WEIGHT_DECAY, DROPOUT, MIN_EPOCHS, MODELS_DIR,
    WANDB_PROJECT,
)

# WandB: Nicole (Fase 5) implementa estas funciones.
# Mientras no estén listas, el try/except evita que el training se rompa.
try:
    from src.tracking.wandb_utils import init_run, log_epoch, log_model_artifact
    _WANDB_READY = True
except (ImportError, NotImplementedError):
    _WANDB_READY = False

MODELS_PATH = Path(MODELS_DIR)


def get_dataloaders(batch_size: int):
    """Usa src.data si Diego ya lo implementó; si no, cae a ImageFolder en data/."""
    try:
        from src.data import get_dataloaders as _real
        return _real(batch_size=batch_size)
    except (ImportError, NotImplementedError):
        from torchvision import datasets, transforms
        from torch.utils.data import DataLoader
        from src.config import RESIZE, CROP, IMAGENET_MEAN, IMAGENET_STD

        norm = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
        train_tf = transforms.Compose([
            transforms.Resize(RESIZE),
            transforms.CenterCrop(CROP),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(0.2, 0.2, 0.2),
            transforms.ToTensor(),
            norm,
        ])
        eval_tf = transforms.Compose([
            transforms.Resize(RESIZE), transforms.CenterCrop(CROP),
            transforms.ToTensor(), norm,
        ])
        loaders = {}
        for split in ("train", "val", "test"):
            ds = datasets.ImageFolder(f"data/{split}", train_tf if split == "train" else eval_tf)
            loaders[split] = DataLoader(ds, batch_size=batch_size,
                                        shuffle=(split == "train"), num_workers=2)
        return loaders["train"], loaders["val"], loaders["test"]


def run_epoch(model, loader, criterion, device, optimizer=None, limit_batches=0):
    """Una época. Si optimizer es None → evaluación. Devuelve (loss, accuracy)."""
    training = optimizer is not None
    model.train(training)
    total_loss, correct, seen = 0.0, 0, 0
    with torch.set_grad_enabled(training):
        for i, (images, labels) in enumerate(loader):
            if limit_batches and i >= limit_batches:
                break
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * labels.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            seen += labels.size(0)
    return total_loss / max(seen, 1), correct / max(seen, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["cnn", "transfer"], default="cnn")
    parser.add_argument("--epochs", type=int, default=MIN_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    parser.add_argument("--dropout", type=float, default=DROPOUT)
    parser.add_argument("--limit-batches", type=int, default=0, help="solo smoke test")
    parser.add_argument("--wandb-project", default=WANDB_PROJECT)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = (TuristCNN(dropout=args.dropout) if args.model == "cnn"
             else build_transfer_model()).to(device)
    params = count_parameters(model)

    # WandB logging (Nicole — Fase 5)
    if _WANDB_READY:
        init_run(
            name=f"{args.model}-e{args.epochs}-lr{args.lr}-bs{args.batch_size}",
            config={**vars(args), **params},
        )

    train_loader, val_loader, _ = get_dataloaders(args.batch_size)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr, weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=3)

    MODELS_PATH.mkdir(exist_ok=True)
    best_path = MODELS_PATH / f"best_{args.model}.pth"
    best_val_loss = float("inf")

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, device,
                                          optimizer, args.limit_batches)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, device,
                                      limit_batches=args.limit_batches)
        scheduler.step(val_loss)

        metrics = {
            "epoch": epoch,
            "train/loss": train_loss, "train/acc": train_acc,
            "val/loss": val_loss, "val/acc": val_acc,
            "lr": optimizer.param_groups[0]["lr"],
        }
        if _WANDB_READY:
            log_epoch(metrics, step=epoch)

        print(f"[{epoch:02d}/{args.epochs}] train {train_loss:.4f}/{train_acc:.2%}"
              f"  val {val_loss:.4f}/{val_acc:.2%}")

        if val_loss < best_val_loss:  # mejor checkpoint = menor val loss (requisito)
            best_val_loss = val_loss
            torch.save({"epoch": epoch, "model_state": model.state_dict(),
                        "val_loss": val_loss, "val_acc": val_acc,
                        "config": vars(args)}, best_path)

    # Mejor checkpoint como artifact en WandB (requisito Fase 5).
    if _WANDB_READY:
        log_model_artifact(str(best_path), f"best-{args.model}")

    print(f"Mejor val loss: {best_val_loss:.4f} → {best_path}")


if __name__ == "__main__":
    main()
