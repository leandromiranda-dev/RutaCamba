# Bitácora de decisiones — Fase 2A — Leandro Miranda

> Completá este archivo a medida que avanzás. Copiaste esta plantilla de `docs/PLANTILLA_decisiones.md`.
> Cada ✍️ en `docs/fases/fase2_reid_leandro.md` es una entrada aquí.

---

## Decisión 001 — ArcFace vs otros modelos de embedding (Facenet, VGG-Face)

- **Fecha:** 11 de junio de 2026
- **Contexto / problema:** Necesito generar embeddings faciales para Re-ID.
- **Qué elegí:** Implementar el modelo ArcFace a través de la interfaz de la librería DeepFace.
- **Por qué lo elegí:** ArcFace utiliza una función de pérdida llamada *Additive Angular Margin Loss*. Esto significa que mapea los rostros en una esfera geométrica donde fuerza a que las fotos de una misma persona se agrupen muy juntas (minimizando la varianza intra-clase) y empuja a las de personas distintas para que se separen lo más posible por un margen angular. Esto lo hace extremadamente robusto contra cambios de iluminación o poses laterales, lo cual es vital para el problema de Re-Identificación.
- **Alternativa(s) que descarté y POR QUÉ no:** - *FaceNet:* Lo descarté porque utiliza *Triplet Loss*. Aunque fue revolucionario, optimizar tripletes es más ineficiente computacionalmente y tiende a estancarse en óptimos locales comparado con el margen angular de ArcFace.
  - *VGG-Face:* Lo descarté por ser una arquitectura más antigua y pesada. Sus embeddings no alcanzan el nivel de discriminación geométrica que necesitamos para separar clústeres complejos.
- **Evidencia / dato que lo respalda:** ArcFace es el estado del arte y supera consistentemente el 99% de precisión en benchmarks estándar de verificación facial como LFW (Labeled Faces in the Wild), superando tanto a FaceNet como a VGG-Face.
- **Posible pregunta de defensa que esto responde:** "¿Por qué ArcFace y no FaceNet?" -> *Respuesta directa:* "Por su función de pérdida de margen angular que logra una mejor separación inter-clase en el espacio latente que el Triplet Loss de FaceNet."

---

## Decisión 002 — Implementación del mAP de re-ID (diferencia con mAP de detección)

- **Fecha:** 11 de junio de 2026
- **Contexto / problema:** La rúbrica pide mAP variante correcta de re-ID.
- **Qué elegí:** Implementar el cálculo manual del *Average Precision* (AP) sobre listas rankeadas por cada *query* usando la métrica de distancia coseno, promediando luego los APs de todas las consultas para obtener el mAP global.
- **Fórmula implementada:** Para cada *query*, se calcula el *Average Precision* usando:
  
  $$AP = \frac{\sum_{k=1}^{n} (P(k) \times rel(k))}{N_{total}}$$
  
  Donde $P(k)$ es la precisión hasta la posición $k$ del ranking, $rel(k)$ es una función indicadora (1 si el resultado en la posición $k$ es de la misma identidad, 0 si no lo es), y $N_{total}$ es el total de imágenes relevantes (de la misma identidad) que existen en la galería. 
  
  Luego, el mAP es el promedio de los AP de todas las consultas:
  
  $$mAP = \frac{1}{Q} \sum_{q=1}^{Q} AP_{q}$$
  
  Siendo $Q$ el número total de *queries*.
- **Por qué difiere del mAP de detección:** El mAP de detección de objetos promedia la precisión sobre distintas clases basándose en el umbral de Intersección sobre Unión (IoU) y calculando el área bajo la curva Precision-Recall. En contraste, el mAP de Re-ID proviene del campo de recuperación de información (Information Retrieval); no trabaja con cajas de detección ni IoU, sino que evalúa la calidad del ordenamiento (ranking) por similitud de características para cada individuo consultado frente a una galería.
- **Alternativa(s) que descarté y POR QUÉ no:** Descarté usar `sklearn.metrics.average_precision_score` de forma ingenua directamente sobre los vectores de características porque esa función está diseñada para problemas de clasificación binaria o multietiqueta estándar, no para evaluar listas de recuperación indexadas dinámicamente por distancias vectoriales.
- **Posible pregunta de defensa que esto responde:** "¿Cómo calculaste el mAP de re-ID y en qué difiere del de detección?"

---

## Decisión 003 — PCA vs t-SNE para visualización

- **Fecha:** 11 de junio de 2026
- **Contexto / problema:** Necesito visualizar el espacio de embeddings en 2D para comprobar si el modelo agrupa correctamente los rostros de la misma persona.
- **Qué elegí:** Utilizar t-SNE (t-Distributed Stochastic Neighbor Embedding) como método principal de visualización.
- **Por qué lo elegí:** t-SNE es un algoritmo de reducción de dimensionalidad no lineal diseñado específicamente para preservar la estructura local de los datos (la vecindad). En el caso de los embeddings de ArcFace, t-SNE logra agrupar visualmente los vectores de la misma persona formando clústeres claros y separados, lo que demuestra que nuestra función de pérdida extrajo características discriminativas correctamente.
- **Alternativa(s) que descarté y POR QUÉ no:** Descarté utilizar únicamente PCA (Principal Component Analysis). Al ser una técnica de proyección lineal enfocada en preservar la varianza global, PCA tiende a colapsar los embeddings complejos de alta dimensionalidad en una nube de puntos superpuestos en 2D, haciendo imposible distinguir la separación real de las identidades.
- **Posible pregunta de defensa que esto responde:** "¿Por qué usaste t-SNE en lugar de PCA para tu visualización?" -> *Respuesta directa:* "Porque PCA es lineal y superpone los datos complejos, mientras que t-SNE es no lineal y preserva las relaciones de vecindad local, permitiendo visualizar claramente los clústeres de cada identidad en el espacio 2D."