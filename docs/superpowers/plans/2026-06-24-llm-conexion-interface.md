# LLM Conexión e Interface — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar Claude API en tiempo de predicción para mostrar info del landmark en ES/EN/FR/IT, con fallback de 3 niveles (LLM → JSON file → datos estáticos embebidos). Corregir el bug de display en la UI.

**Architecture:** `TranslationService.get_landmark_translations()` implementa una cadena de fallback: (1) llamada en vivo a Claude API si ANTHROPIC_API_KEY está configurada, (2) lookup en `data/translations.json` si existe, (3) dict estático embebido en el código — siempre disponible. La UI formatea correctamente `nombre` + `descripcion` por idioma.

**Tech Stack:** Python 3.10+, `anthropic`, FastAPI, Gradio, pytest, unittest.mock

---

## Archivos

- **Modify:** `src/translation/translate.py` — fix FileNotFoundError + agregar `_STATIC_TRANSLATIONS` + live LLM method + fallback chain
- **Modify:** `ui/app.py` — fix bug `t.get('es', '—')` + display multilingual con nombre+descripcion
- **Create:** `tests/__init__.py`
- **Create:** `tests/translation/__init__.py`
- **Create:** `tests/translation/test_translate.py`

---

### Task 1: Tests para el fallback chain (TDD — escribe primero)

**Files:**
- Create: `tests/__init__.py` (vacío)
- Create: `tests/translation/__init__.py` (vacío)
- Create: `tests/translation/test_translate.py`

- [ ] **Step 1: Crear archivos `__init__.py`**

```
tests/__init__.py     (vacío)
tests/translation/__init__.py   (vacío)
```

- [ ] **Step 2: Escribir el test de datos estáticos**

