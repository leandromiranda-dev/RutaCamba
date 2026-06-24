# Bitácora de decisiones — Fase 3 (entrenamiento B2) — Jose Alfredo

> Tarea asignada: analizar el código y entrenar el modelo de Transfer Learning
> (ResNet18, "B2"). Esta bitácora registra las decisiones técnicas tomadas para
> dejar B2 entrenado, exportado y evaluado, sin pisar la bitácora de arquitectura
> de Alejandro (`fase3_decisiones_alejandro.md`), que cubre el diseño de B1/B2.
> Todo el detalle narrado está en `ReporteJoseAlfredo.md`.

---

## Decisión 001 — Materializar el split desde Google Drive (y no implementar el ETL de S3)

- **Fecha:** 2026-06-22
- **Contexto / problema:** El entrenamiento necesita las imágenes en
  `data/train|val|test/<clase>/`, pero localmente no existían. El `ETL/etl_s3.py`
  previsto estaba sin implementar y las credenciales AWS del `.env` eran inválidas.
  El dataset real vive en Google Drive (carpeta "Places", organizada por clase).
- **Qué elegí:** Un script nuevo, `scripts/prepare_dataset.py`, que lee
  `data/manifest.csv` y copia cada imagen desde `Places/<clase>/<archivo>` a
  `data/<split>/<clase>/<archivo>`, respetando el split ya definido en el manifest.
- **Por qué lo elegí:** El manifest ya es la fuente de verdad del split estratificado
  70/15/15 (Fase 1). Reusarlo garantiza el mismo split que se usó en el EDA y evita
  re-particionar (que rompería la comparabilidad con resultados previos).
- **Alternativa(s) que descarté y POR QUÉ no:** (a) Implementar el ETL de S3:
  descartado porque el dataset no está en S3 y las credenciales no funcionan;
  (b) re-hacer el split con `ImageFolder`: descartado porque generaría una partición
  distinta y arruinaría la regla de "no solapamiento" y la trazabilidad con el manifest.
- **Evidencia / dato que lo respalda:** Resultado del script: 553 train / 118 val /
  119 test, 8 clases en cada split (coincide exactamente con el manifest).
- **Posible pregunta de defensa que esto responde:** "¿Cómo reconstruiste el dataset
  local y cómo garantizaste que el split es el mismo del EDA?"

---

## Decisión 002 — Entrenar en GPU local usando un entorno virtual dedicado con build CUDA

- **Fecha:** 2026-06-22
- **Contexto / problema:** El entrenamiento debía correr en la GPU del equipo
  (NVIDIA RTX 4050). El intérprete inicial tenía `torch` solo-CPU y el entorno
  virtual del proyecto estaba vacío.
- **Qué elegí:** Instalar en el venv `envDeepLearning` (Python 3.10) las ruedas
  `torch 2.9.0+cu128` y `torchvision 0.24.0+cu128` (compatibles con el driver
  CUDA 12.9), más `wandb`, `scikit-learn` y `matplotlib`.
- **Por qué lo elegí:** La build `+cu128` habilita el cómputo en GPU; aislar las
  dependencias en el venv evita contaminar el Python global y deja el entorno
  reproducible. La RTX 4050 reduce el tiempo de entrenamiento de ~20 min (CPU) a
  pocos minutos.
- **Alternativa(s) que descarté y POR QUÉ no:** (a) Entrenar en CPU: descartado por
  lento; (b) instalar en el Python global: descartado por falta de aislamiento y
  riesgo de conflictos de versiones con otras tareas.
- **Evidencia / dato que lo respalda:** `torch.cuda.is_available() == True`, GPU
  detectada como "NVIDIA GeForce RTX 4050 Laptop GPU", `torch 2.9.0+cu128`.
- **Posible pregunta de defensa que esto responde:** "¿En qué hardware entrenaste y
  cómo configuraste el entorno?"

---

## Decisión 003 — Implementar el fine-tuning de dos fases en el loop de entrenamiento

- **Fecha:** 2026-06-22
- **Contexto / problema:** El loop `src/landmarks/train.py`, con `--model transfer`,
  entrenaba únicamente la capa FC con el backbone congelado: nunca descongelaba
  `layer4`. Con el backbone 100 % congelado, B2 no podía aprovechar el fine-tuning
  y difícilmente superaría a B1.
- **Qué elegí:** Agregar el flag `--finetune-layer4` (con `--freeze-epochs` y
  `--finetune-lr`). Al llegar a `freeze_epochs + 1`, se llama a `unfreeze_layer4()`,
  se crea un optimizador nuevo (layer4 + FC, `lr=1e-4`) y se recrea el scheduler.
  Por defecto, `freeze_epochs = epochs // 2`.
- **Por qué lo elegí:** Es la estrategia de dos fases que justifica Alejandro en su
  Decisión 004 (congelar para estabilizar la FC, luego afinar layer4 con lr bajo).
  Faltaba la implementación en el loop; este flag la habilita de forma reproducible
  por línea de comandos y deja la fase (a) y (b) trazables en los logs.
