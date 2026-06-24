# Reporte de trabajo — Jose Alfredo

**Proyecto:** RutaCamba — Asistente Turístico Inteligente
**Tarea asignada:** Analizar el código y entrenar el modelo de Transfer Learning (ResNet18, "B2")
**Fecha:** 2026-06-22
**Entorno:** Windows 11 · GPU NVIDIA RTX 4050 Laptop (6 GB) · venv `envDeepLearning` (Python 3.10)

---

## 1. Resumen ejecutivo

Se entrenó con éxito el modelo **B2 (Transfer Learning con ResNet18)** para la
clasificación de los 8 landmarks de Santa Cruz. El modelo alcanzó **99.15 % de
val accuracy**, superando ampliamente al modelo desde cero **B1 (TuristCNN,
91.53 %)** y cumpliendo el criterio de la rúbrica **B2 > B1**.

En el proceso se detectaron y corrigieron varios problemas que impedían entrenar
(código revertido, falta del dataset local, entorno sin GPU, configuración de
WandB y un bug de exportación). Todo el entrenamiento quedó registrado en WandB
con su artifact correspondiente.

| Modelo | Arquitectura | Val acc | Test acc | Estado |
|--------|--------------|---------|----------|--------|
| B1 | TuristCNN (desde cero) | 91.53 % | 90.76 % | Entrenado (en Colab por Nicole) |
| **B2** | **ResNet18 (Transfer Learning)** | **99.15 %** | **100.00 %** | **Entrenado localmente ✅** |

---

## 2. Análisis inicial del proyecto

Antes de entrenar se hizo un repaso del repositorio para entender qué estaba listo
y qué faltaba:

- **Entrenamiento (Fase 3):** vive en `src/landmarks/` — `train.py` (loop),
  `cnn.py` (TuristCNN, B1), `transfer.py` (ResNet18, B2), `predictor.py`
  (inferencia). Se alimenta de `src/data/` (dataset, transforms, dataloaders).
- **Seguimiento (Fase 5):** `src/tracking/wandb_utils.py` con `init_run`,
  `log_epoch` y `log_model_artifact`, enganchados en `train.py`.
- **Hallazgo crítico:** varios archivos estaban **revertidos a *stub*** en el
  working tree (implementados en el último commit, pero borrados localmente):
  `translate.py`, `wandb_utils.py`, `generate_translations.py` y parte de
  `cnn.py`. Se restauraron con `git restore` antes de continuar.

---

## 3. Preparación del dataset

El dataset **no estaba en la máquina local**. Se determinó su ubicación real:

- **Fuente:** Google Drive, carpeta **"Places"** (compartida por Leandro),
  organizada por clase (`Places/<clase>/*.jpg`). **No** está en S3 (las
  credenciales AWS del `.env` son placeholders inválidos).
- **División train/val/test:** la define `data/manifest.csv` (553 / 118 / 119,
  790 imágenes totales, 8 clases).

### Pasos realizados
1. Descarga de la carpeta "Places" desde Drive (zip de ~1.7 GB) y extracción.
2. Creación del script **`scripts/prepare_dataset.py`** (nuevo), que lee el
   manifest y copia cada imagen a la estructura que espera el entrenamiento:
   `data/<split>/<clase>/<archivo>`.
3. Verificación: **553 train / 118 val / 119 test**, 8 clases en cada split.

```bash
python scripts/prepare_dataset.py --places-dir "<ruta>/Places_extracted/Places"
```

---

## 4. Configuración del entorno (GPU)

El entrenamiento debía correr en la GPU del equipo (RTX 4050), pero el entorno
no estaba listo:

- El Python que se usaba inicialmente era el **global**, con `torch 2.9.0+cpu`
  (sin CUDA).
- El venv del proyecto, **`envDeepLearning` (Python 3.10), estaba vacío**.

### Pasos realizados
1. Instalación en el venv de **torch 2.9.0+cu128** y **torchvision 0.24.0+cu128**
   (compatibles con el driver CUDA 12.9 de la RTX 4050), más `wandb` y `pillow`.
2. Verificación: `torch.cuda.is_available() == True`, GPU detectada
   (`NVIDIA GeForce RTX 4050 Laptop GPU`).

---

## 5. Entrenamiento de B2 (Transfer Learning)

### Mejora aplicada al código
`src/landmarks/train.py` originalmente, con `--model transfer`, **solo entrenaba
la capa FC con el backbone congelado** y nunca descongelaba `layer4`. Con el
backbone 100 % congelado, B2 difícilmente superaría a B1.

Se agregó el flag **`--finetune-layer4`** (junto a `--freeze-epochs` y
`--finetune-lr`) para implementar las **dos fases** que pide el plan:

- **Fase (a):** backbone congelado, se entrena solo la FC (`lr = 1e-3`).
- **Fase (b):** se descongela `layer4` y se afina con `lr = 1e-4`.

