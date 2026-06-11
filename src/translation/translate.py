"""translate.py — Servicio de traducción multilingüe con LLM + fallback.

Jose (Fase 4): implementá TranslationService.

CONTRATO (no cambiar las firmas — Nicole las usa desde la API):
    class TranslationService:
        def get_landmark_translations(self, landmark_id: str) -> dict
        def normalize_input(self, query: str) -> dict
"""

# TODO (Jose): implementar TranslationService


class TranslationService:
    def __init__(self, translations_path: str = "data/translations.json"):
        raise NotImplementedError("Jose (Fase 4): implementá TranslationService.__init__()")

    def get_landmark_translations(self, landmark_id: str) -> dict:
        raise NotImplementedError("Jose (Fase 4): implementá get_landmark_translations()")

    def normalize_input(self, query: str) -> dict:
        raise NotImplementedError("Jose (Fase 4): implementá normalize_input()")
