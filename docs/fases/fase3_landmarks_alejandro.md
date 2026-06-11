# Fase 3 — Clasificación de landmarks · Alejandro Ojeda

**Peso:** 20 pts (la fase de mayor peso técnico) · **Carpeta:** `src/landmarks/` +
`notebooks/03_cnn_scratch.ipynb` + `notebooks/04_transfer_learning.ipynb`

> Es el núcleo: dada una foto, decir qué lugar es. Tenés que hacer DOS modelos sobre
> el mismo dataset (CNN propia y Transfer Learning) y compararlos. Dependés de que
> Diego (Fase 1) tenga `get_dataloaders()` listo. Mientras tanto podés desarrollar
> contra un loader de prueba.

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `src/landmarks/__init__.py` | exporta `LandmarkPredictor` |
| `src/landmarks/cnn.py` | `TuristCNN` (≥3 conv, BatchNorm, dropout, FC) |
| `src/landmarks/transfer.py` | ResNet18 con cabeza nueva |
| `src/landmarks/train.py` | loop de entrenamiento (loguea a WandB) |
| `src/landmarks/predictor.py` | `LandmarkPredictor.predict()` ← lo usa la API |
| `notebooks/03_cnn_scratch.ipynb` | entrenamiento + curvas B1 |
| `notebooks/04_transfer_learning.ipynb` | entrenamiento + curvas B2 + tabla comparativa |
| `requirements/fase3.txt` | torch, torchvision, wandb, scikit-learn, matplotlib |

> ⚠️ **MIGRACIÓN:** En la raíz de `src/` ya existen `model.py` y `train.py`
> con el diseño de `TuristCNN` y el loop de entrenamiento. **Migrá ese código a**
> `src/landmarks/cnn.py` y `src/landmarks/train.py`. Los originales quedan como
> referencia pero el código "vivo" va en tu carpeta.

Consumís de otras fases (no las edites): `src/data/dataloaders.get_dataloaders`,
`src/tracking/wandb_utils`.

---

## 2. Lo que tu código DEBE exponer (contrato)

```python
# src/landmarks/predictor.py
class LandmarkPredictor:
    def __init__(self, model_path="models/transfer_learning.pt"): ...
    def predict(self, image, k=3) -> dict:
        # {"landmark_id":..., "confidence":..., "top_k":[(id, prob), ...]}
```

Y dejás en `models/`: `cnn_scratch.pt` y `transfer_learning.pt` (TorchScript).

---

## 3. Paso a paso

### B1 — CNN desde cero

1. Migrá `TuristCNN` de `src/model.py` a **`src/landmarks/cnn.py`**. La arquitectura
   ya está diseñada y documentada en `docs/ARQUITECTURA_CNN.md` — leéla, es tuya.
   4 bloques `Conv→BatchNorm→ReLU→MaxPool`, luego `AdaptiveAvgPool → Flatten →
   Dropout → FC → FC(NUM_CLASSES)`. ✍️ Justificá el tamaño de cada capa.

2. Migrá el loop de entrenamiento de `src/train.py` a **`src/landmarks/train.py`**.
   Adaptalo para que importe desde `src/landmarks/cnn.py` y llame a
   `src/tracking/wandb_utils` (Nicole los define).

3. Entrená **≥ 30 épocas** con `CrossEntropyLoss` + `Adam`. Logueá por época
   `train/loss`, `val/loss`, `val/acc` a WandB. Guardá el checkpoint de **menor val
   loss** (no el último). ✍️ por qué menor val loss y no última época.

### B2 — Transfer Learning

4. Cargá **ResNet18** con pesos ImageNet en `src/landmarks/transfer.py`. ✍️ Justificá
   ResNet18 (11.7M params, residual connections, converge rápido) vs VGG16 (138M,
   FC de 102M, excesivo).

5. **Dos fases de entrenamiento:**
   - (a) Congelá el backbone (`requires_grad=False`), reemplazá la FC por una de
     `NUM_CLASSES` y entrená solo esa cabeza (lr=1e-3).
   - (b) Descongelá `layer4` y hacé fine-tuning con lr=1e-4.
   ✍️ por qué congelar primero (evitar destruir los pesos preentrenados con gradientes
   grandes en la FC nueva).

6. Registrá B1 y B2 como **runs separados** en WandB (avisá a Nicole para la
   comparación de runs / sweep).

### Evaluación y exportación

7. Evaluá ambos en el **test set** (que no tocaste): accuracy, precision, recall y
   **matriz de confusión por clase**. Identificá qué clases se confunden.

8. **Tabla comparativa B1 vs B2:** accuracy, nº de parámetros, tiempo de
   entrenamiento, tamaño del `.pt`. (Va en el informe.)

9. Exportá ambos con `torch.jit.script`/`torch.jit.trace`, recargá con
   `torch.jit.load()` y verificá que la inferencia da lo mismo que antes de exportar.

10. `LandmarkPredictor.predict()` carga el TorchScript y devuelve el dict del contrato.

---

## 4. Umbrales que TENÉS que pasar (valen 9 de los 20 pts)

| Modelo | Test Accuracy | Condición |
|--------|--------------|-----------|
| CNN desde cero (B1) | **≥ 45 %** | — |
| Transfer Learning (B2) | **≥ 75 %** | debe superar a B1 |

> Estos umbrales dependen del dataset de Diego. Si no llegás, primero revisá datos
> (volumen, limpieza, augmentation) antes que la arquitectura. Coordiná con Diego.

---

## 5. Checklist de rúbrica

- [ ] CNN propia justificada (≥3 conv, pooling, BN, dropout, FC) (3)
- [ ] Entrenamiento ≥30 épocas, curvas train/val, mejor modelo guardado (2)
- [ ] CNN Test Acc ≥45% (4)
- [ ] TL elegido y justificado; congelar + nueva FC; fine-tuning (4)
- [ ] TL Test Acc ≥75% y supera a CNN; comparación en tabla/gráfico (5)
- [ ] Ambos exportados con TorchScript y prueba de carga (2)

---

## 6. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase3_decisiones_alejandro.md` (copiá `docs/PLANTILLA_decisiones.md`).
Cada ✍️ es una entrada con "por qué esto y no lo otro".

Decisiones mínimas a registrar:
- Por qué 4 bloques conv (y no 3 o 5)
- Por qué AdaptiveAvgPool vs Flatten directo
- Por qué ResNet18 y no VGG16/EfficientNet
- Por qué congelar primero en Transfer Learning
- Por qué guardar checkpoint por menor val loss y no última época
- Cómo mitigaste el overfitting (augmentation, dropout, weight decay)

---

## 7. Cómo entregar

Rama `fase3-landmarks-alejandro` → PR a `develop`.
Avisá que `LandmarkPredictor` y los `.pt` ya cumplen el contrato para que Nicole
conecte `/predict`.
