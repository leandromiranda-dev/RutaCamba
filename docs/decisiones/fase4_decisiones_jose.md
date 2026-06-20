# Bitácora de decisiones — Fase 4 — Jose Alfredo

> Este archivo duplica las decisiones de Fase 4 del archivo consolidado
> `docs/decisiones/fase2_decisiones_jose.md` (decisiones 004-006).
> Las decisiones de Fase 2-B están también en ese archivo (decisiones 001-003).

---

## Decisión 001 — Pre-generar traducciones offline vs LLM en cada request

- **Fecha:** 2026-06-11
- **Contexto / problema:** El endpoint `/predict` necesita devolver traducciones EN/FR/IT. ¿Llamo al LLM en cada request o pre-genero offline?
- **Qué elegí:** Pre-generar offline con `generate_translations.py` y guardar en `data/translations.json`. En runtime: lookup O(1) desde dict en memoria.
- **Por qué lo elegí:** Latencia (LLM ~2s vs dict instantáneo), costo (32 pares fijos vs costo variable acumulativo), disponibilidad sin internet, y control de calidad manual de las traducciones.
- **Alternativa(s) que descarté y POR QUÉ no:** LLM en cada request — latencia intolerable, costo variable, falla sin internet en la demo.
- **Posible pregunta de defensa que esto responde:** "¿Por qué pre-generaste las traducciones?"

---

## Decisión 002 — LLM para normalización de entrada vs traductor literal

- **Fecha:** 2026-06-11
- **Contexto / problema:** El usuario puede consultar en inglés, francés, italiano, etc. Necesito convertirlo al español para el sistema de clasificación.
- **Qué elegí:** LLM (Claude) para `normalize_input` porque entiende intención semántica.
- **Por qué lo elegí:** Ejemplo clave: `"Where is the big Jesus statue?"` → LLM devuelve `"Cristo Redentor"`. Un traductor literal daría `"¿Dónde está la gran estatua de Jesús?"`, que no es el nombre del landmark. El LLM también maneja errores ortográficos y referencias culturales.
- **Posible pregunta de defensa que esto responde:** "¿Por qué usás un LLM para normalizar en lugar de un traductor estándar?"

---

## Decisión 003 — NLLB-200 como fallback vs MarianMT / Google Translate

- **Fecha:** 2026-06-11
- **Contexto / problema:** El LLM puede fallar (sin red, timeout). Necesito un fallback completamente offline y multilingüe.
- **Qué elegí:** NLLB-200 distilled 600M (Facebook/Meta, HuggingFace) con carga lazy en CPU.
- **Por qué lo elegí:** Un solo modelo cubre 200 idiomas; completamente offline post-descarga; carga lazy (solo se instancia si el LLM falla); compatible con CPU sin GPU.
- **Alternativa(s) que descarté y POR QUÉ no:** MarianMT — un modelo separado por par de idiomas (>1 GB en total, más complejidad). Google Translate — requiere internet, no es un verdadero fallback offline.
- **Posible pregunta de defensa que esto responde:** "¿Por qué NLLB-200 y no MarianMT o Google Translate?"