```python
# tests/translation/test_translate.py
import json
import pytest
from unittest.mock import MagicMock
from src.translation.translate import TranslationService, _STATIC_TRANSLATIONS

EXPECTED_LANGS = ("es", "en", "fr", "it")
ALL_LANDMARKS = [
    "Cambodromo", "CatedralMunicipal", "Cristo", "DunasArena",
    "ParqueUrbano", "Plaza24", "Tahuichi", "Ventura",
]


class TestStaticTranslations:
    def test_all_landmarks_present(self):
        for lm in ALL_LANDMARKS:
            assert lm in _STATIC_TRANSLATIONS, f"{lm} missing from _STATIC_TRANSLATIONS"

    def test_all_languages_present(self):
        for lm in ALL_LANDMARKS:
            for lang in EXPECTED_LANGS:
                assert lang in _STATIC_TRANSLATIONS[lm], f"{lm}.{lang} missing"

    def test_nombre_and_descripcion_present(self):
        for lm in ALL_LANDMARKS:
            for lang in EXPECTED_LANGS:
                entry = _STATIC_TRANSLATIONS[lm][lang]
                assert "nombre" in entry and entry["nombre"]
                assert "descripcion" in entry and entry["descripcion"]


class TestTranslationServiceNoFile:
    def test_no_crash_when_json_missing(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        assert svc is not None

    def test_returns_static_fallback_when_no_json_no_llm(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        result = svc.get_landmark_translations("Cristo")
        for lang in EXPECTED_LANGS:
            assert lang in result
            assert "nombre" in result[lang]
            assert "descripcion" in result[lang]

    def test_all_landmarks_via_static_fallback(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        for lm in ALL_LANDMARKS:
            result = svc.get_landmark_translations(lm)
            for lang in EXPECTED_LANGS:
                assert lang in result


class TestTranslationServiceWithJsonFile:
    def test_uses_json_when_no_llm(self, tmp_path):
        json_data = {
            "Cristo": {
                "es": {"nombre": "Cristo ES JSON", "descripcion": "Desc ES"},
                "en": {"nombre": "Cristo EN JSON", "descripcion": "Desc EN"},
                "fr": {"nombre": "Cristo FR JSON", "descripcion": "Desc FR"},
                "it": {"nombre": "Cristo IT JSON", "descripcion": "Desc IT"},
            }
        }
        json_path = tmp_path / "translations.json"
        json_path.write_text(json.dumps(json_data), encoding="utf-8")
        svc = TranslationService(translations_path=str(json_path))
        result = svc.get_landmark_translations("Cristo")
        assert result["es"]["nombre"] == "Cristo ES JSON"

    def test_json_fallback_for_landmark_not_in_json_uses_static(self, tmp_path):
        json_data = {"Cristo": {"es": {"nombre": "x", "descripcion": "y"}, "en": {"nombre": "x", "descripcion": "y"}, "fr": {"nombre": "x", "descripcion": "y"}, "it": {"nombre": "x", "descripcion": "y"}}}
        json_path = tmp_path / "translations.json"
        json_path.write_text(json.dumps(json_data), encoding="utf-8")
        svc = TranslationService(translations_path=str(json_path))
        # Ventura is not in the JSON, should fall to static
        result = svc.get_landmark_translations("Ventura")
        expected = _STATIC_TRANSLATIONS["Ventura"]["es"]["nombre"]
        assert result["es"]["nombre"] == expected


class TestTranslationServiceLLM:
    def test_llm_result_used_when_client_available(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        llm_response = {
            "es": {"nombre": "Cristo LLM ES", "descripcion": "LLM Desc"},
            "en": {"nombre": "Cristo LLM EN", "descripcion": "LLM Desc"},
            "fr": {"nombre": "Cristo LLM FR", "descripcion": "LLM Desc"},
            "it": {"nombre": "Cristo LLM IT", "descripcion": "LLM Desc"},
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(llm_response))]
        mock_client.messages.create.return_value = mock_response
        svc._anthropic_client = mock_client

        result = svc.get_landmark_translations("Cristo")
        assert result["es"]["nombre"] == "Cristo LLM ES"

    def test_falls_back_to_static_when_llm_raises(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Network error")
        svc._anthropic_client = mock_client

        result = svc.get_landmark_translations("Cristo")
        expected = _STATIC_TRANSLATIONS["Cristo"]["es"]["nombre"]
        assert result["es"]["nombre"] == expected

    def test_falls_back_when_llm_returns_invalid_json(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json at all")]
        mock_client.messages.create.return_value = mock_response
        svc._anthropic_client = mock_client

        result = svc.get_landmark_translations("Ventura")
        assert "es" in result and "nombre" in result["es"]

    def test_unknown_landmark_returns_generic_structure(self, tmp_path):
        svc = TranslationService(translations_path=str(tmp_path / "no_file.json"))
        result = svc.get_landmark_translations("LugarDesconocido")
        for lang in EXPECTED_LANGS:
            assert lang in result
            assert "nombre" in result[lang]
            assert "descripcion" in result[lang]
```

- [ ] **Step 3: Correr los tests — deben FALLAR (TranslationService no tiene `_STATIC_TRANSLATIONS`)**

```
cd D:\deepLearning\RutaCamba
pytest tests/translation/test_translate.py -v
```

Expected: `ImportError: cannot import name '_STATIC_TRANSLATIONS'` o errores de FileNotFoundError.

- [ ] **Step 4: Commit del test rojo**

```bash
git add tests/
git commit -m "test: tests TDD para fallback chain de TranslationService"
```

---

### Task 2: Implementar `_STATIC_TRANSLATIONS` y arreglar `__init__`

**Files:**
- Modify: `src/translation/translate.py`

- [ ] **Step 1: Agregar `_STATIC_TRANSLATIONS` antes de la clase**

Insertar este dict en `translate.py` después de `_LANGDETECT_TO_NLLB`:

