# Bitácora de decisiones — Fases 5 y 6 — Nicole Lozada

> Este archivo cubre WandB (Fase 5) y Despliegue (Fase 6).

---

# FASE 5 — WandB

## Decisión 001 — WandB vs MLflow vs TensorBoard

- **Fecha:** 2026-06-11
- **Contexto / problema:** El enunciado exige experiment tracking. ¿Qué herramienta elegimos para registrar los entrenamientos de CNN (Fase 3) y las métricas de Re-ID (Fase 2)?
- **Qué elegí:** WandB (Weights & Biases).
- **Por qué lo elegí:**
  1. **El enunciado lo exige explícitamente** — no hay libertad de elección aquí, pero la razón técnica es válida.
  2. **Dashboards compartibles sin levantar servidor** — con MLflow necesitás un `mlflow server` corriendo; con WandB solo compartís un link (clave para trabajar en equipo en un proyecto académico).
  3. **Parallel coordinates view nativa** — en el enunciado se pide comparar runs de CNN scratch vs Transfer Learning; WandB tiene esta vista lista sin configuración extra.
  4. **Gestión de artifacts integrada** — `wandb.Artifact(type="model")` sube y versiona los `.pt` directamente desde Python, sin configurar un artifact store separado.
  5. **Sweep bayesiano con una función** — `wandb.sweep(config)` + `wandb.agent(...)` lanza búsqueda de hiperparámetros sin infraestructura adicional.
- **Alternativa(s) que descarté y POR QUÉ no:**
  - **MLflow:** necesita un servidor de tracking y un artifact store (S3 o carpeta local compartida). Para un proyecto académico es overhead innecesario. Además, la UI de comparación de runs es menos visual.
  - **TensorBoard:** no tiene dashboards compartibles sin servir desde un servidor público. Tampoco tiene gestión nativa de artifacts ni sweeps. La comparación entre runs distintos (distintos experimentos, no solo distintas ejecuciones) es más incómoda.
- **Posible pregunta de defensa que esto responde:** "¿Por qué WandB y no TensorBoard/MLflow?" → Dashboards compartibles sin infraestructura propia, artifacts versionados, y sweep bayesiano integrado. El equipo puede ver los runs desde cualquier navegador con el link del proyecto.

---

## Decisión 002 — Cómo cubrir el re-ID sin loop de entrenamiento

- **Fecha:** 2026-06-11
- **Contexto / problema:** DeepFace/ArcFace es un modelo pre-entrenado que NO se fine-tunea en este proyecto. No hay epochs de entrenamiento para Re-ID, entonces no hay un "run" natural para WandB. Sin esto, el dashboard quedaría vacío para Fase 2 y perderíamos puntos de rúbrica.
- **Qué elegí:** Registrar un run de **evaluación** del Re-ID en WandB. Leandro llama a `init_run("reid_eval", config)` con los hiperparámetros fijos (modelo, distancia, umbral) y luego `log_epoch({"top1": ..., "top5": ..., "map": ...}, step=0)` con las métricas finales del conjunto de evaluación. Un solo step es suficiente porque no hay epochs.
- **Por qué lo elegí:** Permite que el dashboard de WandB incluya los resultados de Re-ID junto a los runs de CNN, haciendo posible una comparación global del sistema. Los hiperparámetros (umbral de distancia, modelo ArcFace) aparecen en la tabla de comparación aunque no hayan sido "entrenados". Es la solución mínima que cumple la rúbrica sin falsear que hubo entrenamiento.
- **Posible pregunta de defensa que esto responde:** "¿Cómo registraste el Re-ID si DeepFace no se entrena?" → Se logueó un run de evaluación con las métricas finales (top-1, top-5, mAP) y los hiperparámetros de configuración (umbral, modelo). No hay epochs porque no hay entrenamiento, pero el experimento queda documentado y comparable en el dashboard.

---

# FASE 6 — Despliegue

## Decisión 003 — Carga de modelos en startup vs en cada request

- **Fecha:**
- **Contexto / problema:** ¿Cuándo cargo LandmarkPredictor y TranslationService?
- **Qué elegí:**
- **Por qué lo elegí:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 004 — Token en memoria vs JWT vs base de datos

- **Fecha:**
- **Contexto / problema:** El endpoint `/predict` requiere que el usuario se haya verificado.
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 005 — Gradio vs Streamlit

- **Fecha:**
- **Contexto / problema:** Necesito una interfaz web para la demo.
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:**
