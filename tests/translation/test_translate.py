"""Tests para TranslationService — fallback chain de 3 niveles."""
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
            assert lm in _STATIC_TRANSLATIONS, f"{lm} falta en _STATIC_TRANSLATIONS"

    def test_all_languages_present(self):
        for lm in ALL_LANDMARKS:
            for lang in EXPECTED_LANGS:
                assert lang in _STATIC_TRANSLATIONS[lm], f"{lm}.{lang} falta"

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
        json_data = {
            "Cristo": {
                "es": {"nombre": "x", "descripcion": "y"},
                "en": {"nombre": "x", "descripcion": "y"},
                "fr": {"nombre": "x", "descripcion": "y"},
                "it": {"nombre": "x", "descripcion": "y"},
            }
        }
        json_path = tmp_path / "translations.json"
        json_path.write_text(json.dumps(json_data), encoding="utf-8")
        svc = TranslationService(translations_path=str(json_path))
        # Ventura no está en el JSON, debe caer a estáticos
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
        mock_response.content = [MagicMock(text="esto no es JSON")]
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
