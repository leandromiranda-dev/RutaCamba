"""generate_translations.py — Genera data/translations.json con Claude API.

Jose (Fase 4): ejecutá este script UNA vez offline para pre-generar las traducciones.

Uso:
    python scripts/generate_translations.py --api-key <tu-clave>
    # O con variable de entorno:
    set ANTHROPIC_API_KEY=<tu-clave>
    python scripts/generate_translations.py

Salida: data/translations.json con estructura:
{
  "cristo_redentor": {
    "es": {"nombre": "...", "descripcion": "..."},
    "en": {"nombre": "...", "descripcion": "..."},
    "fr": {"nombre": "...", "descripcion": "..."},
    "it": {"nombre": "...", "descripcion": "..."}
  },
  ...
}

IMPORTANTE: revisá las traducciones manualmente antes de commitear.
"""

import argparse
import json
import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Catálogo de los 8 landmarks (mismos IDs que config.LANDMARK_CLASSES) ─────
# FUENTE: context.md + config.py — NO cambiar los keys sin coordinar con el equipo
LANDMARK_CATALOG = {
    "cristo_redentor": {
        "nombre": "Cristo Redentor de Santa Cruz",
        "descripcion": (
            "Estatua monumental del Cristo Redentor ubicada en la ciudad de "
            "Santa Cruz de la Sierra, Bolivia. Es uno de los íconos más reconocidos "
            "de la ciudad, situada en un punto elevado que ofrece vistas panorámicas "
            "sobre la urbe y sus alrededores."
        ),
    },
    "fuerte_samaipata": {
        "nombre": "El Fuerte de Samaipata",
        "descripcion": (
            "Sitio arqueológico precolombino declarado Patrimonio de la Humanidad "
            "por la UNESCO. Ubicado en la provincia Florida del departamento de Santa "
            "Cruz, fue construido por la cultura chané y posteriormente ocupado por los "
            "incas. Destaca su enorme roca esculpida con relieves únicos en el mundo."
        ),
    },
    "parque_el_arenal": {
        "nombre": "Parque El Arenal",
        "descripcion": (
            "Parque histórico y emblemático ubicado en el centro de Santa Cruz de la "
            "Sierra. Es un espacio de recreación rodeado de áreas verdes, lagunas "
            "artificiales y monumentos que celebran la cultura e historia cruceña. "
            "Punto de encuentro popular para locales y turistas."
        ),
    },
    "jardin_botanico": {
        "nombre": "Jardín Botánico de Santa Cruz",
        "descripcion": (
            "Reserva natural y jardín botánico que preserva la flora tropical del "
            "oriente boliviano. Cuenta con senderos ecológicos, colecciones de plantas "
            "nativas, mariposario y zonas de picnic. Es ideal para familias y amantes "
            "de la naturaleza."
        ),
    },
    "catedral_metropolitana": {
        "nombre": "Catedral Metropolitana Basílica de San Lorenzo",
        "descripcion": (
            "Templo católico de estilo barroco mestizo ubicado en la Plaza 24 de "
            "Septiembre, corazón histórico de Santa Cruz de la Sierra. Es la catedral "
            "más importante del departamento y uno de los edificios coloniales más "
            "representativos de Bolivia."
        ),
    },
    "biocentro_guembe": {
        "nombre": "Biocentro Güembé",
        "descripcion": (
            "Parque temático y ecoturístico a las afueras de Santa Cruz. Ofrece "
            "piscinas con olas artificiales, mariposario, orquideario, senderos en "
            "la naturaleza y actividades de aventura. Es el destino de entretenimiento "
            "familiar más popular del departamento."
        ),
    },
    "lomas_de_arena": {
        "nombre": "Lomas de Arena",
        "descripcion": (
            "Parque regional con dunas de arena y lagunas estacionales, ubicado al "
            "sur de Santa Cruz de la Sierra. Es un ecosistema único de Bolivia, "
            "donde el desierto y la laguna conviven en perfecta armonía. "
            "Ideal para sandboarding y fotografía de naturaleza."
        ),
    },
    "manzana_uno": {
        "nombre": "Manzana Uno",
        "descripcion": (
            "Centro cultural y comercial emblemático en el corazón de Santa Cruz. "
            "Alberga museos, galerías de arte contemporáneo, tiendas de diseño, "
            "restaurantes gourmet y espacios de coworking en un entorno arquitectónico "
            "moderno que combina historia y vanguardia."
        ),
    },
}

