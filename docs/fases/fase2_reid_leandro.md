# Fase 2 — Re-ID · Parte A (embeddings, métricas y visualización) · Leandro Miranda

**Peso:** 15 pts (compartidos con Jose) · **Carpeta:** `src/reid/embeddings.py`,
`src/reid/metrics.py`, `notebooks/02a_reid_embeddings.ipynb`

> La Fase 2 la hacen DOS personas. Vos (Leandro) hacés la parte de **medición**:
> generar embeddings, calcular las métricas (top-1, top-k, mAP) y visualizar el
> espacio. Jose hace la parte de **decisión** (galería, ranking, umbral, acceso).
> Coordinen el formato del embedding (está en el contrato) y no se pisen archivos.

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `src/reid/embeddings.py` | `get_embedding(image)` y `build_gallery(dir)` con DeepFace/ArcFace |
| `src/reid/metrics.py` | `evaluate_reid(...)` → top-1, top-k y **mAP variante re-ID** |
| `notebooks/02a_reid_embeddings.ipynb` | generación de embeddings + visualización PCA/t-SNE |
| `requirements/fase2.txt` | deepface, scikit-learn, numpy, matplotlib (coordinalo con Jose) |

**No toques** `gallery.py`, `ranking.py`, `access.py` (son de Jose).
**No toques** archivos de otras fases.

---

## 2. Lo que tu código DEBE exponer (contrato)

```python
# src/reid/embeddings.py
def get_embedding(image) -> "np.ndarray":
    """Vector de embedding del rostro (DeepFace/ArcFace). Devuelve None si no detecta rostro."""

def build_gallery(gallery_dir: str) -> dict:
    """{identidad: [emb, emb, ...]} a partir de carpetas por persona."""

# src/reid/metrics.py
def evaluate_reid(query_set, gallery) -> dict:
    """Devuelve {'top1': float, 'top5': float, 'map': float}. mAP variante re-ID."""
```

---

## 3. Paso a paso

1. **`get_embedding`:** envolver `DeepFace.represent(img, model_name="ArcFace")`
   y devolver el vector como `np.ndarray`. Manejá el caso "no se detectó rostro"
   (devolvé `None` o lanzá excepción clara). ✍️ (por qué ArcFace y no Facenet/VGG-Face)

2. **`build_gallery`:** recorrer `data/gallery/<persona>/*.jpg`, generar embeddings
   y guardarlos cacheados (`.pkl` o dict) para no recalcular. **3–5 fotos por persona**,
   ángulos/iluminación variados.

3. **Métricas — ESTE ES EL PUNTO CRÍTICO de la fase.** La rúbrica pide "mAP variante
   correcta de re-ID" y en la defensa preguntan por qué difiere del mAP de detección.
   **No uses `average_precision_score` de forma ingenua.** El mAP de re-ID se calcula así:
   - Separás un **probe set** (consultas) de la **galería**. Cada identidad debe tener
     varias imágenes en la galería para que haya varios "relevantes" por query.
   - Para cada query: rankeás TODA la galería por distancia (menor = más parecido).
   - Calculás el **Average Precision sobre esa lista rankeada** (precisión acumulada en
     cada posición donde aparece un match correcto de la misma identidad).
   - **mAP = promedio de los AP de todas las queries.**
   - Top-1 = % de queries cuyo vecino más cercano es de la misma identidad.
     Top-k = % donde aparece un match correcto entre los k primeros.
   ✍️ Documentá la diferencia con el mAP de detección (detección promedia sobre
   IoU/clases vía área PR; re-ID promedia AP sobre listas rankeadas por query). Esto
   es respuesta directa de defensa.

4. **Visualización PCA/t-SNE** en `02a_reid_embeddings.ipynb`: proyectá todos los
   embeddings a 2-D y coloreá por identidad. Tiene que verse que cada persona forma
   su cluster. **Escribí una interpretación** debajo del gráfico (la rúbrica pide
   "con interpretación", no solo el dibujo). ✍️ PCA vs t-SNE: por qué usaste cuál.

5. **Logueá a WandB** las métricas de re-ID (top-1, top-k, mAP) usando
   `src/tracking/wandb_utils.py`. Esto cubre el hueco de "entrenamiento de re-ID en
   WandB": como usan DeepFace pre-entrenado y no entrenan, **al menos los resultados
   de evaluación tienen que quedar registrados** o pierden parte de la Fase 5.

---

## 4. Checklist de rúbrica (tu parte de los 15)

- [ ] Red de embeddings funcionando (DeepFace/ArcFace) — junto con la galería de Jose (5)
- [ ] Métricas top-1, top-k y **mAP variante re-ID** correctas (3)
- [ ] Visualización PCA/t-SNE **con interpretación** (3)

---

## 5. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase2_decisiones_leandro.md` (copiá `docs/PLANTILLA_decisiones.md`).
Registrá: ArcFace vs otros modelos, cómo implementaste el mAP de re-ID (¡con la fórmula!),
PCA vs t-SNE. Cada ✍️ = una entrada en la bitácora.

---

## 6. Coordinación con Jose

Pónganse de acuerdo en:
- (a) el formato exacto del embedding que devuelve `get_embedding` (vector 1-D np.ndarray)
- (b) la métrica de distancia (`coseno`, ver `src/config.REID_DISTANCE`)
- (c) quién genera `data/gallery/`

Compartan UN solo `requirements/fase2.txt`.

---

## 7. Cómo entregar

Rama `fase2-reid-leandro` → PR a `develop`.
