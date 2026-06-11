# Fase 4 — Traducción multilingüe con LLM · Jose Alfredo

**Peso:** 5 pts · **Carpeta:** `src/translation/` + `scripts/generate_translations.py`
+ `data/translations.json`

> Tres criterios independientes: (1) traducir la salida a EN/FR/IT, (2) normalizar
> consultas que lleguen en otro idioma, (3) fallback claro si el LLM falla.
> (Recordá: también tenés la Fase 2-B. Una a la vez.)

---

## 1. Archivos que te pertenecen (solo estos)

| Archivo | Qué va adentro |
|---------|----------------|
| `scripts/generate_translations.py` | script OFFLINE: genera `translations.json` una vez |
| `src/translation/__init__.py` | exporta `TranslationService` |
| `src/translation/translate.py` | `TranslationService` (lo usa la API) |
| `data/translations.json` | traducciones pre-generadas y curadas |
| `requirements/fase4.txt` | anthropic, langdetect, transformers, torch, sentencepiece |

---

## 2. Lo que tu código DEBE exponer (contrato)

```python
# src/translation/translate.py
class TranslationService:
    def __init__(self, translations_path: str = "data/translations.json"): ...

    def get_landmark_translations(self, landmark_id: str) -> dict:
        # {es, en, fr, it} — lookup O(1), sin llamadas a red

    def normalize_input(self, query: str) -> dict:
        # {original, detected_lang, normalized, method: "llm"|"nllb"|"passthrough"}
```

Nicole (Fase 6) llama exactamente a estas dos funciones desde la API.

---

## 3. Paso a paso

### Criterio 1 — Traducción de salida (2 pts)

1. En `generate_translations.py` definí el catálogo de los **8 landmarks** (mismos
   IDs que `config.LANDMARK_CLASSES`) con nombre + descripción curada en español.
   ⚠️ Los IDs de landmarks son exactamente los de `src/config.LANDMARK_CLASSES` — usá esos.

2. Llamá al LLM (Claude API) con retry + backoff para traducir cada uno a EN/FR/IT y
   guardá `data/translations.json`. **Revisá las traducciones a mano** antes de la
   demo y versionalo en git.

3. `get_landmark_translations` hace lookup O(1) en el JSON cargado en memoria.
   ✍️ por qué pre-generar offline y no llamar al LLM en cada request (latencia/costo).

### Criterio 2 — Normalización de entrada (2 pts)

4. `normalize_input`: detectá idioma con `langdetect` (local, no falla). Si ya es
   español → passthrough. Si no → pasá la consulta por el LLM para entender la
   intención y devolver el nombre del lugar en español. ✍️ por qué LLM y no un
   traductor literal (entiende intención, no solo palabras).

### Criterio 3 — Fallback (1 pt)

5. Si el LLM falla (timeout/sin red/error), caé a **NLLB-200 local** (corre en CPU,
   sin internet). Devolvé `method: "llm" | "nllb" | "passthrough"` para que se vea
   qué capa respondió. ✍️ por qué NLLB-200 y no MarianMT / Google Translate.
   **El sistema nunca debe caerse por el LLM.**

---

## 4. Checklist de rúbrica

- [ ] Traducción correcta a EN/FR/IT mediante LLM (2)
- [ ] Normalización de entrada en idioma inesperado (2)
- [ ] Manejo de error del LLM con fallback claro (1)

---

## 5. Documentá tus decisiones (OBLIGATORIO)

Creá `docs/decisiones/fase4_decisiones_jose.md` (copiá `docs/PLANTILLA_decisiones.md`).
Cada ✍️ es una entrada. Registrá al menos:

- Por qué pre-generar offline y no LLM en cada request
- Por qué LLM para normalización de entrada y no traductor directo
- Por qué NLLB-200 como fallback y no MarianMT / Google Translate
- Cómo manejas errores de red (retry/backoff en el script de generación)

---

## 6. Cómo entregar

Rama `fase4-llm-jose` → PR a `develop`.
Avisá que `TranslationService` cumple el contrato y que `data/translations.json`
ya está curado, para que Nicole lo conecte.