- **Alternativa(s) que descarté y POR QUÉ no:** (a) Hacer el fine-tuning solo en el
  notebook: descartado porque no queda reproducible por comando ni registrado igual
  en WandB; (b) descongelar todo el backbone: descartado por riesgo de destruir los
  pesos preentrenados con un dataset chico.
- **Evidencia / dato que lo respalda:** Al descongelar `layer4` en la época 8, el
  val accuracy saltó de 88.98 % a 97.46 %, llegando a 99.15 % al final.
- **Posible pregunta de defensa que esto responde:** "¿Cómo implementaste las dos
  fases del transfer learning y qué efecto tuvo descongelar layer4?"

---

## Decisión 004 — Exportar el TorchScript desde una copia en CPU

- **Fecha:** 2026-06-22
- **Contexto / problema:** Al entrenar en GPU, `export_torchscript` fallaba en la
  prueba de carga: el tensor de prueba estaba en CPU y los pesos en CUDA
  (`Input type (torch.FloatTensor) and weight type (torch.cuda.FloatTensor) should
  be the same`). El bug solo aparecía en GPU.
- **Qué elegí:** Exportar desde una copia en CPU (`torch.jit.script(model.cpu())`)
  y correr la verificación en el mismo device del modelo recargado.
- **Por qué lo elegí:** Un `.pt` exportado en CPU es portable: la API puede cargarlo
  en una máquina sin GPU. Además, alinear el device del tensor de prueba con el del
  modelo elimina el error de raíz.
- **Alternativa(s) que descarté y POR QUÉ no:** Mover solo el tensor de prueba a CUDA:
  funcionaría, pero ataría el `.pt` a GPU y restaría portabilidad para el despliegue.
- **Evidencia / dato que lo respalda:** Tras el arreglo, el modelo recargado en CPU
  devuelve salida `(1, 8)` sin error.
- **Posible pregunta de defensa que esto responde:** "¿Por qué exportar el modelo en
  CPU y no en GPU?"

---

## Decisión 005 — Corregir la entity de WandB

- **Fecha:** 2026-06-22
- **Contexto / problema:** El primer intento de entrenamiento abortó al iniciar
  WandB: `entity lozadaleonn not found during upsertBucket`. El `.env` tenía
  `WANDB_ENTITY=lozadaleonn`, que no existe.
- **Qué elegí:** Corregir a `WANDB_ENTITY=lozadaleonn-ciencialink`, la entity real
  del equipo (la misma del run previo de B1).
- **Por qué lo elegí:** Es la entity donde está el proyecto `rutacamba`; sin ella,
  todo el tracking falla antes de empezar a entrenar.
- **Alternativa(s) que descarté y POR QUÉ no:** Entrenar con WandB desactivado:
  descartado porque la rúbrica exige el registro de experimentos en WandB.
- **Evidencia / dato que lo respalda:** El run posterior sincronizó correctamente
  (`Currently logged in as: lozadaleonn (lozadaleonn-ciencialink)`).
- **Posible pregunta de defensa que esto responde:** "¿Dónde quedó registrado el
  entrenamiento?"

---

## Decisión 006 — Para la comparativa, descargar el B1 real (no re-entrenarlo)

- **Fecha:** 2026-06-22
- **Contexto / problema:** Para la tabla comparativa B1 vs B2 hacía falta el modelo
  B1 real (91.53 %). El `models/cnn_scratch.pt` local era un placeholder de prueba,
  no el modelo entrenado. El loop de entrenamiento no fija semilla, así que
  re-entrenar B1 daría un valor distinto del 91.53 % registrado.
- **Qué elegí:** Descargar el B1 real desde su artifact de WandB
  (`best-cnn:v0`, run `g3630v5v`) y usar ese `.pt` para evaluar.
- **Por qué lo elegí:** Garantiza que la comparación use exactamente el modelo cuyo
  resultado figura en el informe, sin introducir varianza por re-entrenamiento.
- **Alternativa(s) que descarté y POR QUÉ no:** Re-entrenar B1 localmente: descartado
  porque, sin semilla fija y con hardware distinto, no reproduce el 91.53 % exacto y
  generaría una comparación inconsistente con lo ya reportado.
- **Evidencia / dato que lo respalda:** El run `g3630v5v` reporta `val/acc = 0.9153`;
  el artifact `best-cnn:v0` contiene `cnn_scratch.pt`.
- **Posible pregunta de defensa que esto responde:** "¿El B1 con el que comparaste es
  el mismo del informe? ¿Por qué no lo re-entrenaste?"

---

## Decisión 007 — Evaluación final en test una sola vez (métricas + matriz de confusión)

- **Fecha:** 2026-06-22
- **Contexto / problema:** La rúbrica exige una evaluación final sobre el test set,
  que se toca **una sola vez**, con métricas más allá del accuracy.
- **Qué elegí:** Un script de evaluación (`scripts/evaluate_test.py`) que corre ambos
  modelos sobre el test (119 imágenes) y reporta accuracy, precision/recall/F1
  (macro), reporte por clase y matriz de confusión (PNG), más la tabla comparativa.
