# PLAN SCRUM — Asistente Turístico Inteligente (RutaCruceña)

**Curso:** Redes Neuronales y Aprendizaje Profundo — UCB Santa Cruz
**Duración:** 7 días (Mié 10/06 → Mié 17/06) · 3 sprints · Equipo de 5
**Meta:** sistema end-to-end (Re-ID → clasificación → traducción LLM → API + UI) con
tracking en WandB. Al cerrar el Scrum, **cada uno terminó su fase y todo corre al 100%.**

> Tareas tomadas de los `.md` de cada fase (`docs/fases/`). Los dueños son los de
> `context.md`. Lo único agregado es el marco Scrum (ceremonias, Definition of Done).

---

## 1. Equipo, fases y carpetas (dueños reales)

| Miembro | Fase(s) que posee | Carpetas | Rama | Pts |
|---------|-------------------|----------|------|-----|
| **Diego Lewenstein** | Fase 1 — Datos | `ETL/`, `src/data/`, `notebooks/01` | `feat/datos` | 10 |
| **Leandro Miranda** | Fase 2-A — Re-ID (embeddings, métricas, t-SNE) | `src/reid/embeddings.py`, `metrics.py`, `notebooks/02a` | `feat/reid-embeddings` | parte de 15 |
| **Jose Alfredo** | Fase 2-B — Re-ID (galería, ranking, acceso) **+** Fase 4 — LLM | `src/reid/{gallery,ranking,access}.py`, `notebooks/02b`, `src/translation/`, `scripts/generate_translations.py` | `feat/reid-access`, `feat/llm` | parte de 15 + 5 |
| **Alejandro Ojeda** | Fase 3 — Landmarks (B1 + B2) | `src/landmarks/`, `notebooks/03`, `notebooks/04` | `feat/landmarks` | 20 |
| **Nicole Lozada** | Fase 5 — WandB **+** Fase 6 — Deploy **+** Fase 7 — Informe | `src/tracking/`, `api/`, `ui/`, `README.md`, `report.pdf` | `feat/wandb`, `feat/deploy`, `feat/informe` | 5 + 5 + 40 |

> **Carga:** Jose (2 fases) y Nicole (3 fases) son los más cargados. El plan secuencia
> sus fases para que no choquen (Jose: LLM en Sprint 1, Re-ID en Sprint 2; Nicole: WandB
> en Sprint 1, Deploy en Sprint 2, Informe en Sprint 3) y Diego apoya al terminar Fase 1.

---

## 2. Marco Scrum

| Elemento | Quién / qué |
|----------|-------------|
| **Product Owner** | El ingeniero/docente — la **rúbrica** son los criterios de aceptación |
| **Scrum Master** | Nicole (dueña de integración/informe) — modera dailies y desbloquea |
| **Equipo** | Los 5 |
| **Daily Scrum** | 15 min cada mañana: ayer / hoy / bloqueos |
| **Sprint Planning / Review / Retro** | Al inicio y cierre de cada sprint |

**Definition of Done (cualquier tarea):** (1) código en la rama + PR revisado por 1
compañero; (2) decisión registrada en `docs/decisiones/faseX_decisiones_nombre.md` con
"por qué esto y no lo otro"; (3) criterio de rúbrica verificable (corre y tiene salida);
(4) el **test set se toca una sola vez** (Día 5) — todo lo demás se decide con validación.

---

## 3. SPRINT 1 — Fundaciones (Días 1–2)

**Objetivo:** dataset particionado, esqueletos de todos los módulos corriendo, traducción
LLM y galería Re-ID funcionando aisladas.

### 📅 Día 1 — Mié 10/06 · Kickoff + esqueletos
- **Todos (1 h):** confirmar las 8 clases; repartir 2 clases de recolección por persona
  (~100 img c/u); **el coordinador** crea el repo con la estructura, `src/config.py`,
  `docs/interfaces/contratos.md`, `.gitignore` y lo sube a `main`; crear WandB team + canal.
