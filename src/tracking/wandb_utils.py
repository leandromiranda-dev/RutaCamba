"""wandb_utils.py — Wrappers de WandB para el equipo.

Nicole (Fase 5): implementá init_run, log_epoch y log_model_artifact.
Alejandro y Leandro llamarán a estas funciones en sus loops de entrenamiento.

CONTRATO (no cambiar las firmas):
    def init_run(name: str, config: dict): ...
    def log_epoch(metrics: dict, step: int): ...
    def log_model_artifact(path: str, name: str): ...
"""
from src.config import WANDB_PROJECT, WANDB_ENTITY  # noqa: F401

# TODO (Nicole): implementar init_run, log_epoch, log_model_artifact


def init_run(name: str, config: dict):
    raise NotImplementedError("Nicole (Fase 5): implementá init_run()")


def log_epoch(metrics: dict, step: int):
    raise NotImplementedError("Nicole (Fase 5): implementá log_epoch()")


def log_model_artifact(path: str, name: str):
    raise NotImplementedError("Nicole (Fase 5): implementá log_model_artifact()")
