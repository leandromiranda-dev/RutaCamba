# Pendientes RutaCamba — Qué falta para el 100

> Estado al **2026-06-23**. Las fases 1–6 valen 60 pts en total; la Fase 7
> (informe + video + defensa) vale **40 pts**. El código solo da la mitad.

---

## Resumen rápido por persona

| Persona | Fases | Estado |
|---------|-------|--------|
| Diego Lewenstein | 1 — Datos | ✅ código listo · ⚠️ notebook sin outputs |
| Leandro Miranda | 2-A — Embeddings | ✅ código listo · ⚠️ notebook sin outputs · ⚠️ galería vacía |
| **Jose Alfredo** | 2-B — Re-ID · 4 — LLM | ✅ código listo · ❌ galería vacía · ❌ translations.json falta · ⚠️ umbral sin calibrar |
| Alejandro Ojeda | 3 — CNN/TL | ✅ B1 91.53% · ✅ B2 100% · ⚠️ notebooks sin outputs |
| Nicole Lozada | 5 — WandB · 6 — API · 7 — Informe | ✅ WandB OK · ⚠️ API no probada end-to-end · ❌ informe/video/README |

---

## ❌ BLOQUEANTES (el sistema no arranca sin esto)

### 1. `data/gallery/` — vacía
**Responsable: Leandro + Jose Alfredo**

La carpeta `data/gallery/` existe pero está vacía. Sin fotos de identidades
autorizadas, `verify_identity` falla en el primer request y la API queda
inutilizable. Es el bloqueo más crítico del proyecto.

**Qué hacer:**
- Leandro: correr `build_gallery()` + `save_gallery()` de `embeddings.py` con
  fotos reales de los integrantes (o de personas de prueba).
- La estructura esperada: `data/gallery/<identidad>/<foto>.jpg` (varias fotos
  por persona para mayor robustez).
- Una vez poblada, Jose Alfredo calibra el umbral (ver punto 3).

### 2. `data/translations.json` — no existe
**Responsable: Jose Alfredo (Fase 4)**

Sin este archivo, `TranslationService.get_landmark_translations()` falla y el
endpoint `/predict` no puede devolver traducciones. Bloquea la API.

**Qué hacer:**
- Conseguir una `ANTHROPIC_API_KEY` real y ponerla en `.env`.
- Correr: `python scripts/generate_translations.py`
- Revisar las traducciones a mano antes de la demo (son los 8 landmarks en ES/EN/FR/IT).
- Commitear `data/translations.json` al repo (es texto, no tiene secretos).

---

## ⚠️ PENDIENTES IMPORTANTES (bajan puntos si faltan)

### 3. Umbral de Re-ID sin calibrar
**Responsable: Jose Alfredo (Fase 2-B) — 4 pts en rúbrica**

`REID_THRESHOLD = 0.65` es el placeholder de `config.py`. La rúbrica exige
un **umbral justificado con ROC/EER**, no a dedo.

**Qué hacer:**
- Poblar la galería (punto 1 primero).
- Correr `notebooks/02b_reid_ranking_metrics.ipynb`:
  generar pares misma-persona (intra) y distinta-persona (inter), graficar
  distribuciones de distancia, trazar curva ROC, elegir el punto EER.
- Actualizar `REID_THRESHOLD` en `config.py` con el valor resultante.
- Documentar en `docs/decisiones/fase2_decisiones_jose.md`.

### 4. Flujo end-to-end sin probar
**Responsable: Nicole (Fase 6) — 5 pts en rúbrica**

`api/main.py` (131 líneas) y `ui/app.py` (140 líneas) están escritos pero
**nunca se probaron con datos reales juntos**. El flujo completo:

```
selfie + id → /verify → token → foto lugar → /predict → landmark + traducciones
```

**Qué hacer:**
- Instalar `requirements/fase6.txt`.
- Arrancar: `uvicorn api.main:app --reload` y `python ui/app.py`.
- Probar con una selfie real y una foto de landmark real.
- Ojo: conviven PyTorch (landmarks) + TensorFlow (DeepFace). Verificar que
  no choquen al cargar en el mismo proceso (testear el startup temprano).
- Documentar en `docs/decisiones/fase6_decisiones_nicole.md` (falta ese archivo).

### 5. Notebooks sin outputs ejecutados
**Responsables: todos**

Los 5 notebooks existen pero ninguno tiene outputs visibles. El informe y la
defensa los necesitan con resultados reales.

| Notebook | Responsable | Estado |
|----------|-------------|--------|
| `01_datos_eda.ipynb` | Diego | Sin outputs |
| `02a_reid_embeddings.ipynb` | Leandro | Sin outputs |
| `02b_reid_ranking_metrics.ipynb` | Jose Alfredo | Sin outputs |
| `03_cnn_scratch.ipynb` | Alejandro | Sin outputs |
| `04_transfer_learning.ipynb` | Alejandro | Sin outputs |

**Qué hacer:** ejecutar cada notebook de punta a punta y hacer commit con
las celdas ejecutadas y los gráficos visibles (WandB, matrices de confusión,
curvas de entrenamiento, distribuciones de Re-ID, EDA).

---

## 📄 FASE 7 — INFORME + VIDEO + DEFENSA (40 pts)

Esta es la fase más pesada. Aunque todo el código funcione perfecto,
sin esto no se llega al 100.

### 6. README.md completo
**Responsable: Nicole (Fase 7)**

