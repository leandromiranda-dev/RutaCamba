"""download_model_wandb.py — Descarga el modelo desde WandB artifacts.

Uso:
    wandb login          (solo la primera vez)
    python scripts/download_model_wandb.py
"""
import os
import sys

WANDB_ENTITY  = "lozadaleonn-ciencialink"
WANDB_PROJECT = "rutacamba"
ARTIFACT_NAME = "best-transfer:latest"
OUTPUT_PATH   = "models/transfer_learning.pt"


def main():
    try:
        import wandb
    except ImportError:
        print("Instala wandb: pip install wandb")
        sys.exit(1)

    if os.path.exists(OUTPUT_PATH):
        print(f"[skip] {OUTPUT_PATH} ya existe.")
        return

    os.makedirs("models", exist_ok=True)
    print(f"Descargando {WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME} ...")

    api = wandb.Api()
    artifact = api.artifact(f"{WANDB_ENTITY}/{WANDB_PROJECT}/{ARTIFACT_NAME}")
    artifact.download(root="models/")

    # Renombrar si el artifact trae otro nombre
    import glob
    pts = glob.glob("models/*.pt") + glob.glob("models/*.pth")
    if pts and not os.path.exists(OUTPUT_PATH):
        os.rename(pts[0], OUTPUT_PATH)
        print(f"  -> renombrado a {OUTPUT_PATH}")

    print(f"Modelo descargado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
