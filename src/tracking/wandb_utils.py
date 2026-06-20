"""wandb_utils.py — Wrappers de WandB para el equipo (Nicole, Fase 5).

Alejandro y Leandro llaman a estas funciones en sus loops de entrenamiento.

CONTRATO (no cambiar las firmas):
    def init_run(name: str, config: dict): ...
    def log_epoch(metrics: dict, step: int): ...
    def log_model_artifact(path: str, name: str): ...

Uso típico:
    run = init_run("transfer_learning_b2", {"lr": 1e-3, "batch_size": 32})
    for epoch in range(epochs):
        ...
        log_epoch({"train/loss": tl, "val/loss": vl, "val/acc": va}, step=epoch)
    log_model_artifact("models/transfer_learning.pt", "transfer_learning")
    run.finish()
"""
import os

import wandb

from src.config import WANDB_PROJECT, WANDB_ENTITY


def init_run(name: str, config: dict):
    """Inicia un run de WandB con la convención del equipo.

    - `name`: nombre descriptivo del run (ej: "cnn_scratch_b1", "reid_eval").
    - `config`: hiperparámetros del experimento. Van en `wandb.config` para que
      aparezcan en las tablas de comparación y parallel coordinates.

    Devuelve el objeto `run` (acordate de `run.finish()` al terminar).
    """
    return wandb.init(
        project=WANDB_PROJECT,
        entity=WANDB_ENTITY or None,  # None → usa la entity por defecto del login
        name=name,
        config=config,
        reinit="finish_previous",  # permite varios runs en un mismo proceso/notebook
    )


def log_epoch(metrics: dict, step: int):
    """Loguea las métricas de una época.

    - `metrics`: dict con claves con prefijo, ej:
      {"train/loss": 0.41, "val/loss": 0.52, "val/acc": 0.87}
    - `step`: número de época (eje x compartido entre runs).
    """
    wandb.log(metrics, step=step)


def log_model_artifact(path: str, name: str):
    """Sube un checkpoint .pt como artifact de tipo "model".

    - `path`: ruta al .pt (ej: "models/transfer_learning.pt").
    - `name`: nombre del artifact (ej: "transfer_learning").

    Llamala UNA vez por entrenamiento, con el mejor checkpoint (menor val loss).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe el checkpoint: {path}")
    artifact = wandb.Artifact(name=name, type="model")
    artifact.add_file(path)
    wandb.log_artifact(artifact)
    return artifact
