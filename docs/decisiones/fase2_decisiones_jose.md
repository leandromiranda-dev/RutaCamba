# Bitácora de decisiones — Fase 2B + Fase 4 — Jose Alfredo

> Completá este archivo a medida que avanzás. Cada ✍️ en tus `.md` de fase es una entrada aquí.
> Esta bitácora cubre TUS dos fases (2-B y 4) en el mismo archivo para mantener todo junto.
> Separá con un encabezado ##.

---

# FASE 2-B — Re-ID (galería, ranking, umbral, acceso)

## Decisión 001 — Distancia coseno vs euclidiana

- **Fecha:**
- **Contexto / problema:** Necesito una métrica para comparar embeddings en Re-ID.
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Evidencia / dato que lo respalda:**
- **Posible pregunta de defensa que esto responde:** "¿Por qué distancia coseno y no euclidiana?"

---

## Decisión 002 — Mínimo vs promedio al agregar varias fotos por identidad

- **Fecha:**
- **Contexto / problema:** Una identidad tiene 3-5 fotos en la galería. ¿Cómo agrego sus distancias?
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 003 — Elección del umbral de verificación (ROC/EER)

- **Fecha:**
- **Contexto / problema:** Necesito un umbral de distancia coseno para aceptar/rechazar identidades.
- **Qué elegí (valor del umbral):**
- **Cómo lo determiné (ROC/EER/otro):**
- **Por qué este método y no poner un valor a dedo:**
- **Evidencia / dato que lo respalda:**
- **Posible pregunta de defensa que esto responde:** "¿Cómo y por qué elegiste el umbral de verificación?"

---

# FASE 4 — Traducción multilingüe (LLM)

## Decisión 004 — Pre-generar traducciones offline vs LLM en cada request

- **Fecha:**
- **Contexto / problema:** ¿Debo llamar al LLM en cada request de `/predict` o pre-generar?
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 005 — LLM para normalización de entrada vs traductor literal

- **Fecha:**
- **Contexto / problema:** El usuario puede escribir en inglés, francés, etc.
- **Qué elegí:**
- **Por qué lo elegí:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 006 — NLLB-200 como fallback vs MarianMT / Google Translate

- **Fecha:**
- **Contexto / problema:** El LLM puede fallar; necesito un fallback offline.
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:** "¿Por qué NLLB-200 y no MarianMT?"
