# Fase 6 — Despliegue (API + interfaz) · Nicole Lozada

**Peso:** 5 pts · **Carpeta:** `api/` + `ui/` + `scripts/download_models.py`

> Vos conectás TODO. La gracia del diseño del proyecto es que, si cada fase respetó
> su contrato (`docs/interfaces/contratos.md`), tu API solo "enchufa" módulos. Podés
> empezar a programar contra stubs antes de que las otras fases estén 100% listas.

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `api/__init__.py` | init del módulo API |
| `api/main.py` | FastAPI: `/verify`, `/predict`, `/normalize` |
| `ui/app.py` | Gradio que consume la API |
| `scripts/download_models.py` | baja los `.pt` desde S3 (no se suben al repo) |
| `requirements/fase6.txt` | fastapi, uvicorn[standard], python-multipart, gradio, requests, boto3, python-dotenv |

Importás de todas las demás fases (no las edites):
- `reid.access.verify_identity`
- `landmarks.predictor.LandmarkPredictor`
- `translation.translate.TranslationService`

---

## 2. Paso a paso

1. **Carga de modelos en el startup** (lifespan de FastAPI), UNA sola vez:
   `LandmarkPredictor`, `TranslationService`, y la galería de Re-ID. La API
   **nunca re-entrena**, solo infiere (requisito explícito). ✍️

2. **Endpoints:**
   - `POST /verify`: recibe identidad declarada + selfie → llama `verify_identity`
     → si `access=True` devuelve un **token de sesión** (dict en memoria
     `{token: identidad, expiración}`; no hace falta JWT ni DB para la demo). ✍️
   - `POST /predict`: exige token válido (si no, **401/403**) → `predictor.predict`
     (top-k + probabilidades) → `get_landmark_translations` → devuelve landmark +
     top_k + traducciones {es,en,fr,it}.
   - `POST /normalize`: `normalize_input(query)` para consultas en idioma inesperado.

3. **Interfaz Gradio** (`ui/app.py`): `gr.Blocks` en **dos pasos** — primero subir
   selfie + declarar identidad (verificación), y solo si pasa, habilitar la pestaña
   de subir foto del lugar y mostrar el **top-k con probabilidades** (`gr.Label`) +
   las traducciones. La UI consume la API con `requests`, **nunca carga modelos
   directamente** (mantiene la separación que exige el enunciado). ✍️ Gradio vs
   Streamlit: por qué Gradio (menos código para este flujo).

4. **`scripts/download_models.py`:** baja los `.pt` desde S3 con boto3 (cumple "no
   subir modelos al repo").

5. **Config:** `.env` con `python-dotenv` para la clave del LLM; documentá variables
   y puertos (API 8000 / UI 7860) — esto se lo pasás al README en la Fase 7.

---

## 3. Checklist de rúbrica

- [ ] API con `/verify`, `/predict` (condicionado a token) y traducción; consume
      TorchScript sin re-entrenar (3)
- [ ] Interfaz Gradio que consume la API y muestra el flujo end-to-end (top-k +
      traducciones) (2)

> Nota técnica: el `/verify` usa DeepFace (TensorFlow) y el `/predict` usa TorchScript
> (PyTorch). Vas a tener PyTorch + TensorFlow + transformers en el mismo proceso.
> **Probá el arranque temprano** para que no choquen dependencias el día de la demo. ✍️

---

## 4. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase6_decisiones_nicole.md` (copiá `docs/PLANTILLA_decisiones.md`).
Registrá al menos:
- Por qué cargar modelos en startup y no en cada request
- Por qué token en memoria y no JWT/DB
- Por qué Gradio y no Streamlit
- Cómo resolviste la coexistencia PyTorch + TensorFlow en el mismo proceso

Cada ✍️ = una entrada en la bitácora.

---

## 5. Cómo entregar

Rama `fase6-deploy-nicole` → PR a `develop`.
Esta es la fase de integración: cuando mergees, probá el flujo end-to-end completo.
