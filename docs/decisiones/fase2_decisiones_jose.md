# Bitácora de decisiones — Fase 2B + Fase 4 — Jose Alfredo

> Completá este archivo a medida que avanzás. Cada ✍️ en tus `.md` de fase es una entrada aquí.
> Esta bitácora cubre TUS dos fases (2-B y 4) en el mismo archivo para mantener todo junto.
> Separá con un encabezado ##.

---

# FASE 2-B — Re-ID (galería, ranking, umbral, acceso)

## Decisión 001 — Distancia coseno vs euclidiana

- **Fecha:** 2026-06-11
- **Contexto / problema:** Necesito una métrica para comparar embeddings de rostros en Re-ID. El modelo ArcFace de DeepFace produce vectores de alta dimensión que representan identidades faciales.
- **Qué elegí:** Distancia coseno (= 1 − similitud coseno).
- **Por qué lo elegí:** ArcFace fue entrenado explícitamente para que la similitud coseno sea la métrica de comparación correcta. Sus embeddings están **L2-normalizados** (norma = 1), lo que hace que la distancia euclidiana y la distancia coseno sean equivalentes en esa condición. Sin embargo, si hay alguna variación de norma, la coseno es invariante a la magnitud y solo mide el ángulo entre vectores — que es exactamente lo que queremos: ¿apunta el embedding de la selfie hacia la misma dirección que los embeddings de la galería?
- **Alternativa(s) que descarté y POR QUÉ no:** Distancia euclidiana — sensible a la magnitud del vector, por lo que dos embeddings del mismo rostro con distintas normas darían distancias altas aunque el ángulo sea pequeño. Con embeddings L2-normalizados da el mismo resultado que coseno, pero en el caso general es menos robusta.
- **Evidencia / dato que lo respalda:** El paper de ArcFace (Deng et al., 2019) y la documentación de DeepFace indican explícitamente que la métrica de comparación es coseno. `config.REID_DISTANCE = "cosine"` ya lo definió el coordinador.
- **Posible pregunta de defensa que esto responde:** "¿Por qué distancia coseno y no euclidiana para comparar embeddings faciales?"

---

## Decisión 002 — Mínimo vs promedio al agregar varias fotos por identidad

- **Fecha:** 2026-06-11
- **Contexto / problema:** La galería tiene 3–5 fotos por persona. Al comparar un probe contra una identidad, necesito agregar las distancias individuales de cada foto en una sola distancia representativa.
- **Qué elegí:** **Mínimo** (`aggregation="min"`) — la distancia mínima entre el probe y cualquier foto de esa identidad.
- **Por qué lo elegí:** En verificación de identidad, si hay UNA foto que coincide bien con el probe, eso es suficiente para confirmar la identidad. El mínimo captura la "mejor coincidencia posible" con esa persona. Si usara el promedio, una foto de mala calidad (mala iluminación, oclusión parcial) elevaría artificialmente la distancia y podría causar falsos rechazos.
- **Alternativa(s) que descarté y POR QUÉ no:** Promedio — penaliza cuando hay fotos con ruido en la galería. Media ponderada — más compleja sin ganancia demostrada con solo 3–5 fotos.
- **Evidencia / dato que lo respalda:** Práctica estándar en sistemas de verificación face-1:1, donde el "mejor match" es más informativo que el match promedio. Ver sistemas tipo FaceNet y ArcFace en producción.
- **Posible pregunta de defensa que esto responde:** "¿Cómo agregás las distancias cuando hay varias fotos de una misma persona en la galería?"

---

## Decisión 003 — Elección del umbral de verificación (ROC/EER)

