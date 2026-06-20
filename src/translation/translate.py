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


class TranslationService:
    """Servicio de traducción con lookup O(1) y normalización de entrada.

    Arquitectura de tres capas:
        1. Lookup O(1) desde JSON pre-generado → sin latencia, sin red.
        2. Normalización de entrada: LLM (Claude) para entender intención.
        3. Fallback local: NLLB-200 (carga lazy en CPU) si el LLM no está disponible.

    El sistema NUNCA debe caerse por fallo del LLM (✍️ Decisión 006 — NLLB-200).
    """

    def __init__(self, translations_path: str = "data/translations.json"):
        """Inicializa el servicio cargando el JSON de traducciones en memoria.

        Args:
            translations_path: ruta al JSON generado por generate_translations.py.

        Raises:
            FileNotFoundError: si el JSON no existe aún.
        """
        # ── Cargar traducciones pre-generadas ─────────────────────────────────
        # DECISIÓN (✍️ Decisión 004): cargamos OFFLINE para lookup O(1) en runtime.
        # Alternativa descartada: llamar al LLM en cada /predict → latencia ~2s
        # por request y costo acumulado. Con 8 landmarks fijos, 32 traducciones
        # pre-generadas son suficientes y la latencia es irrelevante.
        if not os.path.exists(translations_path):
            raise FileNotFoundError(
                f"No se encontró {translations_path}.\n"
                "Ejecutá primero:\n"
                "    python scripts/generate_translations.py --api-key <clave>"
            )
        with open(translations_path, "r", encoding="utf-8") as f:
            self._translations: dict = json.load(f)
        logger.info(
            f"TranslationService: {len(self._translations)} landmarks cargados "
            f"desde {translations_path}"
        )

        # ── Intentar inicializar cliente Anthropic ────────────────────────────
        self._anthropic_client = None
        try:
            import anthropic  # noqa: F401
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("TranslationService: cliente Anthropic inicializado.")
            else:
                logger.warning(
                    "ANTHROPIC_API_KEY no configurada. "
                    "normalize_input usará directamente NLLB-200 como fallback."
                )
        except ImportError:
            logger.warning(
                "anthropic no está instalado. "
                "Instala con: pip install anthropic"
            )

        # ── NLLB-200: carga lazy (solo cuando el LLM falla) ──────────────────
        self._nllb_pipeline = None

    # ── Contrato 1: Traducción de salida (Criterio 1 — 2 pts) ────────────────

    def get_landmark_translations(self, landmark_id: str) -> dict:
        """Devuelve las traducciones del landmark en los 4 idiomas soportados.

        Lookup O(1) desde el JSON en memoria — sin llamadas a red.

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
        if landmark_id in self._translations:
            return self._translations[landmark_id]

        # Fallback si el ID no está en el JSON (no debería pasar en producción)
        logger.warning(f"landmark_id '{landmark_id}' no encontrado en translations.json")
        fallback_msg = {
            lang: {"nombre": landmark_id, "descripcion": "Descripción no disponible."}
            for lang in ("es", "en", "fr", "it")
        }
        return fallback_msg

    # ── Contrato 2: Normalización de entrada (Criterio 2 — 2 pts) ───────────

    def normalize_input(self, query: str) -> dict:
        """Normaliza una consulta en idioma inesperado al español.

        Pipeline:
            1. Detecta idioma con langdetect (local, no falla sin red).
            2. Si ya es español → passthrough.
            3. Si no → intenta con Claude LLM (entiende intención turística).
            4. Si el LLM falla → cae a NLLB-200 (local, sin internet).

        DECISIÓN (✍️ Decisión 005): se usa LLM y no traductor literal porque
        el LLM entiende la INTENCIÓN. Ejemplo: "Where is the big Jesus statue?"
        → "Cristo Redentor". Un traductor literal solo haría word-for-word.

        Args:
            query: consulta del usuario en cualquier idioma.

        Returns:
            {
                "original"     : str,  # consulta original
                "detected_lang": str,  # código ISO 639-1 detectado
                "normalized"   : str,  # consulta normalizada en español
                "method"       : str,  # "passthrough" | "llm" | "nllb" | "error"
            }
        """
        # ── Paso 1: Detectar idioma ───────────────────────────────────────────
        detected_lang = self._detect_language(query)

        # ── Paso 2: Si ya es español, passthrough ────────────────────────────
        if detected_lang == "es":
            return {
                "original": query,
                "detected_lang": "es",
                "normalized": query,
                "method": "passthrough",
            }

        # ── Paso 3: Intentar con LLM ─────────────────────────────────────────
        if self._anthropic_client is not None:
            result = self._normalize_with_llm(query, detected_lang)
            if result is not None:
                return result

        # ── Paso 4: Fallback NLLB-200 ────────────────────────────────────────
        return self._normalize_with_nllb(query, detected_lang)

    # ── Métodos internos ──────────────────────────────────────────────────────

    def _detect_language(self, text: str) -> str:
        """Detecta el idioma con langdetect (local, sin red)."""
        try:
            from langdetect import detect, LangDetectException
            return detect(text)
        except Exception as e:
            logger.warning(f"langdetect falló: {e}. Asumiendo idioma desconocido.")
            return "unknown"

    def _normalize_with_llm(self, query: str, detected_lang: str) -> Optional[dict]:
        """Intenta normalizar al español con Claude. Devuelve None si falla."""
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
            response = self._anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=128,
                messages=[{"role": "user", "content": prompt}],
            )
            normalized = response.content[0].text.strip()
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

        DECISIÓN (✍️ Decisión 006): NLLB-200 sobre MarianMT porque:
        - NLLB cubre 200 idiomas con un único modelo (MarianMT requiere un
          modelo separado por par de idiomas → ≥600 MB por par).
        - NLLB corre en CPU sin internet, cumple el requisito de fallback offline.
        - Google Translate no es offline → no aplica como fallback de emergencia.
        """
        # Carga lazy: solo se instancia si realmente se necesita
        if self._nllb_pipeline is None:
            try:
                from transformers import pipeline as hf_pipeline
                logger.info("Cargando NLLB-200 en CPU (puede tardar la primera vez)...")
                self._nllb_pipeline = hf_pipeline(
                    "translation",
                    model="facebook/nllb-200-distilled-600M",
                    device=-1,  # CPU siempre (sin CUDA requerido)
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
