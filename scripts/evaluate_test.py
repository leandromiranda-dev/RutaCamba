"""evaluate_test.py — Evaluación final en TEST de todos los modelos + tabla comparativa.

Modelos evaluados:
    models/cnn_scratch.pt        ← B1 (TuristCNN, desde cero)
    models/transfer_learning.pt  ← B2 (ResNet18 Transfer Learning)
    models/se_cnn_scratch.pt     ← B3 (TuristSECNN, SE-attention)
    models/resnet_lite_scratch.pt← BA (TuristResNet, bloques residuales)

Calcula para cada modelo: accuracy, precision/recall/F1 (macro), reporte por
clase y matriz de confusión (PNG en docs/eval/). Al final imprime la tabla
comparativa y la guarda en docs/eval/metrics.json.

Uso (con el venv y .env cargado):
    python scripts/evaluate_test.py
"""
import json
import os
import sys

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Permite ejecutar el script directo (python scripts/evaluate_test.py) además de
# como módulo: agrega el root del repo al path para poder importar `src`.
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import LANDMARK_CLASSES  # noqa: E402
from src.data.dataloaders import get_dataloaders  # noqa: E402

# Consola de Windows: forzar UTF-8 para los prints con acentos/flechas.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

MODELS = {
    "B1 (CNN scratch)": "models/cnn_scratch.pt",
    "B2 (ResNet TL)":   "models/transfer_learning.pt",
    "B3 (SE-CNN)":      "models/se_cnn_scratch.pt",
    "BA (ResNet-lite)": "models/resnet_lite_scratch.pt",
}
# Runs de WandB de cada modelo, para sacar el tiempo de entrenamiento (_runtime).
WANDB_RUNS = {
    "B1 (CNN scratch)": "g3630v5v",
    "B2 (ResNet TL)":   "enedjxj9",
    "B3 (SE-CNN)":      "wbay2jxu",
    "BA (ResNet-lite)": "3i5ickz4",
}
OUT_DIR = "docs/eval"


def _slug(name: str) -> str:
    if "B1" in name:
        return "b1"
    if "B2" in name:
        return "b2"
    if "B3" in name:
        return "b3"
    return "ba"


def evaluate(model_path: str, test_loader, device):
    """Corre el modelo sobre todo el test set. Devuelve (y_true, y_pred, params, MB)."""
    model = torch.jit.load(model_path, map_location=device)
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            logits = model(images.to(device))
            y_pred.extend(logits.argmax(1).cpu().tolist())
            y_true.extend(labels.tolist())
    n_params = sum(p.numel() for p in model.parameters())
    size_mb = os.path.getsize(model_path) / 1e6
    return np.array(y_true), np.array(y_pred), n_params, size_mb


def fetch_train_times() -> dict:
    """Tiempo de entrenamiento (seg) de cada run desde WandB. {} si no hay red/creds."""
    try:
        import wandb
        api = wandb.Api()
        entity, project = os.getenv("WANDB_ENTITY"), os.getenv("WANDB_PROJECT")
        times = {}
        for name, run_id in WANDB_RUNS.items():
            if not run_id:
                continue
            run = api.run(f"{entity}/{project}/{run_id}")
            times[name] = run.summary.get("_runtime")
        return times
    except Exception as e:  # noqa: BLE001
        print(f"[aviso] No se pudo obtener tiempo de entrenamiento de WandB: {e}")
        return {}


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}")

    *_, test_loader, _ = get_dataloaders(batch_size=32)
    train_times = fetch_train_times()

    results = {}
    for name, path in MODELS.items():
        if not os.path.exists(path):
            print(f"[skip] {name}: no existe {path}")
            continue

        y_true, y_pred, n_params, size_mb = evaluate(path, test_loader, device)
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
        f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

        results[name] = {
            "test_accuracy": round(float(acc), 4),
            "precision_macro": round(float(prec), 4),
            "recall_macro": round(float(rec), 4),
            "f1_macro": round(float(f1), 4),
            "params": int(n_params),
            "size_mb": round(size_mb, 2),
            "train_seconds": train_times.get(name),
        }

        print(f"\n===== {name} =====")
        print(f"Test accuracy: {acc:.4f} | precision(macro): {prec:.4f} | "
              f"recall(macro): {rec:.4f} | f1(macro): {f1:.4f}")
        print(classification_report(y_true, y_pred, target_names=LANDMARK_CLASSES,
                                    zero_division=0))

        cm = confusion_matrix(y_true, y_pred, labels=list(range(len(LANDMARK_CLASSES))))
        disp = ConfusionMatrixDisplay(cm, display_labels=LANDMARK_CLASSES)
        fig, ax = plt.subplots(figsize=(8, 7))
        disp.plot(ax=ax, xticks_rotation=45, cmap="Blues", colorbar=False)
        ax.set_title(f"Matriz de confusión — {name} (test)")
        plt.tight_layout()
        cm_path = f"{OUT_DIR}/confusion_{_slug(name)}.png"
        fig.savefig(cm_path, dpi=120)
        plt.close(fig)
        print(f"Matriz de confusión → {cm_path}")

    # ── Tabla comparativa ─────────────────────────────────────────────────────
    print("\n\n===== TABLA COMPARATIVA (TEST) =====")
    header = f"{'Modelo':<20}{'Test Acc':>10}{'Prec':>8}{'Recall':>8}{'F1':>8}{'Params':>13}{'MB':>8}{'Train(s)':>10}"
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        t = r["train_seconds"]
        t_str = f"{t:.0f}" if isinstance(t, (int, float)) else "—"
        print(f"{name:<20}{r['test_accuracy']:>9.2%}{r['precision_macro']:>8.2%}"
              f"{r['recall_macro']:>8.2%}{r['f1_macro']:>8.2%}{r['params']:>13,}"
              f"{r['size_mb']:>8.1f}{t_str:>10}")

    with open(f"{OUT_DIR}/metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nMétricas guardadas en {OUT_DIR}/metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