- **Diego (F1):** estructura de `src/data/` y `ETL/`, convención de nombres de imágenes,
  planilla de fuentes (autor/licencia). Empezar recolección de sus 2 clases.
- **Leandro (F2-A):** armar la galería inicial (3–5 fotos por persona del equipo);
  esqueleto de `embeddings.py` con DeepFace/ArcFace; primer `get_embedding` funcionando.
- **Jose (F4):** esqueleto de `src/translation/translate.py` + catálogo de los **8 landmarks**
  (mismos IDs de `config.LANDMARK_CLASSES`) en `generate_translations.py`. *(Arranca por LLM
  porque su parte de Re-ID depende de los embeddings de Leandro.)*
- **Alejandro (F3):** diseñar `LandmarkCNN` en papel (≥3 conv + BN + dropout + FC);
  esqueleto de `src/landmarks/cnn.py` y `train.py`.
- **Nicole (F5):** esqueleto de `src/tracking/wandb_utils.py` (`init_run`, `log_epoch`,
  `log_model_artifact`); crear el proyecto WandB (config, naming). **Pasar las firmas a
  Alejandro y Leandro** para que las usen en sus loops.
- **Todos (resto):** recolectar sus 2 clases. **Meta: ≥60 img/clase.**

### 📅 Día 2 — Jue 11/06 ⬅️ HOY · Dataset listo + pipelines en humo
- **Diego (F1):** consolidar dataset (limpieza duplicados/corruptas, **split estratificado
  70/15/15 sin solapamiento**, transforms resize 256 → crop 224 → norm ImageNet,
  augmentation moderado solo en train, `get_dataloaders()`). Notebook `01_datos_eda.ipynb`
  (ejemplos, distribución, **desbalance**). Subir a S3 + script de descarga.
- **Leandro (F2-A):** `build_gallery` con embeddings cacheados; baseline de top-1/top-k con
  la galería (modelo preentrenado, sin entrenar todavía).
- **Jose (F4):** `translate.py` funcional — traducción de salida (lookup) + normalización de
  entrada en idioma inesperado (langdetect + LLM) + **fallback NLLB-200**. Tests manuales de
  los 3 casos. **Corregir la inconsistencia 8-vs-10 landmarks.**
- **Alejandro (F3):** implementar la CNN en PyTorch; **smoke test de 2 épocas** con un subset
  usando los DataLoaders de Diego (loss baja, logging a WandB con `wandb_utils` de Nicole OK).
- **Nicole (F5→F6):** verificar que el run de Alejandro aparece en WandB; arrancar esqueleto
  de `api/main.py` con endpoints stub (`/verify`, `/predict`, `/normalize`) contra los contratos.

**🔚 Review 1:** dataset completo + DataLoaders, EDA hecho, CNN loggeando a WandB,
traducción LLM aislada OK, galería + baseline Re-ID, API stub levantando. **Retro:** ¿alguien
bloqueado por datos o galería?

---

## 4. SPRINT 2 — Entrenamiento y métricas (Días 3–5)

**Objetivo:** los tres modelos entrenados superando umbrales (CNN ≥45 %, TL ≥75 % y > CNN),
Re-ID con métricas completas, todo en WandB, API + UI con modelos reales.

### 📅 Día 3 — Vie 12/06 · Arranca el entrenamiento
- **Diego (F1):** iterar augmentation/balanceo según EDA (weighted sampler si hay
  desbalance). Al cerrar Fase 1, **pasa a apoyar:** documentar origen de datos + empezar README.
- **Leandro (F2-A):** implementar `evaluate_reid` — **mAP variante re-ID** con split
  probe/gallery (lo más delicado de la fase; NO usar `average_precision_score` ingenuo).