```python
_STATIC_TRANSLATIONS: dict = {
    "Cambodromo": {
        "es": {
            "nombre": "Cambódromo de Santa Cruz de la Sierra",
            "descripcion": "Recinto construido para los desfiles de comparsas del Carnaval Cruceño, uno de los carnavales más importantes de Bolivia. Espacio público amplio usado también para otros eventos masivos fuera de la temporada de carnaval.",
        },
        "en": {
            "nombre": "Cambódromo of Santa Cruz de la Sierra",
            "descripcion": "A venue built for the carnival troupe parades of the Santa Cruz Carnival, one of Bolivia's most important carnivals. A large public space also used for other major city events outside carnival season.",
        },
        "fr": {
            "nombre": "Cambódromo de Santa Cruz de la Sierra",
            "descripcion": "Enceinte construite pour les défilés de troupes du Carnaval de Santa Cruz, l'un des carnavals les plus importants de Bolivie. Grand espace public utilisé aussi pour d'autres événements majeurs hors saison.",
        },
        "it": {
            "nombre": "Cambódromo di Santa Cruz de la Sierra",
            "descripcion": "Struttura costruita per le sfilate di comparsas del Carnevale di Santa Cruz, uno dei carnevali più importanti della Bolivia. Ampio spazio pubblico utilizzato anche per altri grandi eventi cittadini fuori stagione.",
        },
    },
    "CatedralMunicipal": {
        "es": {
            "nombre": "Catedral Basílica Menor San Lorenzo",
            "descripcion": "Templo católico ubicado en la Plaza 24 de Septiembre, corazón histórico de Santa Cruz de la Sierra. Es la catedral más importante del departamento y uno de los edificios coloniales más representativos de la ciudad.",
        },
        "en": {
            "nombre": "Cathedral Basilica of San Lorenzo",
            "descripcion": "A Catholic church on Plaza 24 de Septiembre, the historic heart of Santa Cruz de la Sierra. The most important cathedral in the department and one of the city's most representative colonial buildings.",
        },
        "fr": {
            "nombre": "Cathédrale Basilique de San Lorenzo",
            "descripcion": "Temple catholique situé sur la Plaza 24 de Septiembre, cœur historique de Santa Cruz de la Sierra. La cathédrale la plus importante du département et l'un des édifices coloniaux les plus représentatifs de la ville.",
        },
        "it": {
            "nombre": "Cattedrale Basilica di San Lorenzo",
            "descripcion": "Tempio cattolico situato in Plaza 24 de Septiembre, cuore storico di Santa Cruz de la Sierra. La cattedrale più importante del dipartimento e uno degli edifici coloniali più rappresentativi della città.",
        },
    },
    "Cristo": {
        "es": {
            "nombre": "Cristo Redentor de Santa Cruz",
            "descripcion": "Estatua monumental del Cristo Redentor en Santa Cruz de la Sierra, Bolivia. Uno de los íconos más reconocidos de la ciudad, en un punto elevado con vistas panorámicas sobre la urbe y sus alrededores.",
        },
        "en": {
            "nombre": "Christ the Redeemer of Santa Cruz",
            "descripcion": "Monumental statue of Christ the Redeemer in Santa Cruz de la Sierra, Bolivia. One of the city's most recognized icons, situated at an elevated point with panoramic views over the city and surroundings.",
        },
        "fr": {
            "nombre": "Christ Rédempteur de Santa Cruz",
            "descripcion": "Statue monumentale du Christ Rédempteur à Santa Cruz de la Sierra, Bolivie. L'un des symboles les plus reconnus de la ville, perché en hauteur avec des vues panoramiques sur la cité.",
        },
        "it": {
            "nombre": "Cristo Redentore di Santa Cruz",
            "descripcion": "Statua monumentale del Cristo Redentore a Santa Cruz de la Sierra, Bolivia. Uno dei simboli più riconoscibili della città, in un punto elevato con viste panoramiche sulla metropoli.",
        },
    },
    "DunasArena": {
        "es": {
            "nombre": "Lomas de Arena",
            "descripcion": "Parque regional con dunas de arena y lagunas estacionales al sur de Santa Cruz de la Sierra. Ecosistema único de Bolivia donde el desierto y la laguna conviven. Ideal para sandboarding y fotografía de naturaleza.",
        },
        "en": {
            "nombre": "Lomas de Arena (Sand Dunes)",
            "descripcion": "Regional park with sand dunes and seasonal lagoons south of Santa Cruz de la Sierra. A unique Bolivian ecosystem where desert and lagoon coexist. Ideal for sandboarding and nature photography.",
        },
        "fr": {
            "nombre": "Lomas de Arena (Dunes de Sable)",
            "descripcion": "Parc régional avec des dunes de sable et des lagons saisonniers au sud de Santa Cruz de la Sierra. Écosystème unique en Bolivie, idéal pour le sandboard et la photographie de nature.",
        },
        "it": {
            "nombre": "Lomas de Arena (Dune di Sabbia)",
            "descripcion": "Parco regionale con dune di sabbia e lagune stagionali a sud di Santa Cruz de la Sierra. Ecosistema unico della Bolivia, ideale per il sandboarding e la fotografia naturalistica.",
        },
    },
    "ParqueUrbano": {
        "es": {
            "nombre": "Parque Urbano",
            "descripcion": "Parque recreativo de gran extensión dentro de Santa Cruz de la Sierra, con áreas verdes, senderos y espacios de esparcimiento. Punto de encuentro popular para actividades al aire libre.",
        },
        "en": {
            "nombre": "Parque Urbano (Urban Park)",
            "descripcion": "Large recreational park within Santa Cruz de la Sierra, with green areas, trails and recreation spaces. A popular meeting point for outdoor activities among the city's residents.",
        },
        "fr": {
            "nombre": "Parque Urbano (Parc Urbain)",
            "descripcion": "Grand parc récréatif au cœur de Santa Cruz de la Sierra, avec espaces verts, sentiers et aires de loisirs. Lieu de rencontre populaire pour les activités de plein air.",
        },
        "it": {
            "nombre": "Parque Urbano (Parco Urbano)",
            "descripcion": "Ampio parco ricreativo nella città di Santa Cruz de la Sierra, con aree verdi, sentieri e spazi ricreativi. Punto di incontro popolare per le attività all'aperto.",
        },
    },
    "Plaza24": {
        "es": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": "Plaza principal y centro histórico de Santa Cruz de la Sierra. Rodeada de edificios coloniales, la Catedral y sedes de gobierno, es el punto de encuentro social más tradicional de la ciudad.",
        },
        "en": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": "Main square and historic center of Santa Cruz de la Sierra. Surrounded by colonial buildings, the Cathedral and government offices, it is the city's most traditional social gathering point.",
        },
        "fr": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": "Place principale et centre historique de Santa Cruz de la Sierra. Entourée d'édifices coloniaux, de la Cathédrale et des sièges gouvernementaux, c'est le point de rencontre social le plus traditionnel de la ville.",
        },
        "it": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": "Piazza principale e centro storico di Santa Cruz de la Sierra. Circondata da edifici coloniali, la Cattedrale e sedi governative, è il punto di incontro sociale più tradizionale della città.",
        },
    },
    "Tahuichi": {
        "es": {
            "nombre": "Estadio Ramón Tahuichi Aguilera",
            "descripcion": "Estadio de fútbol principal de Santa Cruz de la Sierra, sede de partidos profesionales y asociado a la célebre academia de fútbol formativo Tahuichi.",
        },
        "en": {
            "nombre": "Ramón Tahuichi Aguilera Stadium",
            "descripcion": "Main football stadium of Santa Cruz de la Sierra, home to professional matches and associated with the famous Tahuichi youth football academy.",
        },
        "fr": {
            "nombre": "Stade Ramón Tahuichi Aguilera",
            "descripcion": "Principal stade de football de Santa Cruz de la Sierra, accueillant des matchs professionnels et associé à la célèbre académie de football jeunesse Tahuichi.",
        },
        "it": {
            "nombre": "Stadio Ramón Tahuichi Aguilera",
            "descripcion": "Principale stadio di calcio di Santa Cruz de la Sierra, sede di partite professionistiche e associato alla famosa accademia di calcio giovanile Tahuichi.",
        },
    },
    "Ventura": {
        "es": {
            "nombre": "Ventura Mall",
            "descripcion": "Centro comercial moderno de Santa Cruz de la Sierra, con tiendas, restaurantes y espacios de entretenimiento. Uno de los destinos de compras y ocio más visitados de la ciudad.",
        },
        "en": {
            "nombre": "Ventura Mall",
            "descripcion": "Modern shopping center in Santa Cruz de la Sierra, with shops, restaurants and entertainment spaces. One of the most visited shopping and leisure destinations in the city.",
        },
        "fr": {
            "nombre": "Ventura Mall",
            "descripcion": "Centre commercial moderne de Santa Cruz de la Sierra, avec boutiques, restaurants et espaces de divertissement. L'une des destinations shopping et loisirs les plus fréquentées de la ville.",
        },
        "it": {
            "nombre": "Ventura Mall",
            "descripcion": "Centro commerciale moderno di Santa Cruz de la Sierra, con negozi, ristoranti e spazi di intrattenimento. Una delle destinazioni shopping e svago più visitate della città.",
        },
    },
}
```

