# Bitácora de decisiones — Fase 1 — Diego Lewenstein

> Completado en base al EDA del notebook `notebooks/01_datos_eda.ipynb`.
> Dataset final: 790 imágenes · 8 clases · split 70/15/15 (train=553, val=118, test=119).

---

## Decisión 001 — Split estratificado vs submuestreo al mínimo

- **Fecha:** 2026-06-16
- **Contexto / problema:** Necesito partir el dataset en train/val/test sin sesgo
  por clase. El dataset tiene desbalance moderado (ratio 2.82x entre clase
  mayoritaria Ventura=172 y minoritaria CatedralMunicipal=61).
- **Qué elegí:** Split estratificado 70/15/15 con `train_test_split(stratify=y)`
  de scikit-learn, preservando la distribución original de clases en cada
  subconjunto. Resultado: train=553, val=118, test=119, sin solapamiento de
  imágenes entre splits.
- **Por qué lo elegí:** Garantiza que cada clase tenga representación proporcional
  en los tres subconjuntos, evitando que una clase quede ausente o subrepresentada
  en validación/test. Con solo 61 imágenes en la clase más pequeña, un split
  aleatorio podría dejar 0 ejemplos de esa clase en val o test.
- **Alternativa(s) que descarté y POR QUÉ no:** Submuestreo al mínimo (igualar
  todas las clases a 61 imágenes) descartaría ~470 imágenes válidas, reduciendo
  artificialmente el dataset de 790 a 488. Se pierde información real sin
  necesidad: el desbalance 2.82x es moderado y se corrige mejor en el sampler
  durante el entrenamiento.
- **Evidencia / dato que lo respalda:** CV = 0.42, entropía normalizada = 0.97
  (distribución casi uniforme). El split estratificado replica esa distribución
  en cada subconjunto. Ver `eda_distribucion.png`.
- **Posible pregunta de defensa que esto responde:** "¿Por qué usaste split
  estratificado?" / "¿Por qué no balanceaste las clases antes del split?"

---

## Decisión 002 — Augmentation moderado vs agresivo

- **Fecha:** 2026-06-16
- **Contexto / problema:** Debo aplicar augmentation en train para evitar
  overfitting con un dataset pequeño (553 imágenes de entrenamiento).
- **Qué elegí:** Augmentation moderado verificado visualmente:
  `RandomCrop(224)` + `HFlip(p=0.5)` + `Rotation(±10°)` + `ColorJitter(0.2)`.
  Val/Test solo reciben `CenterCrop(224)` sin augmentation.
- **Por qué lo elegí:** Los landmarks son objetos con geometría característica
  (monumentos, arquitectura). Augmentation agresivo (rotaciones grandes, flips
  verticales, distorsiones de perspectiva) destruye las claves visuales que el
  modelo debe aprender: si el Cristo Redentor aparece boca abajo o con colores
  invertidos, la augmentation introduce ruido en lugar de variabilidad útil.
  La verificación visual en `eda_augmentation.png` confirmó que el augmentation
  moderado mantiene el monumento reconocible.
- **Alternativa(s) que descarté y POR QUÉ no:** Augmentation agresivo (rotaciones
  ±45°, flips verticales, elastic transforms) descartado porque deformaría la
  geometría de los monumentos, que es la principal señal discriminativa entre
  clases. El modelo aprendería variantes artificiales que no existen en val/test.
- **Evidencia / dato que lo respalda:** Inspección visual del pipeline en el
  notebook. Ver `eda_augmentation.png` con ejemplos de imágenes augmentadas.
- **Posible pregunta de defensa que esto responde:** "¿Por qué augmentation
  moderado y no agresivo para landmarks?"

---

## Decisión 003 — Proporción 70/15/15

- **Fecha:** 2026-06-16
- **Contexto / problema:** ¿Qué proporción usar para train/val/test con un
  dataset de 790 imágenes?
- **Qué elegí:** 70/15/15 → train=553, val=118, test=119.
- **Por qué lo elegí:** Con 790 imágenes, la proporción clásica 80/10/10 dejaría
  solo 79 imágenes de test (~9-10 por clase), con alta varianza estadística.
  El 70/15/15 da 118-119 imágenes de val y test (~14-15 por clase), suficiente
  para estimaciones más estables del accuracy por clase. La clase más pequeña
  (CatedralMunicipal=61) queda con ~9 imágenes en val/test — ya es el límite
  inferior aceptable; reducirlo más aumentaría la varianza de la métrica de esa clase.
- **Alternativa(s) que descarté y POR QUÉ no:** 80/10/10 descartado por dejar
  val y test con muy pocas imágenes por clase (riesgo de alta varianza en métricas).
  60/20/20 descartado porque reduce el train a ~474 imágenes, penalizando
  más al modelo que al conjunto de evaluación.
- **Evidencia / dato que lo respalda:** Clase minoritaria CatedralMunicipal=61:
  con 70/15/15 quedan ~9 imgs en val y ~9 en test. Con 80/10/10 quedarían ~6 en cada
  uno, demasiado pocas para métricas confiables.
