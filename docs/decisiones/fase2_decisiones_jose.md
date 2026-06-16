# Bitácora de decisiones — Fase 2B + Fase 4 — Jose Alfredo

> Completá este archivo a medida que avanzás. Cada ✍️ en tus `.md` de fase es una entrada aquí.
> Esta bitácora cubre TUS dos fases (2-B y 4) en el mismo archivo para mantener todo junto.
> Separá con un encabezado ##.

---

# FASE 2-B — Re-ID (galería, ranking, umbral, acceso)

## Decisión 001 — Distancia coseno vs euclidiana

- **Fecha:** 2026-06-12
- **Contexto / problema:** Necesito una métrica para comparar embeddings en Re-ID.
- **Qué elegí:** Distancia coseno (`1 - cos(a, b)`).
- **Por qué lo elegí:** ArcFace entrena con *Additive Angular Margin Loss*, que maximiza el
  ángulo (no la distancia euclidiana) entre clases en el espacio de embeddings. La métrica
  natural de ese espacio es el coseno. DeepFace y `config.REID_DISTANCE` también lo especifican
  así. Con ArcFace, pares genuinos rondan dist ≈ 0.1–0.4 e impostores ≈ 0.6–1.0,
  dando separación clara.
- **Alternativa(s) que descarté y POR QUÉ no:** Euclidiana — depende de la magnitud del vector.
  Si los embeddings no están perfectamente normalizados, la escala domina sobre la dirección.
  Con ArcFace la dirección es todo; la magnitud no es informativa.
- **Evidencia / dato que lo respalda:** Papers de ArcFace (Deng et al. 2019) y la propia
  documentación de DeepFace usan cosine distance como métrica estándar.
- **Posible pregunta de defensa que esto responde:** "¿Por qué distancia coseno y no euclidiana?"

---

## Decisión 002 — Mínimo vs promedio al agregar varias fotos por identidad

- **Fecha:** 2026-06-12
- **Contexto / problema:** Una identidad tiene 3–5 fotos en la galería. ¿Cómo agrego sus distancias?
- **Qué elegí:** **Mínima distancia** (best-match): la identidad queda representada
  por su foto más cercana al probe.
- **Por qué lo elegí:** Si al menos UNA foto de la galería coincide bien con la selfie,
  la persona está físicamente presente. El promedio castigaría casos donde el sujeto tiene
  fotos de distintos ángulos o iluminaciones — el promedio bajaría la similitud aunque
  haya una coincidencia perfecta. Con min se maximiza la chance de reconocer correctamente.
- **Alternativa(s) que descarté y POR QUÉ no:** Promedio — más sensible a ruido (fotos borrosas
  o mal encuadradas elevan la distancia promedio aunque la persona sea la misma).
  Centroide del espacio de embeddings — requiere más fotos para ser estable; con 3–5 fotos
  el centroide puede estar lejos de cualquier foto real.
- **Posible pregunta de defensa que esto responde:** "¿Cómo manejás que una persona tiene
  múltiples fotos en la galería?"

---

## Decisión 003 — Elección del umbral de verificación (ROC/EER)

- **Fecha:** 2026-06-13
- **Contexto / problema:** Necesito un umbral de distancia coseno para aceptar/rechazar identidades.
- **Qué elegí (valor del umbral):** 0.65 como punto de partida (de `config.REID_THRESHOLD`),
  a refinar con ROC/EER en el notebook `02b_reid_ranking_metrics.ipynb` una vez que se
  cuente con la galería real de pares genuinos/impostores del equipo.
- **Cómo lo determiné (ROC/EER/otro):** En el notebook se generan distribuciones de distancias
  intra-clase (misma persona, distintas fotos) e inter-clase (personas distintas). Se grafica
  la curva ROC y se elige el punto donde FPR = FNR (Equal Error Rate). Ese valor
  reemplaza al 0.65 provisional en `config.REID_THRESHOLD`.
- **Por qué este método y no poner un valor a dedo:** EER garantiza que la tasa de falsos
  aceptos (impostores que pasan) es igual a la de falsos rechazos (personas legítimas bloqueadas).
  Con ArcFace+coseno el umbral real suele rondar 0.6–0.7, por eso 0.65 es razonable como
  arranque, pero sin datos reales es solo una estimación.
- **Evidencia / dato que lo respalda:** Ver gráficas de distribución y curva ROC en `02b`.
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