- **Jose (F2-B):** ahora que Leandro tiene embeddings, implementar `gallery.py` + `ranking.py`
  (distancia coseno, ranking ordenado).
- **Alejandro (F3-B1):** entrenamiento completo CNN **≥30 épocas**: curvas train/val loss +
  accuracy, guardar mejor checkpoint (**menor val loss**), log a WandB.
- **Nicole (F5):** coordinar que B1 y la **evaluación de Re-ID** se registren en WandB
  *(esto cubre el hueco de "entrenamiento de Re-ID" de la Fase 5)*; empezar comparación de runs.

### 📅 Día 4 — Sáb 13/06 · TL + métricas Re-ID + umbral
- **Leandro (F2-A):** cerrar top-1/top-k/mAP; **visualización PCA/t-SNE con interpretación**;
  loggear las métricas de Re-ID a WandB.
- **Jose (F2-B):** `access.py` → `verify_identity`; **justificar el umbral con ROC/EER**
  (distribución de distancias genuinos vs impostores, no el 0.5 a dedo); demo aceptar/rechazar;
  notebook `02b`.
- **Alejandro (F3-B2):** Transfer Learning ResNet18 en dos fases (congelar + nueva FC lr=1e-3,
  luego fine-tuning de `layer4` lr=1e-4); registrar tiempo y nº de params; ajustes si B1<45 %;
  export TorchScript de B1 + prueba de carga.
- **Nicole (F6):** conectar la API a los TorchScript reales a medida que se exportan
  (`LandmarkPredictor` lo expone Alejandro); esqueleto de `ui/app.py` en Gradio.

### 📅 Día 5 — Lun 15/06 · Evaluación final + integración + notebooks
- **Diego (F1):** dataset finalizado; verificar no solapamiento; `01_datos_eda.ipynb`
  ejecutado con salidas visibles.
- **Leandro (F2-A):** `02a_reid_embeddings.ipynb` ejecutado (embeddings + t-SNE + métricas);
  confirmar top-k/mAP registrados en WandB.
- **Jose (F2-B + F4):** integrar Re-ID a la API con Nicole (`/verify` usa galería real +
  umbral); `02b` ejecutado; confirmar `translations.json` curado para que `/predict` traduzca.
- **Alejandro (F3):** **evaluación final en test (UNA sola vez):** accuracy, precision,
  recall, **matriz de confusión**; **tabla comparativa B1 vs B2** (accuracy, params, tiempo,
  tamaño); export TorchScript de B2 + prueba de carga; notebooks `03` y `04` ejecutados.
  ✅ Verificar **B1 ≥ 45 %, B2 ≥ 75 % y B2 > B1**.
- **Nicole (F5 + F6):** WandB — checkpoints como artifacts, comparación de runs (parallel
  coordinates), **bonus** mini sweep lr/batch; UI completa consumiendo la API (verificación →
  top-k → traducciones); generar **enlace WandB compartible**.
- **Todos (fin):** prueba end-to-end interna — alguien ajeno a cada módulo corre el flujo
  siguiendo solo el README. Registrar bugs.

**🔚 Review 2:** CNN ≥45 %, TL ≥75 % y > CNN, Re-ID con top-k/mAP/umbral/t-SNE, TorchScript
exportados y cargando, WandB completo con artifacts + comparación, API + UI con modelos
reales y traducciones conectadas. **Retro:** bugs priorizados para Sprint 3.

---

## 5. SPRINT 3 — Integración, informe y defensa (Días 6–7)

**Objetivo:** sistema pulido, informe de 10 páginas, video y defensa ensayada.

### 📅 Día 6 — Mar 16/06 · Pulido + informe
- **Diego (F1→apoyo):** sección de datos del README; verificar que el dataset **NO** está en
  el repo y que el script de descarga funciona en limpio.
- **Leandro (F2-A):** sección Re-ID del informe (embeddings/métricas) + respuestas de
  defensa (clasificación vs retrieval, qué representa el espacio de embeddings, **mAP re-ID
  vs detección**).