- **Fecha:** 2026-06-12 (a completar tras análisis en notebook 02b)
- **Contexto / problema:** Necesito un umbral de distancia coseno para decidir si concedo o deniego el acceso. Si pongo el umbral muy bajo, rechazo personas legítimas (FRR alto). Si lo pongo muy alto, acepto impostores (FAR alto).
- **Qué elegí (valor del umbral):** *Pendiente — se determina en notebook 02b con los datos reales del equipo.*
- **Cómo lo determiné (ROC/EER/otro):** Se generan pares genuinos (misma persona) e impostores (distinta persona), se calculan sus distancias coseno, y se traza la curva ROC. El **Equal Error Rate (EER)** es el punto donde FAR = FRR — el balance justo entre seguridad y usabilidad. Ese valor reemplaza al `0.65` inicial de `config.REID_THRESHOLD`.
- **Por qué este método y no poner un valor a dedo:** El umbral a dedo (ej: 0.5 o 0.65) no tiene respaldo en los datos reales del equipo. El EER es el estándar en sistemas biométricos porque tiene justificación estadística: minimiza el error total. Con ArcFace+coseno el umbral suele rondar 0.6–0.7, pero puede variar con la calidad y diversidad de las fotos del equipo.
- **Evidencia / dato que lo respalda:** *A completar: gráfico de distribuciones intra/inter + curva ROC con el EER marcado, del notebook 02b.*
- **Posible pregunta de defensa que esto responde:** "¿Cómo y por qué elegiste el umbral de verificación? ¿Por qué no pusiste 0.5 a dedo?"

---

# FASE 4 — Traducción multilingüe (LLM)

## Decisión 004 — Pre-generar traducciones offline vs LLM en cada request

- **Fecha:** 2026-06-11
- **Contexto / problema:** El endpoint `/predict` necesita devolver traducciones EN/FR/IT del landmark clasificado. ¿Llamo al LLM en cada request o pre-genero?
- **Qué elegí:** **Pre-generar offline** con `generate_translations.py` (se corre una vez) y guardar en `data/translations.json`. En runtime: lookup O(1).
- **Por qué lo elegí:** (1) Latencia: una llamada a Claude tarda ~2 segundos. Un lookup en dict es instantáneo. (2) Costo: con 8 landmarks × 4 idiomas = 32 pares, el costo de pre-generar es mínimo y fijo. En runtime sería variable y acumulativo. (3) Disponibilidad: el JSON funciona sin internet; el LLM en runtime requiere red. (4) Control de calidad: puedo revisar y corregir las traducciones manualmente antes de la demo.
- **Alternativa(s) que descarté y POR QUÉ no:** LLM en cada request — latencia intolerable para una API de usuario, costo variable, y falla si no hay internet en la demo.
- **Posible pregunta de defensa que esto responde:** "¿Por qué pre-generaste las traducciones en lugar de llamar al LLM en cada request?"

---

## Decisión 005 — LLM para normalización de entrada vs traductor literal

- **Fecha:** 2026-06-11
- **Contexto / problema:** El usuario puede escribir su consulta en inglés, francés, italiano, etc. Necesito convertirla al español para el sistema de clasificación.
- **Qué elegí:** **LLM (Claude)** para `normalize_input`.
- **Por qué lo elegí:** El LLM entiende la **intención semántica**, no solo las palabras. Ejemplo: `"Where is the big Jesus statue?"` → el LLM reconoce que se refiere al "Cristo Redentor" aunque no use ese nombre. Un traductor literal daría `"¿Dónde está la gran estatua de Jesús?"`, que todavía no es el nombre del landmark. El LLM también maneja abreviaciones, errores ortográficos y referencias culturales.
- **Posible pregunta de defensa que esto responde:** "¿Por qué usás un LLM para normalizar la entrada en lugar de un traductor estándar?"

---

## Decisión 006 — NLLB-200 como fallback vs MarianMT / Google Translate

- **Fecha:** 2026-06-11
- **Contexto / problema:** El LLM puede fallar (sin internet, timeout, API caída). Necesito un fallback que funcione sin red y sea razonablemente bueno en múltiples idiomas.
- **Qué elegí:** **NLLB-200 distilled 600M** (Facebook/Meta, HuggingFace).
- **Por qué lo elegí:** (1) **Un solo modelo, 200 idiomas**: NLLB cubre todos los idiomas que un turista podría usar. (2) **Completamente offline**: una vez descargado, no requiere internet. (3) **Carga lazy**: solo se instancia en memoria si el LLM falla, evitando consumir ~600 MB de RAM innecesariamente. (4) **CPU-compatible**: corre en CPU sin GPU (el campo `device=-1`).
- **Alternativa(s) que descarté y POR QUÉ no:** MarianMT — requiere un modelo separado (100–300 MB) por cada par de idiomas (EN→ES, FR→ES, IT→ES, etc.), lo que suma >1 GB y complejidad de carga. Google Translate — requiere internet, no es un verdadero fallback offline.
- **Posible pregunta de defensa que esto responde:** "¿Por qué elegiste NLLB-200 como fallback y no MarianMT o Google Translate?"