### Comando ejecutado
```bash
# (con el venv envDeepLearning y tras cargar .env para WandB)
python -m src.landmarks.train --model transfer --epochs 15 --finetune-layer4
```

### Resultados
15 épocas (7 congelado + 8 fine-tuning). El salto clave ocurrió en la época 8,
al descongelar `layer4`:

| Fase | Época | Val accuracy |
|------|-------|--------------|
| (a) backbone congelado | 1 → 7 | 53.4 % → 88.98 % |
| **(b) descongela layer4** | 8 | **97.46 %** |
| (b) fine-tuning | 10 → 15 | **99.15 %** |

- **Mejor checkpoint:** época 14 — `val_loss = 0.0213`, **`val_acc = 99.15 %`**.
- **Modelo exportado:** `models/transfer_learning.pt` (TorchScript).
- **WandB:** run `enedjxj9` + artifact `best-transfer` subido.
  → https://wandb.ai/lozadaleonn-ciencialink/rutacamba/runs/enedjxj9

---

## 6. Evaluación final en test (comparativa B1 vs B2)

Se evaluaron **ambos modelos** sobre el conjunto de **test (119 imágenes)**, que
por rúbrica se toca **una sola vez**. Script: `scripts/evaluate_test.py`.

### Tabla comparativa (test)

| Modelo | Test acc | Precision (macro) | Recall (macro) | F1 (macro) | Parámetros | Tamaño | Tiempo entren.\* |
|--------|----------|-------------------|----------------|------------|------------|--------|------------------|
| B1 (CNN scratch) | 90.76 % | 92.12 % | 88.89 % | 89.87 % | 422 824 | 1.8 MB | ~53 min (Colab) |
| **B2 (ResNet TL)** | **100.00 %** | 100 % | 100 % | 100 % | 11 180 616 | 44.9 MB | ~8 min (RTX 4050) |

> \* Los tiempos **no son comparables directamente**: B1 se entrenó en Colab
> (hardware desconocido) y B2 localmente en la RTX 4050. El `_runtime` que reporta
> WandB para B2 (~15 min) está inflado porque el run se reanudó para subir el
> artifact; el entrenamiento real fue ~8 min.

### Lectura de resultados

- **B2 supera a B1 también en test** (100 % vs 90.76 %), confirmando lo de validación.
- **B1 no muestra overfitting:** test 90.76 % ≈ val 91.53 %. Sus errores se
  concentran en ParqueUrbano ↔ Tahuichi y en Plaza24 (recall 0.70).
- **B2 perfecto en las 8 clases.** Para la defensa conviene aclarar: el test es
  chico (119 imágenes) y los landmarks son visualmente muy distintos, así que un
  backbone preentrenado los separa con holgura. El 100 % es legítimo (test fue
  held-out y el dataset se purgó de near-duplicates en Fase 1), pero **no debe
  leerse como "infalible"**: con más imágenes y condiciones más variadas el
  accuracy bajaría algo.
- **Costo vs beneficio:** B2 tiene ~26× más parámetros y pesa ~25× más que B1,
  pero rinde mejor. Justifica el valor del transfer learning frente a entrenar
  desde cero con un dataset chico.

Matrices de confusión: `docs/eval/confusion_b1.png` y `docs/eval/confusion_b2.png`.
Métricas completas: `docs/eval/metrics.json`.

---

## 7. Problemas encontrados y solucionados

| # | Problema | Solución |
|---|----------|----------|
| 1 | Archivos implementados revertidos a *stub* en el working tree | `git restore` de los 4 archivos |
| 2 | Dataset ausente en local; ETL de S3 sin implementar y credenciales AWS inválidas | Descarga desde Google Drive + `scripts/prepare_dataset.py` |
| 3 | torch local CPU-only; venv del proyecto vacío | Instalación de `torch/torchvision +cu128` en `envDeepLearning` |
| 4 | `WANDB_ENTITY=lozadaleonn` no existía → crash al iniciar WandB | Corregido a `lozadaleonn-ciencialink` en `.env` |
| 5 | `export_torchscript` fallaba en GPU (tensor de prueba en CPU vs pesos en CUDA) | Exportar desde copia en CPU + probar en el device del modelo recargado (`src/landmarks/cnn.py`) |

---

## 8. Archivos modificados / creados

- **`scripts/prepare_dataset.py`** (nuevo) — materializa el split desde el manifest.
- **`scripts/evaluate_test.py`** (nuevo) — evaluación en test + matrices de confusión + tabla comparativa.
- **`src/landmarks/train.py`** — flag `--finetune-layer4` (fine-tuning de dos fases).
- **`src/landmarks/cnn.py`** — fix del bug de device en `export_torchscript`.
- **`docs/eval/`** (nuevo) — `confusion_b1.png`, `confusion_b2.png`, `metrics.json`.
- **`.env`** — corrección de `WANDB_ENTITY` (no se sube; está en `.gitignore`).
- **`.gitignore`** — se añadió `models/*.log` y un comentario aclaratorio.