El README actual (39 líneas) es un placeholder. Debe tener:
- Descripción del sistema y del equipo
- Instrucciones de instalación paso a paso
- Cómo reconstruir el dataset desde Google Drive (`scripts/prepare_dataset.py`)
- Cómo bajar los modelos desde WandB
- Cómo arrancar la API y la UI (variables de entorno, puertos)
- Enlace al proyecto de WandB: `https://wandb.ai/lozadaleonn-ciencialink/rutacamba`
- Tabla de resultados B1 vs B2 (y B3/BA si se incluyen)

### 7. `report.pdf` — 10 páginas
**Responsable: Nicole coordina; todos aportan contenido**

No existe. Formato pregunta–respuesta según el enunciado. Temas clave:

- Arquitecturas elegidas y nº de parámetros (CNN desde cero vs Transfer Learning)
- Por qué B2 supera a B1 (transfer learning + fine-tuning de layer4)
- Diferencia clasificación vs re-ID (embedding space vs logits)
- Cómo eligieron el umbral de Re-ID (ROC/EER)
- Overfitting: cómo lo detectaron y mitigaron (dropout, WeightedSampler, val set)
- Manejo de fallo del LLM (fallback a NLLB-200)
- Comparación de runs en WandB con capturas de dashboard
- Resultados de evaluación en test (tabla B1/B2 + matrices de confusión)

### 8. `docs/guia_de_estudio.md`
**Responsable: Nicole (compila; todos aportaron sus bitácoras)**

Se arma juntando las decisiones de todos los `docs/decisiones/` en un
documento de preguntas-respuestas listo para estudiar. Bitácoras disponibles:

- ✅ `fase1_decisiones_diego.md`
- ✅ `fase2_decisiones_leandro.md`
- ✅ `fase2_decisiones_jose.md`
- ✅ `fase3_decisiones_alejandro.md`
- ✅ `fase3_decisiones_jose.md` (9 decisiones incluyendo B3/BA)
- ✅ `fase4_decisiones_jose.md`
- ✅ `fase5_decisiones_nicole.md`
- ❌ `fase6_decisiones_nicole.md` — falta

### 9. Video 3–5 minutos
**Responsable: Nicole (con todos en pantalla)**

No grabado. Debe mostrar el flujo end-to-end **en vivo** en la UI Gradio:
1. Subir selfie + declarar identidad → acceso concedido/denegado
2. Subir foto de landmark → clasificación top-k con probabilidades
3. Ver traducciones en EN/FR/IT

Grabar con OBS o similar. Debe ser coherente con el informe.

### 10. Preparación de defensa individual
**Responsable: cada integrante**

La defensa es **individual** y puede bajar la nota de quien no entienda su parte.
Cada uno debe poder responder desde su bitácora. Ejes críticos por persona:

| Persona | Pregunta clave que pueden hacerle |
|---------|-----------------------------------|
| Diego | ¿Por qué el split 70/15/15 y cómo garantizaste no solapamiento? |
| Leandro | ¿Qué representa el espacio de embeddings de ArcFace? ¿Por qué coseno y no euclidiana? |
| **Jose Alfredo** | ¿Cómo calibraste el umbral? ¿Por qué pre-generar traducciones offline? ¿Por qué NLLB como fallback? |
| Alejandro | ¿Por qué 4 bloques y no 3 o 5? ¿Cómo detectaste overfitting? ¿Qué es el fine-tuning de layer4? |
| Nicole | ¿Por qué cargar modelos en startup? ¿Por qué token en memoria y no JWT? ¿Por qué Gradio y no Streamlit? |

---

## ✅ LO QUE YA ESTÁ LISTO

- Dataset: 790 imgs, split 70/15/15 (553/118/119), 8 clases ✅
- B1 (TuristCNN): 91.53% val, 90.76% test · artifact `best-cnn:v0` en WandB ✅
- B2 (ResNet18 TL): 99.15% val, 100% test · artifact `best-transfer` en WandB ✅
- B3 (SE-CNN): 92.37% val, 92.44% test · artifact `best-se_cnn` en WandB ✅
- BA (ResNet-lite): 92.37% val, 87.39% test · artifact `best-resnet_lite` en WandB ✅
- Matrices de confusión y métricas: `docs/eval/` ✅
- WandB integrado y todos los runs sincronizados ✅
- `src/reid/gallery.py`, `ranking.py`, `access.py` implementados ✅
- `src/translation/translate.py` + `generate_translations.py` implementados ✅
- `api/main.py` + `ui/app.py` implementados ✅
- Bitácoras de decisiones (7 de 8) ✅
- `ReporteJoseAlfredo.md` con análisis completo de B1/B2/B3/BA ✅

---

## Orden sugerido para cerrar el proyecto

```
1. Poblar data/gallery/             (Leandro → desbloquea todo lo de Re-ID)
2. Conseguir ANTHROPIC_API_KEY      (Jose → genera translations.json)
3. Calibrar umbral REID             (Jose → con notebook 02b + galería real)
4. Ejecutar los 5 notebooks         (cada uno el suyo)
5. Probar API end-to-end            (Nicole → api + ui juntos)
6. fase6_decisiones_nicole.md       (Nicole → 1 archivo que falta)
7. README.md completo               (Nicole)
8. guia_de_estudio.md               (Nicole compila, todos revisan)
9. report.pdf                       (Nicole redacta, todos aportan datos)
10. Video 3-5 min                   (todos disponibles para grabar)
11. Simulacro de defensa            (una ronda de preguntas entre todos)
```
