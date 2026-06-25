"""test_llm.py — Prueba rápida del servicio de traducción con LLM.

Corre sin necesitar el modelo de landmarks ni la galería de Re-ID.
Muestra los 3 niveles de fallback en acción.

Uso:
    python scripts/test_llm.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.translation.translate import TranslationService

LANG_LABELS = {
    "es": "Espanol",
    "en": "English",
    "fr": "Francais",
    "it": "Italiano",
}


def print_result(landmark_id: str, result: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  {landmark_id}")
    print('='*60)
    for lang_code, label in LANG_LABELS.items():
        data = result.get(lang_code, {})
        nombre = data.get("nombre", "—")
        descripcion = data.get("descripcion", "—")
        print(f"\n  [{label}]")
        print(f"  Nombre: {nombre}")
        print(f"  Desc  : {descripcion}")


def main():
    print("\nInicializando TranslationService...")
    svc = TranslationService()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        print("  API key encontrada -> usara LLM en vivo (OpenRouter)")
    else:
        print("  Sin API key -> usara JSON o datos estaticos")

    landmarks_to_test = ["Cristo", "Plaza24", "DunasArena"]

    for landmark_id in landmarks_to_test:
        print(f"\nConsultando info de: {landmark_id}...")
        result = svc.get_landmark_translations(landmark_id)
        print_result(landmark_id, result)

    print(f"\n{'='*60}")
    print("  Prueba de normalize_input (LLM entiende intencion)")
    print('='*60)
    queries = [
        "Where is the big Jesus statue?",
        "Ou est la cathedrale?",
        "Dove sono le dune di sabbia?",
    ]
    for q in queries:
        print(f"\n  Query: {q!r}")
        res = svc.normalize_input(q)
        print(f"  -> Normalizado: {res['normalized']!r}  (metodo: {res['method']})")

    print("\nPrueba completada.\n")


if __name__ == "__main__":
    main()
