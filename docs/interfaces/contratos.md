# contratos.md — Interfaces entre fases (el pegamento del proyecto)

> **Por qué existe este archivo:** para que cada quien programe su fase de forma
> aislada y, al final, la Fase 6 (API) conecte todo "enchufando" módulos sin tener
> que entrar a modificar el código de nadie. Cada fase **expone** funciones/clases
> con la firma exacta que está acá. Mientras respetes tu firma, el resto del equipo
> puede construir contra vos aunque tu implementación interna aún no esté lista.

**Regla:** si necesitás cambiar una firma de este documento, avisá en el grupo y
que se actualice acá ANTES de programar. Nadie cambia un contrato por su cuenta.

Todos los formatos de imagen de entrada son **rutas de archivo (`str`) o `PIL.Image`**.
Todos los `landmark_id` y nombres de clase salen de `src/config.LANDMARK_CLASSES`.

---

## Fase 1 — Datos (Diego) expone

```python
# src/data/dataloaders.py
def get_dataloaders(batch_size: int = 32) -> tuple:
    """
    Devuelve (train_loader, val_loader, test_loader, class_names).
    class_names == src.config.LANDMARK_CLASSES (mismo orden).
    Cada loader entrega (imagen_tensor[B,3,224,224], label[B]).
    """

# src/data/transforms.py
def get_train_transforms(): ...   # incluye augmentation
def get_eval_transforms():  ...   # solo resize/crop/normalize (val y test)
```

Consumido por: **Fase 3** (entrena con estos loaders).

---

## Fase 2 — Re-ID (Jose + Leandro) expone

```python
# src/reid/embeddings.py   (Leandro)
def get_embedding(image) -> "np.ndarray":
    """Vector de embedding del rostro de una imagen (DeepFace/ArcFace).
    Devuelve None si no se detecta ningún rostro."""

def build_gallery(gallery_dir: str) -> dict:
    """{identidad: [embedding, embedding, ...]} a partir de carpetas por persona."""

# src/reid/metrics.py      (Leandro)
def evaluate_reid(query_set, gallery) -> dict:
    """Devuelve {'top1': float, 'top5': float, 'map': float}. mAP variante re-ID."""

# src/reid/access.py       (Jose)   ← ESTA es la que usa la API
def verify_identity(declared_id: str, probe_image) -> dict:
    """
    Punto de entrada del Módulo A. Devuelve:
    {
      "access": bool,            # True solo si top-1 == declared_id y dist < umbral
      "distance": float,
      "top1_identity": str,
      "topk": [(identidad, distancia), ...]
    }
    """
```

Consumido por: **Fase 6** (endpoint `/verify` llama a `verify_identity`).

---

## Fase 3 — Landmarks (Alejandro) expone

```python
# src/landmarks/predictor.py
class LandmarkPredictor:
    def __init__(self, model_path: str = "models/transfer_learning.pt"):
        """Carga un modelo TorchScript con torch.jit.load()."""

    def predict(self, image, k: int = 3) -> dict:
        """
        Devuelve:
        {
          "landmark_id": str,            # top-1, uno de LANDMARK_CLASSES
          "confidence": float,           # prob del top-1
          "top_k": [(landmark_id, prob), ...]   # k elementos ordenados
        }
        """
```

Artefactos que deja en `models/`: `cnn_scratch.pt` y `transfer_learning.pt`
(TorchScript). Consumido por: **Fase 6** (endpoint `/predict`).

---

## Fase 4 — Traducción (Jose) expone

```python
# src/translation/translate.py
class TranslationService:
    def __init__(self, translations_path: str = "data/translations.json"): ...

    def get_landmark_translations(self, landmark_id: str) -> dict:
        """Devuelve {'es':..., 'en':..., 'fr':..., 'it':...} (lookup O(1), sin red)."""

    def normalize_input(self, query: str) -> dict:
        """
        Normaliza una consulta en idioma inesperado al español.
        {'original':..., 'detected_lang':..., 'normalized':..., 'method': 'llm'|'nllb'|'passthrough'}
        """
```

Artefacto que deja en `data/`: `translations.json`. Consumido por: **Fase 6**
(endpoints `/predict` para traducir la salida y `/normalize`).

---

## Fase 5 — WandB (Nicole) expone

```python
# src/tracking/wandb_utils.py
def init_run(name: str, config: dict): ...        # wandb.init estándar del equipo
def log_epoch(metrics: dict, step: int): ...       # {'train/loss':.., 'val/acc':..}
def log_model_artifact(path: str, name: str): ...  # sube el .pt como artifact
```

Consumido por: **Fase 2 y Fase 3** dentro de sus loops de entrenamiento.
> Nota: las llamadas a estas funciones viven DENTRO del código de quien entrena
> (Alejandro / Leandro). Nicole define la convención y produce la comparación de
> runs, el sweep y el Report. Ver su `.md`.

---

## Fase 6 — API (Nicole) consume todo lo anterior

```
POST /verify     → reid.access.verify_identity(...)         → token de sesión
POST /predict    → exige token → landmarks.predictor.predict(...)
                               → translation.get_landmark_translations(...)
POST /normalize  → translation.normalize_input(...)
```

La API **carga modelos TorchScript con `torch.jit.load()` y NUNCA re-entrena.**

---

## Resumen visual de dependencias

```
Fase 1 (datos) ──▶ Fase 3 (landmarks) ──┐
Fase 2 (re-id) ─────────────────────────┤
Fase 4 (traducción) ────────────────────┼──▶ Fase 6 (API + UI) ──▶ flujo end-to-end
Fase 5 (wandb) ──▶ usado por Fase 2 y 3  ┘
Fase 7 (informe) ──▶ junta todo lo de todos
```