- **Jose (F2-B + F4):** sección de informe (umbral/acceso + LLM/fallback) + respuestas de
  defensa (cómo eligieron el umbral, qué pasa si el LLM falla). Con Nicole: manejo de errores
  en la API (LLM caído → fallback **visible** en la UI).
- **Alejandro (F3):** sección de informe B1 + B2 + respuestas de defensa (arquitecturas,
  nº de params y por qué difieren, overfitting: cómo lo detectaron y mitigaron). Corregir bugs.
- **Nicole (F5+F6+F7):** corregir bugs del end-to-end; recolectar las secciones e integrar el
  `report.pdf` (pregunta–respuesta); empezar a ensamblar `docs/guia_de_estudio.md` desde
  `docs/decisiones/`; insertar capturas y enlaces de WandB.
- **Todos:** revisar las preguntas de defensa del enunciado (sección 8) y escribir respuestas
  cortas para su módulo desde su bitácora de decisiones.

### 📅 Día 7 — Mié 17/06 · 🏁 ENTREGA
- **Todos (mañana):** ensayo de demo en vivo del flujo end-to-end (2 corridas). **Congelar
  `main`:** solo hotfix.
- **Diego + Nicole:** grabar el video de 3–5 min coherente con el informe (problema →
  arquitectura → demo → resultados).
- **Alejandro + Jose:** cierre del informe (exportar a PDF 10 págs, verificar enlaces WandB),
  subir al repo.
- **Nicole (F7):** `README.md` final + `guia_de_estudio.md` ensamblada + checklist de
  entregables + verificación del repo público.
- **Leandro:** verificación final de entregables.
- **Todos (tarde):** ensayo de defensa oral (≤5 min): cada uno responde 2 preguntas de los
  demás sobre módulos ajenos. *La defensa ajusta la nota individual — todos deben entender todo.*

---

## 6. Checklist de entregables (Día 7)

- [ ] Repo GitHub público, organizado, **sin dataset**
- [ ] 4 notebooks ejecutados con salidas (EDA, Re-ID, CNN, TL)
- [ ] Modelos `.pt` TorchScript + prueba de carga
- [ ] API FastAPI (`/verify`, `/predict` condicionado, `/translate`) sin re-entrenar
- [ ] UI Gradio consumiendo la API (top-k + probabilidades + EN/FR/IT)
- [ ] WandB: runs, comparación, ≥1 artifact, enlace compartible
- [ ] `report.pdf` (10 págs, pregunta–respuesta, enlaces WandB)
- [ ] `README.md` completo · Video 3–5 min · `guia_de_estudio.md`
- [ ] Defensa ensayada (todos entienden todos los módulos)

---

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| No llegar a 60 img/clase | Día 1 todos recolectan; clases de reserva (Laguna Volcán / Ventura Mall); scraping citando fuente. |
| CNN < 45 % | Día 4 reservado para ajustes (lr, augmentation, arquitectura). |
| TL no supera 75 % | Fine-tuning de más capas / EfficientNet-B0 / más épocas (Día 4–5). |
| LLM caído en la demo | Fallback NLLB-200 + traducciones precalculadas — **probarlo sí o sí**. |
| Re-ID sin run en WandB | Día 3: entrenar/loggear la red de embeddings o, mínimo, loggear la evaluación. |
| Integración de último minuto | API con stubs desde el Día 2; integración progresiva, no big-bang. |
| Jose/Nicole sobrecargados | Diego apoya al cerrar Fase 1; fases secuenciadas para no colisionar. |

---

## 8. Cadencia diaria
- **Daily Scrum 15 min** cada mañana (ayer / hoy / bloqueos).
- Push diario a la rama propia + PR cuando el módulo esté estable.
- Documentar cada decisión en `docs/decisiones/` **el mismo día** que se toma.