- **Posible pregunta de defensa que esto responde:** "¿Por qué 70/15/15 y no
  80/10/10?" / "¿Cómo manejaste la clase con pocas imágenes?"

---

## Decisión 004 — Manejo del desbalance de clases

- **Fecha:** 2026-06-16
- **Contexto / problema:** Ratio mayoritaria/minoritaria = 2.82x (Ventura=172
  vs CatedralMunicipal=61). Sin corrección, el modelo tendería a predecir siempre
  las clases mayoritarias, maximizando accuracy global pero fallando en las
  minoritarias.
- **Qué elegí:** `WeightedRandomSampler` en el DataLoader de entrenamiento
  (pesos inversos a la frecuencia de clase, guardados en `class_weights.json`).
  Como alternativa aplicable también a la loss: `class_weight` en
  `CrossEntropyLoss`. Reportar métricas por clase (precision, recall, F1 macro)
  además de accuracy global.
- **Por qué lo elegí:** El sampler rebalancea el muestreo en cada epoch sin
  descartar datos ni duplicar físicamente imágenes. Los pesos en `class_weights.json`
  son el contrato con la Fase 3 (entrenamiento): quien entrene puede elegir usar
  el sampler, la loss pesada, o ambos. El desbalance 2.82x es suficiente para
  afectar el recall de la clase minoritaria sin corrección.
- **Alternativa(s) que descarté y POR QUÉ no:** Oversampling físico (duplicar
  imágenes de clases pequeñas) descartado porque introduce copias exactas que
  aumentan el riesgo de overfitting en esas clases. Ignorar el desbalance
  descartado: con ratio 2.82x, el modelo sin corrección podría alcanzar ~70%
  accuracy prediciendo solo las clases más frecuentes.
- **Evidencia / dato que lo respalda:** Distribución en `eda_distribucion.png`.
  Pesos calculados como `N_total / (N_clases × N_clase_i)` y guardados en
  `data/class_weights.json`.
- **Posible pregunta de defensa que esto responde:** "¿Cómo manejaste el
  desbalance?" / "¿Por qué no usaste oversampling?"

---

## Decisión 005 — Corrección EXIF + Resize(256)→CenterCrop(224) + purga de near-duplicates

- **Fecha:** 2026-06-16
- **Contexto / problema (EXIF):** El EDA visual detectó imágenes cargadas
  "acostadas" (rotadas 90°) en las clases Cristo y DunasArena. PIL por defecto
  ignora la metadata EXIF de orientación, cargando el tensor sin rotar.
- **Qué elegí (EXIF):** Aplicar `ImageOps.exif_transpose()` en el loader antes
  de cualquier transform. Tras la corrección: 429 vertical / 341 horizontal /
  20 cuadrada. Se implementa en `src/data/dataset.py`.
- **Alternativa EXIF descartada:** No corregir y dejar que el modelo aprenda
  ambas orientaciones vía augmentation. Descartado porque contamina el espacio
  de representación: el modelo gastaría capacidad en aprender invarianza de
  orientación en lugar de features del monumento.

- **Contexto / problema (crop):** Las imágenes tienen aspect-ratios variados
  (0.47 a 2.06). Hacer `Resize(224, 224)` directo deforma la geometría.
- **Qué elegí (crop):** `Resize(256)→CenterCrop(224)` estándar ImageNet,
  compatible con los pesos pre-entrenados de ResNet18/EfficientNet que usará
  la Fase 3. Todas las imágenes son ≥366 px → el resize siempre reduce, nunca
  hace upscaling.
- **Alternativa crop descartada:** `Resize(224, 224)` forzado descartado porque
  deforma la geometría del monumento (un Cristo Redentor estirado horizontalmente
  podría ser indistinguible de otra arquitectura). Limitación asumida con
  CenterCrop: en aspect-ratios extremos se descartan los bordes.

- **Contexto / problema (near-duplicates):** El dataset crudo podía contener
  fotos casi idénticas del mismo monumento (fotos en ráfaga, scraping repetido),
  lo que causaría data leakage si una imagen casi idéntica quedara en train y
  en test.
- **Qué elegí (near-duplicates):** Purga por perceptual hash (pHash) con umbral
  de similitud. Las imágenes duplicadas o casi idénticas se eliminaron antes del
  split. El dataset final de 790 imágenes ya está purgado.
- **Alternativa near-duplicates descartada:** No purgar y confiar en que el split
  aleatorio separe los duplicados. Descartado: con split por índice sin control,
  un duplicado casi-exacto puede caer en train y en test simultáneamente,
  inflando artificialmente las métricas de test.
- **Posible pregunta de defensa que esto responde:** "¿Cómo garantizaste que
  train y test son independientes?" / "¿Por qué usaste CenterCrop y no resize
  directo?" / "¿Qué pasa si PIL no lee bien la orientación de la foto?"