- [ ] **Step 2: Reemplazar `__init__` para que no crashee si falta el JSON**

Reemplazar el `__init__` completo de `TranslationService` con:

```python
def __init__(self, translations_path: str = "data/translations.json"):
    self._translations: dict = {}
    if os.path.exists(translations_path):
        with open(translations_path, "r", encoding="utf-8") as f:
            self._translations = json.load(f)
        logger.info(
            f"TranslationService: {len(self._translations)} landmarks desde {translations_path}"
        )
    else:
        logger.warning(
            f"No se encontró {translations_path}. "
            "Usando datos estáticos como fallback. "
            "Para generar el JSON: python scripts/generate_translations.py"
        )

    self._anthropic_client = None
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("TranslationService: cliente Anthropic inicializado.")
        else:
            logger.warning("ANTHROPIC_API_KEY no configurada. Usando JSON o datos estáticos.")
    except ImportError:
        logger.warning("anthropic no instalado. pip install anthropic")

    self._nllb_pipeline = None
```

- [ ] **Step 3: Correr los tests — algunos deben pasar ahora**

```
pytest tests/translation/test_translate.py -v
```

Expected: `TestStaticTranslations` y `TestTranslationServiceNoFile` pasan. Los de LLM todavía fallan.

---

### Task 3: Agregar método LLM en vivo + cadena de fallback