LANGUAGE_NAMES = {
    "en": "inglés",
    "fr": "francés",
    "it": "italiano",
}


def translate_with_claude(
    client,
    nombre: str,
    descripcion: str,
    target_lang_code: str,
    max_retries: int = 3,
) -> dict:
    """Traduce nombre y descripción de un landmark usando Claude API.

    Implementa retry con backoff exponencial para manejar errores de red
    o rate limiting (✍️ Decisión — manejo de errores de red).

    Args:
        client: instancia de anthropic.Anthropic.
        nombre: nombre del landmark en español.
        descripcion: descripción del landmark en español.
        target_lang_code: "en", "fr" o "it".
        max_retries: número máximo de intentos antes de lanzar excepción.

    Returns:
        {"nombre": str, "descripcion": str} en el idioma objetivo.
    """
    lang_name = LANGUAGE_NAMES[target_lang_code]
    prompt = (
        f"Eres un experto en turismo que traduce textos sobre atracciones turísticas "
        f"de Bolivia al {lang_name}. Traducí exactamente el siguiente texto turístico "
        f"al {lang_name}. Respondé SOLO con un JSON válido con las claves "
        f"\"nombre\" y \"descripcion\", sin ningún texto adicional.\n\n"
        f"Texto a traducir:\n"
        f"nombre: {nombre}\n"
        f"descripcion: {descripcion}"
    )

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            # Limpiar posibles bloques de código markdown
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()

            translated = json.loads(raw)
            return translated

        except json.JSONDecodeError as e:
            logger.warning(
                f"[intento {attempt + 1}] Respuesta no es JSON válido: {e}\n"
                f"Respuesta cruda: {raw[:200]}"
            )
        except Exception as e:
            logger.warning(f"[intento {attempt + 1}] Error de API: {e}")

        if attempt < max_retries - 1:
            wait = 2 ** attempt  # backoff exponencial: 1s, 2s, 4s
            logger.info(f"Esperando {wait}s antes del siguiente intento...")
            time.sleep(wait)

    raise RuntimeError(
        f"No se pudo traducir '{nombre}' al {lang_name} "
        f"después de {max_retries} intentos."
    )


def generate_translations(api_key: str, output_path: str) -> None:
    """Genera translations.json con Claude para los 8 landmarks."""
    try:
        import anthropic
    except ImportError:
        logger.error("Instalá anthropic: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    translations = {}

    total = len(LANDMARK_CATALOG)
    for idx, (landmark_id, data_es) in enumerate(LANDMARK_CATALOG.items(), 1):
        logger.info(f"[{idx}/{total}] Procesando: {landmark_id}")

        translations[landmark_id] = {
            "es": {
                "nombre": data_es["nombre"],
                "descripcion": data_es["descripcion"],
            }
        }

        for lang_code in ("en", "fr", "it"):
            logger.info(f"  → Traduciendo a {lang_code}...")
            try:
                translated = translate_with_claude(
                    client,
                    data_es["nombre"],
                    data_es["descripcion"],
                    lang_code,
                )
                translations[landmark_id][lang_code] = translated
                logger.info(f"  ✓ {lang_code}: {translated['nombre']}")
            except RuntimeError as e:
                logger.error(f"  ✗ FALLÓ {lang_code} para {landmark_id}: {e}")
                # Fallback: copiar el español si falla la traducción
                translations[landmark_id][lang_code] = {
                    "nombre": f"[{lang_code.upper()} - PENDING] {data_es['nombre']}",
                    "descripcion": data_es["descripcion"],
                }

        # Pausa entre landmarks para respetar rate limits
        if idx < total:
            time.sleep(1)

    # Guardar resultado
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ translations.json generado: {output_path}")
    logger.info("⚠️  IMPORTANTE: revisá manualmente las traducciones antes de commitear.")


def main():
    parser = argparse.ArgumentParser(
        description="Genera data/translations.json con Claude API (correr UNA vez offline)."
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="API key de Anthropic (o usar variable ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--output",
        default="data/translations.json",
        help="Ruta de salida (default: data/translations.json)",
    )
    args = parser.parse_args()

    if not args.api_key:
        logger.error(
            "No se proporcionó API key de Anthropic.\n"
            "Usá --api-key <clave> o configurá ANTHROPIC_API_KEY como variable de entorno."
        )
        sys.exit(1)

    generate_translations(api_key=args.api_key, output_path=args.output)


if __name__ == "__main__":
    main()
