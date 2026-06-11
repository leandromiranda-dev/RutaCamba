# Fase 5 — Experiment tracking con WandB · Nicole Lozada

**Peso:** 5 pts · **Carpeta:** `src/tracking/`

> Vos definís la convención de logging de TODO el equipo y producís la comparación
> de experimentos. Ojo: las llamadas `wandb.log(...)` viven dentro del código de
> quien entrena (Alejandro en Fase 3, Leandro en Fase 2). Vos das las funciones
> helper y te encargás del dashboard, la comparación de runs, el artifact y (bonus)
> el sweep.

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `src/tracking/__init__.py` | exporta funciones de wandb_utils |
| `src/tracking/wandb_utils.py` | `init_run`, `log_epoch`, `log_model_artifact` |
| `requirements/fase5.txt` | wandb |

---

## 2. Lo que tu código DEBE exponer (contrato)

```python
# src/tracking/wandb_utils.py
def init_run(name: str, config: dict): ...
def log_epoch(metrics: dict, step: int): ...
def log_model_artifact(path: str, name: str): ...
```

Usan `config.WANDB_PROJECT` y `config.WANDB_ENTITY` de `src/config.py`.
Avisá a Alejandro y Leandro de estas firmas para que las llamen en sus loops.
**Entregá esta fase TEMPRANO** — Alejandro y Leandro la necesitan para entrenar.

---

## 3. Paso a paso

1. **`wandb_utils.py`:** wrappers finos sobre `wandb.init`, `wandb.log` y
   `wandb.Artifact`. Que los hiperparámetros vayan en `config` (así aparecen en las
   tablas de comparación).

2. **Coordiná el logging:** pasale a Alejandro y Leandro estas funciones. Cada
   entrenamiento (CNN scratch, Transfer Learning, y la **evaluación de Re-ID**) tiene
   que registrarse.
   ⚠️ **Hueco a cubrir:** como el Re-ID usa DeepFace pre-entrenado y NO se entrena,
   no hay "run de entrenamiento" de re-ID. Para no perder puntos, acordá con Leandro
   que **al menos las métricas de evaluación del re-ID (top-1, top-k, mAP) se logueen
   a WandB**. ✍️

3. **Artifact:** guardá al menos el mejor checkpoint (`.pt` de menor val loss) como
   `wandb.Artifact(type="model")`. Es criterio explícito (2 pts).

4. **Comparación de runs:** armá la vista de **parallel coordinates** y una tabla
   comparando B1 vs B2. **Bonus:** un `wandb sweep` bayesiano sobre learning rate y
   batch size del Transfer Learning. ✍️ por qué WandB y no MLflow/TensorBoard (lo
   exige el enunciado + dashboards compartibles sin levantar servidor).

5. **Enlaces compartibles:** activá visibilidad pública del proyecto o creá un
   **Report de WandB**. Ese enlace va al informe (Fase 7) y al README.

---

## 4. Checklist de rúbrica

- [ ] Todos los entrenamientos registrados (curvas, config, métricas finales) (3)
- [ ] Comparación de runs + ≥1 checkpoint como artifact + enlaces en el informe (2)

---

## 5. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase5_decisiones_nicole.md` (copiá `docs/PLANTILLA_decisiones.md`).
Registrá al menos:
- Por qué WandB y no MLflow o TensorBoard
- Por qué separar en `init_run` / `log_epoch` / `log_model_artifact` y no un wrapper único
- Cómo cubriste el hueco del re-ID (sin loop de entrenamiento)

Cada ✍️ = una entrada en la bitácora.

---

## 6. Cómo entregar

Rama `fase5-wandb-nicole` → PR a `develop`.
Esta fase habilita a las Fases 2 y 3, así que mergéala **temprano** (antes de que
Alejandro y Leandro terminen sus entrenamientos).
