"""dataloaders.py — DataLoaders de PyTorch para train/val/test.

Diego (Fase 1): implementá get_dataloaders().
CONTRATO (no cambiar la firma):
    def get_dataloaders(batch_size: int = 32) -> tuple:
        # devuelve (train_loader, val_loader, test_loader, class_names)
"""
from src.config import LANDMARK_CLASSES

# TODO (Diego): implementar get_dataloaders


def get_dataloaders(batch_size: int = 32):
    raise NotImplementedError(
        "Diego (Fase 1): implementá get_dataloaders() en src/data/dataloaders.py"
    )
