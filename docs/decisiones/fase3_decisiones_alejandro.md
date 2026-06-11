# Bitácora de decisiones — Fase 3 — Alejandro Ojeda

> Completá este archivo a medida que avanzás. Cada ✍️ en `docs/fases/fase3_landmarks_alejandro.md` es una entrada aquí.
> El código base ya estaba en `src/model.py` y `src/train.py` — lo que no tenías eran las justificaciones.
> Llenlas acá: son lo que defendés en la oral.

---

## Decisión 001 — 4 bloques convolucionales (supera el mínimo de 3)

- **Fecha:**
- **Contexto / problema:** La rúbrica pide ≥3 capas conv. ¿Cuántas usar?
- **Qué elegí:** 4 bloques Conv→BN→ReLU→MaxPool (32→64→128→256 canales)
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:** 3 bloques (campo receptivo insuficiente), 5+ bloques (overfitting con dataset pequeño)
- **Evidencia / dato que lo respalda:**
- **Posible pregunta de defensa que esto responde:** "¿Por qué 4 bloques y no 3?"

---

## Decisión 002 — AdaptiveAvgPool vs Flatten directo

- **Fecha:**
- **Contexto / problema:** Cómo conectar las features conv a la cabeza FC.
- **Qué elegí:** AdaptiveAvgPool2d(1) → 256
- **Por qué lo elegí:** Reduce 256×14×14 → 256: la FC pasa de ~50M pesos a 33K
- **Alternativa(s) que descarté y POR QUÉ no:** Flatten (dimensión enorme, overfitting)
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 003 — ResNet18 para Transfer Learning (vs VGG16, EfficientNet)

- **Fecha:**
- **Contexto / problema:** ¿Qué backbone usar para Transfer Learning?
- **Qué elegí:** ResNet18 (11.7M parámetros, residual connections)
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:** VGG16 (138M params, FC de 102M, excesivo para 8 clases)
- **Posible pregunta de defensa que esto responde:** "¿Por qué ResNet18 y no VGG16?"

---

## Decisión 004 — Congelar backbone primero, luego fine-tuning

- **Fecha:**
- **Contexto / problema:** ¿Cómo entreno el Transfer Learning?
- **Qué elegí:** (a) Congelar backbone, entrenar solo FC; (b) Descongelar layer4, fine-tuning con lr=1e-4
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:** Entrenar todo desde el principio
- **Posible pregunta de defensa que esto responde:** "¿Por qué congelar el backbone primero?"

---

## Decisión 005 — Checkpoint por menor val loss y no última época

- **Fecha:**
- **Contexto / problema:** ¿Cuándo guardo el mejor modelo?
- **Qué elegí:**
- **Por qué lo elegí:**
- **Alternativa(s) que descarté y POR QUÉ no:**
- **Posible pregunta de defensa que esto responde:**

---

## Decisión 006 — Mitigación del overfitting

- **Fecha:**
- **Contexto / problema:** Dataset pequeño (~800 imágenes), alta probabilidad de overfitting.
- **Qué elegí (lista de técnicas):**
- **Por qué cada una:**
- **Posible pregunta de defensa que esto responde:** "¿Cómo detectaste y mitigaste el overfitting?"
