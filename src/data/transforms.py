"""transforms.py — Transformaciones de imagen para train y eval.

Implementado según docs/decisiones/fase1_decisiones_diego.md (Decisión 002 y 005):
- Train: Resize(256) -> RandomCrop(224) -> HFlip(0.5) -> Rotation(±10°) ->
  ColorJitter(0.2) — augmentation moderado, no agresivo, para no deformar la
  geometría de los monumentos.
- Eval (val/test): Resize(256) -> CenterCrop(224), sin augmentation.
"""
from torchvision import transforms

from src.config import CROP, IMAGENET_MEAN, IMAGENET_STD, RESIZE

_NORMALIZE = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)


def get_train_transforms() -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(RESIZE),
        transforms.RandomCrop(CROP),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        _NORMALIZE,
    ])


def get_eval_transforms() -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(RESIZE),
        transforms.CenterCrop(CROP),
        transforms.ToTensor(),
        _NORMALIZE,
    ])