**Files:**
- Modify: `src/translation/translate.py`

- [ ] **Step 1: Agregar `_get_info_from_llm()` como método privado**

Insertar antes de `_detect_language()`:

```python
def _get_info_from_llm(self, landmark_id: str) -> Optional[dict]:
    """Genera info del landmark en ES/EN/FR/IT con Claude API. Devuelve None si falla."""
    if self._anthropic_client is None:
        return None

    display_name = (
        _STATIC_TRANSLATIONS.get(landmark_id, {})
        .get("es", {})
        .get("nombre", landmark_id)
    )

    prompt = (
        "Eres un asistente de turismo para Santa Cruz de la Sierra, Bolivia. "
        f"El modelo de visión identificó este lugar: {display_name}.\n\n"
        "Generá información turística atractiva en 4 idiomas. "
        "Respondé SOLO con JSON válido con esta estructura exacta:\n"
        '{\n'
        '  "es": {"nombre": "...", "descripcion": "..."},\n'
        '  "en": {"nombre": "...", "descripcion": "..."},\n'
        '  "fr": {"nombre": "...", "descripcion": "..."},\n'
        '  "it": {"nombre": "...", "descripcion": "..."}\n'
        '}\n\n'
        "Cada descripción: máximo 80 palabras. Sé preciso y atractivo para turistas."
    )

    try:
        response = self._anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Limpiar bloques de código markdown si los hay
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        result = json.loads(raw)

        if all(
            lang in result
            and isinstance(result[lang], dict)
            and "nombre" in result[lang]
            and "descripcion" in result[lang]
            for lang in ("es", "en", "fr", "it")
        ):
            logger.info(f"LLM generó info para '{landmark_id}'.")
            return result

        logger.warning(f"LLM devolvió estructura inválida para '{landmark_id}'.")
        return None

    except Exception as e:
        logger.warning(f"LLM falló para '{landmark_id}', usando fallback: {e}")
        return None
```

- [ ] **Step 2: Reemplazar `get_landmark_translations()` con la cadena de 3 niveles**

