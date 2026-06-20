"""dataloaders.py — DataLoaders de PyTorch para train/val/test.

CONTRATO (no cambiar la firma):
    def get_dataloaders(batch_size: int = 32) -> tuple:
        # devuelve (train_loader, val_loader, test_loader, class_names)

Decisión 004 (docs/decisiones/fase1_decisiones_diego.md): el train_loader usa
WeightedRandomSampler con los pesos de data/class_weights.json para corregir
el desbalance de clases (ratio 2.82x) sin descartar ni duplicar imágenes.
"""
import json
import platform

from torch.utils.data import DataLoader, WeightedRandomSampler

from src.config import LANDMARK_CLASSES
from src.data.dataset import LandmarkDataset
from src.data.transforms import get_eval_transforms, get_train_transforms

CLASS_WEIGHTS_PATH = "data/class_weights.json"

# Igual que en src/landmarks/train.py: num_workers=0 en Windows evita
# conflictos conocidos de multiprocessing con algunas versiones de PyTorch.
_NUM_WORKERS = 0 if platform.system() == "Windows" else 2


def _build_train_sampler(dataset: LandmarkDataset) -> WeightedRandomSampler:
    with open(CLASS_WEIGHTS_PATH, encoding="utf-8") as f:
        weights_by_class = json.load(f)

    sample_weights = [
        weights_by_class[class_name] for _, class_name in dataset.samples
    ]
    return WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)


def get_dataloaders(batch_size: int = 32):
    train_ds = LandmarkDataset(split="train", transform=get_train_transforms())
    val_ds = LandmarkDataset(split="val", transform=get_eval_transforms())
    test_ds = LandmarkDataset(split="test", transform=get_eval_transforms())

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        sampler=_build_train_sampler(train_ds),
        num_workers=_NUM_WORKERS,
    )
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=_NUM_WORKERS)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=_NUM_WORKERS)

    return train_loader, val_loader, test_loader, LANDMARK_CLASSES