> **Nota sobre `.gitignore`:** las **imágenes de entrenamiento** (`data/train|val|test/`)
> y los **modelos** (`models/*.pt`, `*.pth`, `*.log`) **NO se suben al repo** a
> propósito. El dataset vive en Google Drive y los modelos se publican como
> artifacts de WandB. **Esto se subirá recién al final del proyecto.**

---

## 9. Experimentos adicionales: B3 (SE-CNN) y BA (ResNet-lite)

Adicionalmente al contrato B1/B2, se diseñaron, entrenaron y evaluaron dos
arquitecturas CNN desde cero para estudiar el efecto de distintos mecanismos
arquitectónicos con el mismo dataset chico (553 imágenes de entrenamiento).

### Arquitecturas implementadas

**B3 — TuristSECNN (Squeeze-and-Excitation CNN)**
Misma estructura de 4 bloques conv (32→64→128→256) que B1, con la adición de un
módulo SE (Squeeze-and-Excitation) al final de cada bloque. El SE aprende un peso
por canal que recalibra los feature maps según su importancia relativa para la clase.
Costo extra mínimo: 444,584 parámetros (~5 % más que B1), mismo tamaño de archivo (~1.9 MB).

**BA — TuristResNet (ResNet-lite)**
Stem Conv7×7 (stride=2) + MaxPool, seguido de 3 bloques residuales (64→128→256) con
skip connections 1×1 cuando cambian las dimensiones, y cabeza FC. 1,266,632 parámetros,
~5.2 MB. Entrenamiento con mismos hiperparámetros (30 épocas, lr=1e-3, Adam).

### Resultados en test (119 imágenes, tocado una sola vez)

| Modelo | Arquitectura | Params | MB | Val acc | Test acc | Prec (macro) | Recall (macro) | F1 (macro) |
|--------|-------------|--------|----|---------|----------|-------------|----------------|------------|
| B1 | TuristCNN (base) | 422K | 1.8 | 91.53 % | 90.76 % | 92.12 % | 88.89 % | 89.87 % |
| **B3** | **TuristSECNN** | **444K** | **1.9** | **92.37 %** | **92.44 %** | **91.36 %** | **91.32 %** | **91.24 %** |
| BA | TuristResNet | 1.27M | 5.2 | 92.37 % | 87.39 % | 86.49 % | 84.55 % | 85.35 % |
| B2 | ResNet18 (TL) | 11.18M | 44.9 | 99.15 % | 100.00 % | 100 % | 100 % | 100 % |

### Lectura de resultados

- **B3 (SE-CNN) supera a B1** en test (92.44 % vs 90.76 %) con prácticamente el mismo
  tamaño de modelo. El mecanismo de atención de canal es eficiente: por solo ~22K
  parámetros extra, la red aprende qué canales son más discriminativos por clase.
  Mejora notable en ParqueUrbano (recall 92 % vs 83 % en B1) y elimina los errores
  en CatedralMunicipal y Ventura.

- **BA (ResNet-lite) queda debajo de B1** (87.39 % vs 90.76 %) a pesar de tener
  val acc idéntica (92.37 %). La brecha val/test de ~5 pp indica sobreajuste moderado:
  1.26M parámetros es excesivo para solo 553 imágenes de entrenamiento. Con dataset
  chico, la profundidad extra de ResNet-lite no ayuda — los skip connections requieren
  suficientes datos para materializar su ventaja teórica.

- **Ranking final:** B2 (100 %) > B3 (92.44 %) > B1 (90.76 %) > BA (87.39 %).

- **Mejor opción liviana:** B3 — misma huella de B1 (1.9 MB), mejor accuracy, y más
  rápido de entrenar (1685 s vs 3155 s). Candidato natural si se requiere un modelo
  pequeño y portable.

Matrices de confusión: `docs/eval/confusion_b3.png` y `docs/eval/confusion_ba.png`.
WandB runs: B3 → `wbay2jxu`, BA → `3i5ickz4`.

---

## 10. Pendientes

> **✅ La evaluación en test y la comparativa B1/B2/B3/BA YA SE COMPLETARON**
> (ver secciones 6 y 9). Los 4 modelos se evaluaron en test **una sola vez**.

Pendientes del proyecto **fuera de esta tarea** (otras fases):

- [ ] `data/translations.json` (Fase 4 — Traducción LLM); requiere `ANTHROPIC_API_KEY` real.
- [ ] Galería de Re-ID + `verify_identity` end-to-end (Fase 2).
- [ ] Notebooks ejecutados con salidas (`03_cnn_scratch.ipynb`, `04_transfer_learning.ipynb`).
- [ ] Informe final + `README.md` (Fase 7).