```python
def get_landmark_translations(self, landmark_id: str) -> dict:
    """Devuelve info del landmark en 4 idiomas (ES/EN/FR/IT).

    Cadena de fallback:
        1. Claude API en vivo — si ANTHROPIC_API_KEY está configurada
        2. data/translations.json — si existe y contiene el landmark
        3. _STATIC_TRANSLATIONS — siempre disponible para los 8 landmarks
    """
    # Nivel 1: LLM en vivo
    if self._anthropic_client is not None:
        result = self._get_info_from_llm(landmark_id)
        if result is not None:
            return result

    # Nivel 2: JSON pre-generado
    if landmark_id in self._translations:
        return self._translations[landmark_id]

    # Nivel 3: datos estáticos embebidos
    static = _STATIC_TRANSLATIONS.get(landmark_id)
    if static:
        logger.info(f"Usando datos estáticos para '{landmark_id}'.")
        return static

    logger.warning(f"landmark_id '{landmark_id}' desconocido.")
    return {
        lang: {"nombre": landmark_id, "descripcion": "Información no disponible."}
        for lang in ("es", "en", "fr", "it")
    }
```

- [ ] **Step 3: Correr los tests — todos deben pasar**

```
pytest tests/translation/test_translate.py -v
```

Expected: todos los tests en verde.

- [ ] **Step 4: Commit**

```bash
git add src/translation/translate.py tests/
git commit -m "feat: LLM en vivo + fallback 3 niveles en TranslationService"
```

---

### Task 4: Fix UI display

**Files:**
- Modify: `ui/app.py`

- [ ] **Step 1: Agregar función helper `_format_translations()` antes de `step_predict()`**

```python
def _format_translations(landmark_id: str, translations: dict) -> str:
    """Formatea la info multilingüe del landmark como markdown."""
    title = landmark_id.replace("_", " ").title()
    lang_labels = {
        "es": "Espanol",
        "en": "English",
        "fr": "Francais",
        "it": "Italiano",
    }
    sections = [f"## {title}\n"]
    for lang_code, lang_label in lang_labels.items():
        data = translations.get(lang_code, {})
        if isinstance(data, dict) and data:
            nombre = data.get("nombre", "—")
            descripcion = data.get("descripcion", "—")
            sections.append(f"### {lang_label}\n\n**{nombre}**\n\n{descripcion}")
        else:
            sections.append(f"### {lang_label}\n\n—")
    return "\n\n---\n\n".join(sections)
```

- [ ] **Step 2: Reemplazar el bloque de construcción de `info` en `step_predict()`**

Cambiar la línea:
```python
info = (
    f"### {data['landmark_id'].replace('_', ' ').title()}\n\n"
    f"**ES:** {t.get('es', '—')}\n\n"
    f"**EN:** {t.get('en', '—')}\n\n"
    f"**FR:** {t.get('fr', '—')}\n\n"
    f"**IT:** {t.get('it', '—')}"
)
```

Por:
```python
info = _format_translations(data["landmark_id"], data["translations"])
```

- [ ] **Step 3: Commit**

```bash
git add ui/app.py
git commit -m "fix: display multilingüe en UI muestra nombre+descripcion correctamente"
```

---

### Task 5: Generar `data/translations.json` (requiere API key)

> **PAUSA:** Pedir la ANTHROPIC_API_KEY al usuario antes de este paso.

- [ ] **Step 1: Crear `.env` con la API key**

```
ANTHROPIC_API_KEY=<clave-proporcionada-por-el-usuario>
```

- [ ] **Step 2: Correr el script de generación**

```bash
python scripts/generate_translations.py
```

Expected: `data/translations.json` generado con los 8 landmarks × 4 idiomas.

- [ ] **Step 3: Revisar el JSON generado**

```bash
python -c "import json; data=json.load(open('data/translations.json')); print(list(data.keys()))"
```

Expected: `['Cambodromo', 'CatedralMunicipal', 'Cristo', 'DunasArena', 'ParqueUrbano', 'Plaza24', 'Tahuichi', 'Ventura']`

- [ ] **Step 4: Commitear el JSON**

```bash
git add data/translations.json
git commit -m "data: agregar translations.json pre-generado con Claude API"
```

---

### Task 6: Push y PR

- [ ] **Step 1: Push de la rama**

```bash
git push -u origin LLM-conexion-e-interface
```

- [ ] **Step 2: Crear PR**

```bash
gh pr create --title "feat: LLM conexión e interface multilingüe" --body "..."
```
