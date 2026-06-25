"""translate.py — Servicio de traducción multilingüe con LLM + fallback.

Jose (Fase 4): implementa TranslationService.

CONTRATO (no cambiar las firmas — Nicole las usa desde la API):
    class TranslationService:
        def get_landmark_translations(self, landmark_id: str) -> dict
        def normalize_input(self, query: str) -> dict
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Modelo LLM vigente del proyecto (único lugar de verdad) servido vía OpenRouter.
# El equipo migró de Anthropic a OpenRouter + Gemini por costo/disponibilidad.
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"

# Idiomas con traducciones pre-generadas (lookup O(1) offline).
_OFFLINE_LANGUAGES = ("es", "en", "fr", "it")

# Nombres legibles de idioma para los prompts del LLM (clave = código ISO 639-1).
_LANGUAGE_DISPLAY = {
    "es": "español",
    "en": "inglés",
    "fr": "francés",
    "it": "italiano",
    "pt": "portugués",
    "de": "alemán",
    "ja": "japonés",
    "zh": "chino",
    "ko": "coreano",
    "ru": "ruso",
    "ar": "árabe",
}

# Mapeo de códigos ISO 639-1 de langdetect → códigos de idioma NLLB-200
_LANGDETECT_TO_NLLB = {
    "en": "eng_Latn",
    "fr": "fra_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "de": "deu_Latn",
    "ja": "jpn_Jpan",
    "zh-cn": "zho_Hans",
    "zh-tw": "zho_Hant",
    "ko": "kor_Hang",
    "ru": "rus_Cyrl",
    "ar": "arb_Arab",
}

# Traducciones estáticas embebidas — fallback garantizado sin red ni archivos.
# Nivel 3 de la cadena: LLM en vivo → JSON pre-generado → este dict.
_STATIC_TRANSLATIONS: dict = {
    "Cambodromo": {
        "es": {
            "nombre": "Cambódromo de Santa Cruz de la Sierra",
            "descripcion": (
                "Recinto construido para los desfiles de comparsas del Carnaval Cruceño, "
                "uno de los carnavales más importantes de Bolivia. Espacio público amplio "
                "usado también para otros eventos masivos fuera de la temporada de carnaval."
            ),
        },
        "en": {
            "nombre": "Cambódromo of Santa Cruz de la Sierra",
            "descripcion": (
                "A venue built for the carnival troupe parades of the Santa Cruz Carnival, "
                "one of Bolivia's most important carnivals. A large public space also used "
                "for other major city events outside carnival season."
            ),
        },
        "fr": {
            "nombre": "Cambódromo de Santa Cruz de la Sierra",
            "descripcion": (
                "Enceinte construite pour les défilés de troupes du Carnaval de Santa Cruz, "
                "l'un des carnavals les plus importants de Bolivie. Grand espace public "
                "utilisé aussi pour d'autres événements majeurs hors saison."
            ),
        },
        "it": {
            "nombre": "Cambódromo di Santa Cruz de la Sierra",
            "descripcion": (
                "Struttura costruita per le sfilate di comparsas del Carnevale di Santa Cruz, "
                "uno dei carnevali più importanti della Bolivia. Ampio spazio pubblico "
                "utilizzato anche per altri grandi eventi cittadini fuori stagione."
            ),
        },
    },
    "CatedralMunicipal": {
        "es": {
            "nombre": "Catedral Basílica Menor San Lorenzo",
            "descripcion": (
                "Templo católico ubicado en la Plaza 24 de Septiembre, corazón histórico "
                "de Santa Cruz de la Sierra. Es la catedral más importante del departamento "
                "y uno de los edificios coloniales más representativos de la ciudad."
            ),
        },
        "en": {
            "nombre": "Cathedral Basilica of San Lorenzo",
            "descripcion": (
                "A Catholic church on Plaza 24 de Septiembre, the historic heart of "
                "Santa Cruz de la Sierra. The most important cathedral in the department "
                "and one of the city's most representative colonial buildings."
            ),
        },
        "fr": {
            "nombre": "Cathédrale Basilique de San Lorenzo",
            "descripcion": (
                "Temple catholique situé sur la Plaza 24 de Septiembre, cœur historique "
                "de Santa Cruz de la Sierra. La cathédrale la plus importante du département "
                "et l'un des édifices coloniaux les plus représentatifs de la ville."
            ),
        },
        "it": {
            "nombre": "Cattedrale Basilica di San Lorenzo",
            "descripcion": (
                "Tempio cattolico situato in Plaza 24 de Septiembre, cuore storico di "
                "Santa Cruz de la Sierra. La cattedrale più importante del dipartimento "
                "e uno degli edifici coloniali più rappresentativi della città."
            ),
        },
    },
    "Cristo": {
        "es": {
            "nombre": "Cristo Redentor de Santa Cruz",
            "descripcion": (
                "Estatua monumental del Cristo Redentor en Santa Cruz de la Sierra, Bolivia. "
                "Uno de los íconos más reconocidos de la ciudad, en un punto elevado con "
                "vistas panorámicas sobre la urbe y sus alrededores."
            ),
        },
        "en": {
            "nombre": "Christ the Redeemer of Santa Cruz",
            "descripcion": (
                "Monumental statue of Christ the Redeemer in Santa Cruz de la Sierra, Bolivia. "
                "One of the city's most recognized icons, situated at an elevated point "
                "with panoramic views over the city and surroundings."
            ),
        },
        "fr": {
            "nombre": "Christ Rédempteur de Santa Cruz",
            "descripcion": (
                "Statue monumentale du Christ Rédempteur à Santa Cruz de la Sierra, Bolivie. "
                "L'un des symboles les plus reconnus de la ville, perché en hauteur "
                "avec des vues panoramiques sur la cité et ses environs."
            ),
        },
        "it": {
            "nombre": "Cristo Redentore di Santa Cruz",
            "descripcion": (
                "Statua monumentale del Cristo Redentore a Santa Cruz de la Sierra, Bolivia. "
                "Uno dei simboli più riconoscibili della città, in un punto elevato "
                "con viste panoramiche sulla metropoli e dintorni."
            ),
        },
    },
    "DunasArena": {
        "es": {
            "nombre": "Lomas de Arena",
            "descripcion": (
                "Parque regional con dunas de arena y lagunas estacionales al sur de "
                "Santa Cruz de la Sierra. Ecosistema único de Bolivia donde el desierto "
                "y la laguna conviven. Ideal para sandboarding y fotografía de naturaleza."
            ),
        },
        "en": {
            "nombre": "Lomas de Arena (Sand Dunes)",
            "descripcion": (
                "Regional park with sand dunes and seasonal lagoons south of "
                "Santa Cruz de la Sierra. A unique Bolivian ecosystem where desert and "
                "lagoon coexist. Ideal for sandboarding and nature photography."
            ),
        },
        "fr": {
            "nombre": "Lomas de Arena (Dunes de Sable)",
            "descripcion": (
                "Parc régional avec des dunes de sable et des lagons saisonniers au sud "
                "de Santa Cruz de la Sierra. Écosystème unique en Bolivie, idéal pour "
                "le sandboard et la photographie de nature."
            ),
        },
        "it": {
            "nombre": "Lomas de Arena (Dune di Sabbia)",
            "descripcion": (
                "Parco regionale con dune di sabbia e lagune stagionali a sud di "
                "Santa Cruz de la Sierra. Ecosistema unico della Bolivia, ideale per "
                "il sandboarding e la fotografia naturalistica."
            ),
        },
    },
    "ParqueUrbano": {
        "es": {
            "nombre": "Parque Urbano",
            "descripcion": (
                "Parque recreativo de gran extensión dentro de Santa Cruz de la Sierra, "
                "con áreas verdes, senderos y espacios de esparcimiento. Punto de encuentro "
                "popular para actividades al aire libre."
            ),
        },
        "en": {
            "nombre": "Parque Urbano (Urban Park)",
            "descripcion": (
                "Large recreational park within Santa Cruz de la Sierra, with green areas, "
                "trails and recreation spaces. A popular meeting point for outdoor activities "
                "among the city's residents."
            ),
        },
        "fr": {
            "nombre": "Parque Urbano (Parc Urbain)",
            "descripcion": (
                "Grand parc récréatif au cœur de Santa Cruz de la Sierra, avec espaces "
                "verts, sentiers et aires de loisirs. Lieu de rencontre populaire pour "
                "les activités de plein air."
            ),
        },
        "it": {
            "nombre": "Parque Urbano (Parco Urbano)",
            "descripcion": (
                "Ampio parco ricreativo nella città di Santa Cruz de la Sierra, con aree "
                "verdi, sentieri e spazi ricreativi. Punto di incontro popolare per "
                "le attività all'aperto."
            ),
        },
    },
    "Plaza24": {
        "es": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": (
                "Plaza principal y centro histórico de Santa Cruz de la Sierra. Rodeada "
                "de edificios coloniales, la Catedral y sedes de gobierno, es el punto "
                "de encuentro social más tradicional de la ciudad."
            ),
        },
        "en": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": (
                "Main square and historic center of Santa Cruz de la Sierra. Surrounded "
                "by colonial buildings, the Cathedral and government offices, it is the "
                "city's most traditional social gathering point."
            ),
        },
        "fr": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": (
                "Place principale et centre historique de Santa Cruz de la Sierra. Entourée "
                "d'édifices coloniaux, de la Cathédrale et des sièges gouvernementaux, "
                "c'est le point de rencontre social le plus traditionnel de la ville."
            ),
        },
        "it": {
            "nombre": "Plaza 24 de Septiembre",
            "descripcion": (
                "Piazza principale e centro storico di Santa Cruz de la Sierra. Circondata "
                "da edifici coloniali, la Cattedrale e sedi governative, è il punto di "
                "incontro sociale più tradizionale della città."
            ),
        },
    },
    "Tahuichi": {
        "es": {
            "nombre": "Estadio Ramón Tahuichi Aguilera",
            "descripcion": (
                "Estadio de fútbol principal de Santa Cruz de la Sierra, sede de partidos "
                "profesionales y asociado a la célebre academia de fútbol formativo Tahuichi."
            ),
        },
        "en": {
            "nombre": "Ramón Tahuichi Aguilera Stadium",
            "descripcion": (
                "Main football stadium of Santa Cruz de la Sierra, home to professional "
                "matches and associated with the famous Tahuichi youth football academy."
            ),
        },
        "fr": {
            "nombre": "Stade Ramón Tahuichi Aguilera",
            "descripcion": (
                "Principal stade de football de Santa Cruz de la Sierra, accueillant des "
                "matchs professionnels et associé à la célèbre académie de football "
                "jeunesse Tahuichi."
            ),
        },
        "it": {
            "nombre": "Stadio Ramón Tahuichi Aguilera",
            "descripcion": (
                "Principale stadio di calcio di Santa Cruz de la Sierra, sede di partite "
                "professionistiche e associato alla famosa accademia di calcio giovanile "
                "Tahuichi."
            ),
        },
    },
    "Ventura": {
        "es": {
            "nombre": "Ventura Mall",
            "descripcion": (
                "Centro comercial moderno de Santa Cruz de la Sierra, con tiendas, "
                "restaurantes y espacios de entretenimiento. Uno de los destinos de "
                "compras y ocio más visitados de la ciudad."
            ),
        },
        "en": {
            "nombre": "Ventura Mall",
            "descripcion": (
                "Modern shopping center in Santa Cruz de la Sierra, with shops, restaurants "
                "and entertainment spaces. One of the most visited shopping and leisure "
                "destinations in the city."
            ),
        },
        "fr": {
            "nombre": "Ventura Mall",
            "descripcion": (
                "Centre commercial moderne de Santa Cruz de la Sierra, avec boutiques, "
                "restaurants et espaces de divertissement. L'une des destinations shopping "
                "et loisirs les plus fréquentées de la ville."
            ),
        },
        "it": {
            "nombre": "Ventura Mall",
            "descripcion": (
                "Centro commerciale moderno di Santa Cruz de la Sierra, con negozi, "
                "ristoranti e spazi di intrattenimento. Una delle destinazioni shopping "
                "e svago più visitate della città."
            ),
        },
    },
}


class TranslationService:
    """Servicio de traducción con fallback de 3 niveles.

    Cadena de fallback en get_landmark_translations():
        1. Claude API en vivo — si ANTHROPIC_API_KEY está configurada.
        2. data/translations.json — si el archivo existe (pre-generado offline).
        3. _STATIC_TRANSLATIONS — siempre disponible, embebido en el código.

    El sistema NUNCA debe caerse por fallo del LLM (Decisión 006 — NLLB-200).
    """

    def __init__(self, translations_path: str = "data/translations.json"):
        """Inicializa el servicio. El JSON es opcional — usa datos estáticos si no existe.

        Args:
            translations_path: ruta al JSON pre-generado (opcional).
        """
        self._translations: dict = {}
        if os.path.exists(translations_path):
            with open(translations_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            logger.info(
                f"TranslationService: {len(self._translations)} landmarks "
                f"desde {translations_path}"
            )
        else:
            logger.warning(
                f"No se encontró {translations_path}. "
                "Usando datos estáticos como fallback. "
                "Para generar el JSON: python scripts/generate_translations.py"
            )

        self._openrouter_client = None
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key:
                self._openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )
                logger.info("TranslationService: cliente OpenRouter inicializado.")
            else:
                logger.warning(
                    "OPENROUTER_API_KEY no configurada. "
                    "Se usará JSON o datos estáticos para las traducciones."
                )
        except ImportError:
            logger.warning("openai no instalado. pip install openai")

        self._nllb_pipeline = None

    # ── Contrato 1: Traducción de salida ─────────────────────────────────────

    def get_landmark_translations(self, landmark_id: str) -> dict:
        """Devuelve info del landmark en 4 idiomas (ES/EN/FR/IT).

        Cadena de fallback:
            1. Claude API en vivo — si ANTHROPIC_API_KEY está configurada.
            2. data/translations.json — si existe y contiene el landmark.
            3. _STATIC_TRANSLATIONS — siempre disponible para los 8 landmarks.

        Args:
            landmark_id: ID del landmark (uno de config.LANDMARK_CLASSES).

        Returns:
            {
                "es": {"nombre": str, "descripcion": str},
                "en": {"nombre": str, "descripcion": str},
                "fr": {"nombre": str, "descripcion": str},
                "it": {"nombre": str, "descripcion": str},
            }
        """
        # Nivel 1: LLM en vivo
        if self._openrouter_client is not None:
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

    @property
    def chat_available(self) -> bool:
        """True si el LLM (OpenRouter) está disponible para info extendida y chat.

        El frontend usa este flag para mostrar u ocultar el chat (requisito:
        el chat es opcional / solo si el LLM puede). Sin OPENROUTER_API_KEY, el
        sistema sigue funcionando con las traducciones offline.
        """
        return self._openrouter_client is not None

    # ── Info del lugar en el idioma elegido (NUEVO — /place/info) ────────────

    def get_place_info(self, landmark_id: str, language: str) -> dict:
        """Devuelve la info de un lugar en el idioma pedido.

        Estrategia en cascada (degradación elegante):
            1. Si ``language`` ∈ {es,en,fr,it} y el landmark tiene traducción
               pre-generada → lookup O(1) (sin latencia, sin costo, sin red).
            2. Si no (idioma arbitrario o se quiere texto más rico) y el LLM
               está disponible → se genera con el LLM en el idioma pedido.
            3. Si nada de lo anterior aplica → cae al español pre-generado.

        Args:
            landmark_id: ID del landmark (uno de config.LANDMARK_CLASSES).
            language: código de idioma ISO 639-1 (es, en, fr, it, pt, de, ...).

        Returns:
            {
                "landmark_id": str,
                "language": str,
                "name": str,
                "description": str,
                "source": "offline" | "llm" | "fallback",
                "chat_available": bool,
            }
        """
        language = (language or "es").lower().strip()
        entry = self._translations.get(landmark_id, {})

        # ── 1. Lookup O(1) para idiomas pre-generados ────────────────────────
        if language in _OFFLINE_LANGUAGES and language in entry:
            data = entry[language]
            return {
                "landmark_id": landmark_id,
                "language": language,
                "name": data.get("nombre", landmark_id),
                "description": data.get("descripcion", ""),
                "source": "offline",
                "chat_available": self.chat_available,
            }

        # ── 2. Idioma arbitrario → LLM ───────────────────────────────────────
        if self._openrouter_client is not None:
            generated = self._place_info_with_llm(landmark_id, language, entry)
            if generated is not None:
                return generated

        # ── 3. Fallback: español pre-generado (o el ID si no hay nada) ───────
        es = entry.get("es", {})
        return {
            "landmark_id": landmark_id,
            "language": language,
            "name": es.get("nombre", landmark_id),
            "description": es.get(
                "descripcion",
                "Descripción no disponible para este lugar.",
            ),
            "source": "fallback",
            "chat_available": self.chat_available,
        }

    def _place_info_with_llm(
        self, landmark_id: str, language: str, entry: dict
    ) -> Optional[dict]:
        """Genera nombre + descripción del lugar con el LLM. None si falla."""
        lang_name = _LANGUAGE_DISPLAY.get(language, language)
        # Contexto en español (lo que sí sabemos del lugar) para anclar al LLM.
        es = entry.get("es", {})
        contexto = (
            f"Nombre: {es.get('nombre', landmark_id)}\n"
            f"Descripción: {es.get('descripcion', '')}"
        ).strip()

        prompt = (
            "Eres un guía turístico experto de Santa Cruz de la Sierra, Bolivia. "
            f"Te doy información en español sobre un lugar turístico:\n\n{contexto}\n\n"
            f"Reescribe el nombre y una descripción atractiva (3-5 frases) de ese "
            f"lugar en {lang_name}. Responde SOLO con un JSON válido con las claves "
            f"\"nombre\" y \"descripcion\", sin texto adicional."
        )
        try:
            response = self._openrouter_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip().rstrip("```").strip()
            data = json.loads(raw)
            return {
                "landmark_id": landmark_id,
                "language": language,
                "name": data.get("nombre", landmark_id),
                "description": data.get("descripcion", ""),
                "source": "llm",
                "chat_available": True,
            }
        except Exception as e:
            logger.warning(f"LLM falló al generar info de '{landmark_id}' ({language}): {e}")
            return None

    # ── Chat conversacional sobre el lugar (NUEVO — /chat) ───────────────────

    def chat_reply(
        self,
        landmark_id: str,
        language: str,
        message: str,
        history: Optional[list] = None,
    ) -> Optional[str]:
        """Responde una pregunta del usuario sobre el lugar.

        Mantiene la conversación pasando ``history`` (la API es stateless
        respecto al chat; el historial lo guarda el frontend).

        Args:
            landmark_id: lugar sobre el que conversa el usuario.
            language: idioma en el que debe responder (ISO 639-1).
            message: mensaje nuevo del usuario.
            history: lista de turnos previos
                ``[{"role": "user"|"assistant", "content": str}, ...]``.

        Returns:
            El texto de la respuesta, o ``None`` si el LLM no está disponible
            (la API traduce eso a un 503 y el frontend oculta el chat).
        """
        if self._openrouter_client is None:
            return None

        language = (language or "es").lower().strip()
        lang_name = _LANGUAGE_DISPLAY.get(language, language)
        entry = self._translations.get(landmark_id, {})
        place_name = entry.get("es", {}).get("nombre", landmark_id)

        system_prompt = (
            f"Eres un guía turístico de Santa Cruz de la Sierra, Bolivia. "
            f"Responde SOLO sobre el lugar \"{place_name}\" y su entorno, "
            f"siempre en {lang_name}. Si te preguntan por otra cosa, redirige "
            f"amablemente la conversación de vuelta a este lugar. Sé claro, "
            f"cálido y conciso."
        )

        # OpenAI/OpenRouter: el system prompt va como primer mensaje del rol system.
        messages = [{"role": "system", "content": system_prompt}]
        for turn in (history or []):
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        try:
            response = self._openrouter_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                max_tokens=512,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"chat_reply falló para '{landmark_id}': {e}")
            return (
                "Lo siento, no pude generar una respuesta en este momento. "
                "Intentá de nuevo en unos segundos."
            )

    # ── Contrato 2: Normalización de entrada ─────────────────────────────────

    def normalize_input(self, query: str) -> dict:
        """Normaliza una consulta en idioma inesperado al español.

        Pipeline:
            1. Detecta idioma con langdetect (local).
            2. Si ya es español → passthrough.
            3. Si no → intenta con Claude LLM (entiende intención turística).
            4. Si el LLM falla → cae a NLLB-200 (local, sin internet).

        Args:
            query: consulta del usuario en cualquier idioma.

        Returns:
            {
                "original"     : str,
                "detected_lang": str,
                "normalized"   : str,
                "method"       : str,  # "passthrough" | "llm" | "nllb" | "error"
            }
        """
        detected_lang = self._detect_language(query)

        if detected_lang == "es":
            return {
                "original": query,
                "detected_lang": "es",
                "normalized": query,
                "method": "passthrough",
            }

        if self._openrouter_client is not None:
            result = self._normalize_with_llm(query, detected_lang)
            if result is not None:
                return result

        return self._normalize_with_nllb(query, detected_lang)

    # ── Métodos internos ──────────────────────────────────────────────────────

    def _get_info_from_llm(self, landmark_id: str) -> Optional[dict]:
        """Genera info del landmark en ES/EN/FR/IT con OpenRouter. Devuelve None si falla."""
        if self._openrouter_client is None:
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
            response = self._openrouter_client.chat.completions.create(
                model="google/gemini-2.5-flash-lite",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()

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

    def _detect_language(self, text: str) -> str:
        """Detecta el idioma con langdetect (local, sin red)."""
        try:
            from langdetect import detect
            return detect(text)
        except Exception as e:
            logger.warning(f"langdetect falló: {e}. Asumiendo idioma desconocido.")
            return "unknown"

    def _normalize_with_llm(self, query: str, detected_lang: str) -> Optional[dict]:
        """Intenta normalizar al español con OpenRouter. Devuelve None si falla."""
        prompt = (
            "Eres un asistente turístico especializado en Santa Cruz de la Sierra, Bolivia. "
            "El usuario busca un lugar turístico. Su consulta puede estar en cualquier idioma. "
            f"Consulta: \"{query}\"\n\n"
            "Respondé SOLO con el nombre del lugar turístico en español. "
            "Si es un lugar conocido de Santa Cruz (Cambódromo, Catedral Basílica San Lorenzo, "
            "Cristo Redentor, Lomas de Arena, Parque Urbano, Plaza 24 de Septiembre, "
            "Estadio Ramón Tahuichi Aguilera, Ventura Mall), devolvé exactamente ese nombre. "
            "Si no podés identificar el lugar, respondé: NO_MATCH"
        )
        try:
            response = self._openrouter_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                max_tokens=128,
                messages=[{"role": "user", "content": prompt}],
            )
            normalized = response.choices[0].message.content.strip()
            logger.info(f"LLM normalizó '{query}' → '{normalized}'")
            return {
                "original": query,
                "detected_lang": detected_lang,
                "normalized": normalized,
                "method": "llm",
            }
        except Exception as e:
            logger.warning(f"LLM falló al normalizar, cayendo a NLLB-200: {e}")
            return None

    def _normalize_with_nllb(self, query: str, detected_lang: str) -> dict:
        """Fallback local con NLLB-200 cuando el LLM no está disponible.

        DECISIÓN (Decisión 006): NLLB-200 sobre MarianMT porque cubre 200 idiomas
        con un único modelo y corre en CPU sin internet.
        """
        if self._nllb_pipeline is None:
            try:
                from transformers import pipeline as hf_pipeline
                logger.info("Cargando NLLB-200 en CPU (puede tardar la primera vez)...")
                self._nllb_pipeline = hf_pipeline(
                    "translation",
                    model="facebook/nllb-200-distilled-600M",
                    device=-1,
                )
                logger.info("NLLB-200 listo.")
            except Exception as e:
                logger.error(f"No se pudo cargar NLLB-200: {e}")
                return {
                    "original": query,
                    "detected_lang": detected_lang,
                    "normalized": query,
                    "method": "error",
                }

        src_lang = _LANGDETECT_TO_NLLB.get(detected_lang, "eng_Latn")
        try:
            result = self._nllb_pipeline(
                query,
                src_lang=src_lang,
                tgt_lang="spa_Latn",
                max_length=256,
            )
            normalized = result[0]["translation_text"]
            logger.info(f"NLLB-200 normalizó '{query}' ({detected_lang}) → '{normalized}'")
            return {
                "original": query,
                "detected_lang": detected_lang,
                "normalized": normalized,
                "method": "nllb",
            }
        except Exception as e:
            logger.error(f"NLLB-200 también falló: {e}")
            return {
                "original": query,
                "detected_lang": detected_lang,
                "normalized": query,
                "method": "error",
            }
