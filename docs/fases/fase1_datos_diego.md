# Fase 1 — Datos y preprocesamiento · Diego Lewenstein

**Peso:** 10 pts · **Carpetas principales:** `src/data/` + `ETL/` + `notebooks/01_datos_eda.ipynb`

> Sos la base de TODO. Sin tu dataset nadie entrena nada, y la calidad de tus datos
> es el techo de accuracy del proyecto. Si tu dataset sale flojo, Alejandro no llega
> al 75% en la Fase 3 y se cae todo. Tomate en serio el volumen y la limpieza.

---

## 1. Archivos que te pertenecen (trabajá SOLO acá)

| Archivo | Qué va adentro |
|---------|----------------|
| `ETL/etl_s3.py` | Descarga desde S3, deduplica, valida, arma train/val/test |
| `src/data/__init__.py` | Exporta `get_dataloaders` para que sea importable |
| `src/data/dataset.py` | `Dataset` de PyTorch que lee las carpetas |
| `src/data/transforms.py` | `get_train_transforms()` y `get_eval_transforms()` |
| `src/data/dataloaders.py` | `get_dataloaders()` ← lo consume la Fase 3 |
| `notebooks/01_datos_eda.ipynb` | EDA: ejemplos, distribución, desbalance |
| `requirements/fase1.txt` | tus dependencias (torch, torchvision, pillow, boto3, matplotlib, scikit-learn) |

**No toques** `src/config.py` salvo para LEER `LANDMARK_CLASSES`, `RESIZE`, `CROP`,
`IMAGENET_MEAN/STD`. Esas constantes ya están definidas; usalas, no las dupliques.

**No toques** los archivos de otras fases en `src/`. Tu territorio es solo `src/data/` y `ETL/`.

---

## 2. Lo que tu código DEBE exponer (contrato — no lo cambies)

```python
# src/data/dataloaders.py
def get_dataloaders(batch_size: int = 32) -> tuple:
    # devuelve (train_loader, val_loader, test_loader, class_names)
    # class_names == src.config.LANDMARK_CLASSES (mismo orden)
    # cada loader entrega (imagen_tensor[B,3,224,224], label[B])
```

Alejandro (Fase 3) va a llamar exactamente a esto. Si cambiás la firma, le rompés
el entrenamiento. Leé `docs/interfaces/contratos.md` para ver todas las interfaces.

---

## 3. Paso a paso

1. **Recolectar imágenes** de las 8 clases de `LANDMARK_CLASSES` (ver `src/config.py`),
   desde distintos ángulos, distancias, horas e iluminación. **Apuntá a ~100 por clase**
   (el mínimo es 60, pero más datos = más chance de que la Fase 3 pase el 75%).
   Registrá la fuente de cada lote (foto propia / URL) en `data/fuentes.csv`. ✍️

2. **Subir a S3** organizadas por carpeta de clase:
   `s3://tu-bucket/raw/<clase>/...`

3. **Escribir `ETL/etl_s3.py`:** descarga de S3 → descarta corruptas (abrí con PIL
   en try/except) y duplicados (hash MD5 del contenido) → reparte en
   **train/val/test ESTRATIFICADO 70/15/15** (cada clase representada en las tres
   particiones). Verificá que **ninguna imagen quede en dos particiones** (la
   validación sale del train; el test no se toca para elegir modelo). ✍️

4. **`src/data/transforms.py`:**
   - `get_eval_transforms()`: `Resize(256)` → `CenterCrop(224)` → `ToTensor` →
     `Normalize(IMAGENET_MEAN, IMAGENET_STD)`. Esto va en val y test.
   - `get_train_transforms()`: lo de arriba **+ augmentation MODERADO** (flips
     horizontales, rotaciones leves, `ColorJitter` suave). ✍️ Justificá por qué
     moderado y no agresivo (un recorte fuerte puede borrar el rasgo que identifica
     el lugar).

5. **`src/data/dataset.py` + `dataloaders.py`:** Dataset que lee las carpetas y
   aplica los transforms correctos según partición; `get_dataloaders()` arma los 3
   loaders. Test/val usan `get_eval_transforms()`, **augmentation solo en train**.

6. **`notebooks/01_datos_eda.ipynb`:** mostrá una grilla de ejemplos etiquetados,
   graficá la **distribución de clases** (barras) y **comentá el desbalance**. Si hay
   clases con muchas menos imágenes, decí cómo lo vas a mitigar (más recolección,
   class weights, o augmentation extra en esa clase). ✍️

7. **`src/data/__init__.py`:** exportá `get_dataloaders` para que se pueda importar
   como `from src.data import get_dataloaders`.

---

## 4. Checklist de rúbrica (lo que te dan los 10 pts)

- [ ] ≥ 8 clases con volumen adecuado; origen documentado y derechos respetados (4)
- [ ] EDA con ejemplos etiquetados, distribución y análisis de desbalance (3)
- [ ] resize/crop/normalización + augmentation + DataLoaders sin solapamiento (3)

**Riesgo a cuidar:** hay exactamente 8 clases (el mínimo, sin margen). Si una
sale difícil de fotografiar, no hay colchón. Conseguí volumen parejo entre clases.

---

## 5. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase1_decisiones_diego.md` (copiá `docs/PLANTILLA_decisiones.md`).
Registrá con justificación "por qué esto y no lo otro" al menos:

- Estratificado vs aleatorio en el split
- Augmentation moderado vs agresivo
- S3 vs guardar en repo
- 70/15/15 vs otra proporción
- Cómo trataste el desbalance de clases

Cada ✍️ de arriba es una entrada en la bitácora.

---

## 6. Cómo entregar

Rama `fase1-datos-diego` → PR a `develop`.
En tu PR mencioná que `get_dataloaders()` ya respeta el contrato para que
Alejandro pueda integrar sin problemas.

---

## 7. Notas de integración con otras fases

- **Fase 3 (Alejandro)** consume `src/data/dataloaders.get_dataloaders()`.
  Si todavía no terminaste, Alejandro puede entrenar contra un loader de prueba
  local mientras vos terminás; coordinen por el grupo.
- Las imágenes de **galería de Re-ID** (`data/gallery/`) son responsabilidad compartida
  con Jose y Leandro (Fase 2). Coordinad quién las sube.