- **Por qué lo elegí:** Centraliza la evaluación en un único paso reproducible que no
  vuelve a tocar el test; las métricas macro y la matriz de confusión muestran el
  desempeño por clase (no solo el global), clave con clases desbalanceadas.
- **Alternativa(s) que descarté y POR QUÉ no:** Reportar solo accuracy global:
  descartado porque oculta el comportamiento por clase y el desbalance.
- **Evidencia / dato que lo respalda:** B1 test acc 90.76 % (≈ val 91.53 %, sin
  overfitting); B2 test acc 100 % en las 8 clases. Salidas en `docs/eval/`.
- **Posible pregunta de defensa que esto responde:** "¿Cómo evaluaste el modelo final
  y por qué reportás precision/recall y matriz de confusión además del accuracy?"

---

## Decisión 008 — Arquitectura B3: SE-CNN (Squeeze-and-Excitation)

- **Fecha:** 2026-06-23
- **Contexto / problema:** Explorar si agregar un mecanismo de atención de canal
  sobre la arquitectura base B1 mejora la precisión sin aumentar significativamente
  el tamaño del modelo ni el costo computacional.
- **Qué elegí:** `TuristSECNN` — mismos 4 bloques conv (32→64→128→256) que B1, pero
  con un módulo `SEBlock` (Squeeze-and-Excitation) al final de cada bloque. El SE
  comprime espacialmente cada canal a un escalar (squeeze), aprende un vector de
  importancia por canal con dos FC (excitation), y reescala el feature map.
  Reduction ratio = 8 (hidden = channels/8). 30 épocas, mismos hiperparámetros que B1.
- **Por qué lo elegí:** Costo adicional mínimo (~5 % más parámetros: 444K vs 423K,
  mismo tamaño de archivo ~1.9 MB), pero el SE permite que la red enfoque los
  canales más discriminativos por clase. Con dataset chico, este tipo de atención
  liviana suele rendir mejor que agregar profundidad.
- **Alternativa(s) que descarté y POR QUÉ no:** (a) CBAM (atención espacial + canal):
  más costoso y con más hiperparámetros, no justificado con 790 imágenes; (b) solo
  atención espacial: el dataset tiene landmarks visualmente muy distintos, la
  variabilidad relevante está más en los canales que en la posición.
- **Evidencia / dato que lo respalda:** Val acc 92.37 %, test acc **92.44 %**
  (supera B1 90.76 %), F1 macro 91.24 %. El SE mejora especialmente ParqueUrbano
  (recall 92 % vs 83 % en B1) y elimina errores en CatedralMunicipal y Ventura.
  WandB run `wbay2jxu`.
- **Posible pregunta de defensa que esto responde:** "¿Qué ganás con el SE frente
  a B1 y qué coste tiene?"

---

## Decisión 009 — Arquitectura BA: ResNet-lite (bloques residuales desde cero)

- **Fecha:** 2026-06-23
- **Contexto / problema:** Evaluar si incorporar skip connections en una CNN desde
  cero mejora el rendimiento sobre B1, usando una arquitectura estilo miniResNet
  con stem 7×7 y 3 bloques residuales.
- **Qué elegí:** `TuristResNet` — stem Conv7×7 (stride=2) + MaxPool → ResBlock(64→64)
  → ResBlock(64→128, stride=2) → ResBlock(128→256, stride=2) → GlobalAvgPool →
  FC(256→128→8). 1,266,632 parámetros. 30 épocas, mismos hiperparámetros.
- **Por qué lo elegí:** Las skip connections permiten gradientes más directos y
  redes más profundas sin degradación; es la justificación teórica estándar de
  ResNet. Quería medir si ese beneficio se materializa con un dataset chico (553 imgs).
- **Alternativa(s) que descarté y POR QUÉ no:** (a) Usar 4 ResBlocks: mayor profundidad
  pero más riesgo de sobreajuste con tan pocas imágenes; (b) ResBlock sin stride
  (usar MaxPool): descartado por aumentar innecesariamente el mapa de activación.
- **Evidencia / dato que lo respalda:** Val acc 92.37 % pero test acc **87.39 %**
  (debajo de B1 90.76 %). La brecha val/test (4.98 pp) indica sobreajuste moderado:
  1.26M parámetros es demasiado para 553 imágenes. El stem 7×7 con stride=2 pierde
  resolución temprana, lo que puede perjudicar clases con detalles finos (Tahuichi
  73 % recall). WandB run `3i5ickz4`.
- **Posible pregunta de defensa que esto responde:** "¿Por qué ResNet-lite no supera
  a B1 si tiene skip connections? ¿Cuándo ayuda la profundidad y cuándo no?"

---

## Nota de honestidad para la defensa

El 100 % de B2 en test es real (el test se mantuvo separado y el dataset se purgó de
near-duplicates en Fase 1), pero **no debe interpretarse como infalibilidad**: el
test es chico (119 imágenes) y los landmarks son visualmente muy distintos, por lo
que un backbone preentrenado los separa con holgura. Con un dataset mayor y
condiciones más variadas, el accuracy bajaría algo.
