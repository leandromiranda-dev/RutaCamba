# context.md — Cerebro del proyecto "RutaCamba"

> **Para el asistente de código:** leé este archivo COMPLETO antes de hacer nada.
> Te da el contexto del proyecto entero. Cuando el usuario te diga *"me tocó la
> Fase X y me llamo Y"*, andá a la **tabla de enrutamiento** (más abajo), abrí el
> `.md` que te indica y seguí ESE archivo paso a paso. No trabajes fuera de las
> carpetas que tu `.md` te asigna: el proyecto está diseñado para que cada persona
> trabaje en su espacio y luego todo se una sin conflictos de merge.

---

## 1. Qué estamos construyendo

Somos el equipo de ML del proyecto **"RutaCamba"**, un sistema de asistencia turística
inteligente para la ciudad de Santa Cruz de la Sierra, Bolivia. Dado que un turista
sube la foto de un lugar, el sistema:

1. **Verifica la identidad** del usuario (Re-ID con DeepFace/ArcFace) como control de
   acceso.
2. Si hay acceso, **clasifica el landmark** de Santa Cruz (ej: Cristo Redentor, El
   Fuerte de Samaipata, Parque El Arenal) entre 8 clases predefinidas.
3. Entrega la respuesta **traducida a inglés, francés e italiano** usando un LLM.
4. Todo el entrenamiento queda registrado en **WandB** (experiment tracking).
5. Se sirve todo por una **API FastAPI + interfaz Gradio**.

El flujo end-to-end que hay que demostrar:

```
1. Usuario declara identidad + sube selfie  → Módulo A (Re-ID) decide acceso
2. Si hay acceso, sube foto de un lugar      → Módulo B clasifica el landmark (top-k)
3. La respuesta (nombre + descripción)       → Módulo C la traduce a EN/FR/IT
4. Todo el entrenamiento quedó en WandB       → Módulo D
5. Todo se sirve por una API + interfaz       → Módulo E
```

**Stack:** Python, PyTorch, torchvision, DeepFace (Re-ID), FastAPI, Gradio,
WandB, Claude API (traducción), boto3 (S3 para dataset).

**Meta de nota:** 100 pts. El 40% es informe + video + defensa, así que **no basta
con que el código funcione: cada quien tiene que entender y poder defender su parte.**

---

## 2. Las 7 fases, quién las hace y cuánto valen

| Fase | Tema | Responsable(s) | Puntos |
|------|------|----------------|--------|
| 1 | Datos y preprocesamiento | Diego Lewenstein | 10 |
| 2 | Verificación de identidad (Re-ID) | Jose Alfredo **+** Leandro Miranda | 15 |
| 3 | Clasificación de landmarks (CNN) | Alejandro Ojeda | 20 |
| 4 | Traducción multilingüe (LLM) | Jose Alfredo | 5 |
| 5 | Experiment tracking (WandB) | Nicole Lozada | 5 |
| 6 | Despliegue (API + interfaz) | Nicole Lozada | 5 |
| 7 | Informe, video y defensa | Nicole Lozada (coordina, todos aportan) | 40 |

---

## 3. 🧭 TABLA DE ENRUTAMIENTO (leé esto y andá a tu `.md`)

Buscá tu nombre. Abrí el archivo indicado y seguilo. Ese archivo te dice TODO:
qué carpeta es tuya, el paso a paso, y dónde documentar tus decisiones.

| Si te llamás… | y te tocó… | abrí este archivo |
|---------------|-----------|-------------------|
| **Diego Lewenstein** | Fase 1 — Datos | `docs/fases/fase1_datos_diego.md` |
| **Leandro Miranda** | Fase 2 — Re-ID (parte A: embeddings y métricas) | `docs/fases/fase2_reid_leandro.md` |
| **Jose Alfredo** | Fase 2 — Re-ID (parte B: galería, ranking y acceso) | `docs/fases/fase2_reid_jose.md` |
| **Alejandro Ojeda** | Fase 3 — Landmarks (CNN desde cero + Transfer Learning) | `docs/fases/fase3_landmarks_alejandro.md` |
| **Jose Alfredo** | Fase 4 — Traducción LLM | `docs/fases/fase4_llm_jose.md` |
| **Nicole Lozada** | Fase 5 — WandB | `docs/fases/fase5_wandb_nicole.md` |
| **Nicole Lozada** | Fase 6 — Despliegue | `docs/fases/fase6_deploy_nicole.md` |
| **Nicole Lozada** | Fase 7 — Informe | `docs/fases/fase7_informe_nicole.md` |

> Jose tiene dos fases (2-B y 4) y Nicole tres (5, 6, 7). Si sos uno de ellos,
> trabajá una fase a la vez y abrí el `.md` de la fase en la que estés ahora.

---

## 4. Mapa de carpetas — quién es dueño de qué

**Regla de oro para mergear sin conflictos: cada archivo tiene UN solo dueño.**
Nunca edites un archivo de otra fase. Si necesitás algo de otra fase, usalo a
través de su interfaz pública (ver `docs/interfaces/contratos.md`).

