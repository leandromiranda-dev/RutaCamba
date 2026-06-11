# Fase 2 — Re-ID · Parte B (galería, ranking, umbral y acceso) · Jose Alfredo

**Peso:** 15 pts (compartidos con Leandro) · **Carpeta:** `src/reid/gallery.py`,
`src/reid/ranking.py`, `src/reid/access.py`, `notebooks/02b_reid_ranking_metrics.ipynb`

> Vos hacés la parte de **decisión/puerta de entrada**: dada una selfie y una
> identidad declarada, decidir si se concede acceso. Leandro te pasa los embeddings;
> vos hacés el ranking por distancia, definís el umbral JUSTIFICADO y la lógica de
> acceso. `verify_identity` (tuya) es lo que va a llamar la API de Nicole.
> (Ojo: también tenés la Fase 4. Hacé una a la vez.)

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `src/reid/gallery.py` | cargar/guardar la galería de identidades autorizadas |
| `src/reid/ranking.py` | distancia (coseno) query↔galería y ranking ordenado |
| `src/reid/access.py` | `verify_identity(...)` ← lo consume la API (Fase 6) |
| `notebooks/02b_reid_ranking_metrics.ipynb` | demo de ranking + ajuste del umbral |

No toques `embeddings.py` ni `metrics.py` (son de Leandro). Usalos importándolos.
No toques archivos de otras fases.

---

## 2. Lo que tu código DEBE exponer (contrato — clave para la API)

```python
# src/reid/access.py
def verify_identity(declared_id: str, probe_image) -> dict:
    return {
        "access": bool,            # True solo si top1 == declared_id Y distancia < umbral
        "distance": float,
        "top1_identity": str,
        "topk": [(identidad, distancia), ...],
    }
```

Nicole (Fase 6) llama exactamente a esta función desde el endpoint `/verify`.
Si cambiás la firma, avisá.

---

## 3. Paso a paso

1. **`gallery.py`:** función para cargar la galería cacheada que arma Leandro
   (`build_gallery`) o levantar los embeddings desde `.pkl`. No recalcules en cada
   request.

2. **`ranking.py`:** dado el embedding de la selfie (probe), calculá la **distancia
   coseno** contra cada identidad de la galería (si una identidad tiene varias fotos,
   usá la mínima o el promedio — decidí y justificá ✍️) y devolvé el ranking ordenado
   de menor a mayor distancia. El primero es el top-1.

3. **Umbral JUSTIFICADO — punto que la rúbrica exige (4 pts).** No dejes el `0.65`
   a dedo de `config.py`. En `02b_..._metrics.ipynb`:
   - Generá pares **mismas-personas** (distancias intra-identidad) y
     **distintas-personas** (inter-identidad).
   - Graficá ambas distribuciones; el umbral va donde mejor las separa.
   - Idealmente sacá la curva ROC y elegí el punto de **EER** (equal error rate) o el
     que maximiza accuracy de verificación. Ese número reemplaza a `REID_THRESHOLD`.
   ✍️ Documentá: "elegí umbral = X porque a ese valor el EER es Y / separa las
   distribuciones así". Con ArcFace+coseno el umbral suele rondar 0.6–0.7, NO 0.5.

4. **`access.py` → `verify_identity`:** genera el embedding de la selfie (usando
   `embeddings.get_embedding`), rankea (usando `ranking.py`), y concede acceso
   **solo si** el top-1 coincide con `declared_id` **y** la distancia es menor al
   umbral. Devolvé el dict del contrato. Manejá "no se detectó rostro" → access=False
   con mensaje claro.

5. **Demo de aceptar/rechazar:** mostrá en el notebook un caso que ACEPTA y uno que
   RECHAZA (misma persona vs impostor), para la defensa y el video.

---

## 4. Checklist de rúbrica (tu parte de los 15)

- [ ] Galería + ranking por distancia correctamente implementado (5, junto con Leandro)
- [ ] Lógica de control de acceso con **umbral justificado** (acepta/rechaza) (4)

---

## 5. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase2_decisiones_jose.md` (copiá `docs/PLANTILLA_decisiones.md`).
Registrá: distancia coseno vs euclidiana, mín vs promedio cuando hay varias fotos
por identidad, y sobre todo **cómo y por qué elegiste el umbral** (con el dato de
ROC/EER). Cada ✍️ = una entrada.

---

## 6. Coordinación con Leandro

Acordá el formato del embedding y la métrica de distancia (ver `config.REID_DISTANCE`).
Un solo `requirements/fase2.txt` entre los dos.

---

## 7. Entregar

Rama `fase2-reid-jose` → PR a `develop`.
Avisá que `verify_identity` ya cumple el contrato para que Nicole conecte `/verify`.