```
RutaCamba/
├── context.md                      ← ESTE archivo (congelado, no editar)
├── README.md                       ← Nicole (Fase 7) lo arma al final
├── .gitignore                      ← congelado
├── requirements/                   ← cada fase trae el suyo (sin conflicto)
│   ├── fase1.txt  fase2.txt  fase3.txt  fase4.txt  fase5.txt  fase6.txt
│
├── docs/
│   ├── interfaces/contratos.md     ← CONTRATO de funciones (congelado, clave)
│   ├── PLANTILLA_decisiones.md     ← plantilla para tu bitácora
│   ├── fases/                      ← un .md de tareas por persona-fase
│   │   ├── fase1_datos_diego.md
│   │   ├── fase2_reid_leandro.md
│   │   ├── fase2_reid_jose.md
│   │   ├── fase3_landmarks_alejandro.md
│   │   ├── fase4_llm_jose.md
│   │   ├── fase5_wandb_nicole.md
│   │   ├── fase6_deploy_nicole.md
│   │   └── fase7_informe_nicole.md
│   └── decisiones/                 ← tu bitácora de decisiones va acá
│       ├── fase1_decisiones_diego.md
│       ├── fase2_decisiones_leandro.md
│       ├── fase2_decisiones_jose.md
│       ├── fase3_decisiones_alejandro.md
│       ├── fase4_decisiones_jose.md
│       ├── fase5_decisiones_nicole.md
│       └── fase6_decisiones_nicole.md
│
├── notebooks/
│   ├── 01_datos_eda.ipynb               ← Diego
│   ├── 02a_reid_embeddings.ipynb        ← Leandro
│   ├── 02b_reid_ranking_metrics.ipynb   ← Jose
│   ├── 03_cnn_scratch.ipynb             ← Alejandro
│   └── 04_transfer_learning.ipynb       ← Alejandro
│
├── src/
│   ├── __init__.py
│   ├── config.py                   ← CONTRATO compartido (congelado)
│   ├── data/                       ← Diego  (Fase 1)
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── transforms.py
│   │   └── dataloaders.py
│   ├── reid/
│   │   ├── __init__.py
│   │   ├── embeddings.py           ← Leandro (Fase 2-A)
│   │   ├── metrics.py              ← Leandro (Fase 2-A)
│   │   ├── gallery.py              ← Jose    (Fase 2-B)
│   │   ├── ranking.py              ← Jose    (Fase 2-B)
│   │   └── access.py               ← Jose    (Fase 2-B)
│   ├── landmarks/                  ← Alejandro (Fase 3)
│   │   ├── __init__.py
│   │   ├── cnn.py                  ← TuristCNN (ya existe en src/model.py → se migra acá)
│   │   ├── transfer.py
│   │   ├── train.py                ← loop de entrenamiento (ya existe en src/train.py → se migra)
│   │   └── predictor.py
│   ├── translation/                ← Jose (Fase 4)
│   │   ├── __init__.py
│   │   └── translate.py
│   └── tracking/                   ← Nicole (Fase 5)
│       ├── __init__.py
│       └── wandb_utils.py
│
├── ETL/                            ← Diego (Fase 1)
│   └── etl_s3.py
├── api/                            ← Nicole (Fase 6)
│   └── main.py
├── ui/                             ← Nicole (Fase 6)
│   └── app.py
├── scripts/                        ← generate_translations.py (Jose) · download_models.py (Nicole)
├── models/                         ← .pt exportados (gitignored)
└── data/                           ← dataset reconstruido + translations.json (gitignored)
    ├── train/
    ├── val/
    ├── test/
    └── gallery/
```

> **Nota sobre código existente:** en `src/` ya existen `model.py` y `train.py`
> (raíz de src). Alejandro (Fase 3) debe migrar ese contenido a
> `src/landmarks/cnn.py` y `src/landmarks/train.py` respectivamente. Los archivos
> originales se conservan temporalmente para referencia.

---

## 5. Cómo trabajamos con Git (todos en un repo, cada uno en su rama)

**Setup inicial (lo hace el coordinador UNA vez, antes de que todos arranquen):**
crear el repo con esta estructura, `src/config.py`, `.gitignore`,
`docs/interfaces/contratos.md` y los `docs/`, y subirlo a `main`. Recién ahí cada
quien crea su rama. Esto evita que cinco personas creen el esqueleto y choquen.

**Cada persona:**
1. `git checkout main && git pull`
2. Creá tu rama: `git checkout -b faseX-tema-tunombre`
   (ej: `fase1-datos-diego`, `fase2-reid-leandro`, `fase3-landmarks-alejandro`).
3. Trabajá **solo** en tus carpetas/archivos (los que dice tu `.md`).
4. Documentá cada decisión en tu bitácora `docs/decisiones/` (obligatorio).
5. Commits chicos y descriptivos. `git push -u origin tu-rama`.
6. Cuando termines, abrí un Pull Request hacia `develop` (rama de integración).

**Integración:** se mergea todo a `develop`, se prueba el flujo end-to-end, y
recién cuando funciona se mergea `develop → main`. Como cada quien tocó archivos
distintos y respetó los contratos, el merge es casi sin conflictos.

**Lo único compartido** (no lo edites en tu rama sin avisar):
`src/config.py`, `context.md`, `docs/interfaces/contratos.md`, `README.md`.
Cualquier cambio ahí se coordina en el grupo.

---

## 6. Regla de documentación (vale para TODOS)

Tu `.md` de fase te va a repetir esto, pero que quede claro desde acá:

- **Cada decisión técnica se documenta** en tu archivo
  `docs/decisiones/faseX_decisiones_tunombre.md` (usá `PLANTILLA_decisiones.md`).
- Para cada decisión escribí: **qué elegiste, por qué, y por qué NO la alternativa.**
- Al final juntamos todas las bitácoras y armamos la **guía de estudio** para la
  defensa. Si no documentás, llegás a la defensa sin con qué responder, y la
  defensa vale 40 puntos.

---

## 7. Contrato de interfaces (cómo se conectan las fases)

Para que al final "solo haya que conectar", cada fase expone funciones con una
firma fija acordada de antemano. **Antes de programar, leé
`docs/interfaces/contratos.md`.** Si tu código respeta ese contrato, la Fase 6
(API) puede consumir tu módulo sin que tengas que estar presente. Si lo cambiás,
avisá al equipo.
