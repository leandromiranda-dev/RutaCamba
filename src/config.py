"""config.py — Constantes compartidas por TODAS las fases.

REGLA: este archivo lo leen todos pero solo lo edita el coordinador del proyecto.
Si tu fase necesita una constante nueva, avisá al equipo ANTES de agregarla aquí.

Los valores sensibles (credenciales, entity de WandB, clave del LLM) se leen
desde variables de entorno. Crea un `.env` local (ver `.env.example`) y llamá
a `load_dotenv()` en tu punto de entrada antes de importar este módulo.
"""
import os

# ── Clases de landmarks ───────────────────────────────────────────────────────
LANDMARK_CLASSES = [
    "cristo_redentor",         # 0
    "fuerte_samaipata",        # 1
    "parque_el_arenal",        # 2
    "jardin_botanico",         # 3
    "catedral_metropolitana",  # 4
    "biocentro_guembe",        # 5
    "lomas_de_arena",          # 6
    "manzana_uno",             # 7
]
NUM_CLASSES = len(LANDMARK_CLASSES)  # 8

# ── Preprocesamiento de imágenes (Diego — Fase 1) ────────────────────────────
RESIZE = 256
CROP = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# ── Re-ID (Jose + Leandro — Fase 2) ─────────────────────────────────────────
REID_MODEL      = "ArcFace"       # modelo de DeepFace
REID_DISTANCE   = "cosine"        # métrica de distancia
REID_THRESHOLD  = 0.65            # ⚠ punto de partida — Leandro/Jose lo ajustan con ROC/EER
GALLERY_DIR     = "data/gallery"  # carpeta con subcarpetas por identidad

# ── Entrenamiento (Alejandro — Fase 3) ───────────────────────────────────────
BATCH_SIZE      = 32
LR              = 1e-3
WEIGHT_DECAY    = 1e-4
DROPOUT         = 0.5
MIN_EPOCHS      = 30
MODELS_DIR      = "models"

# ── Experiment tracking (Nicole — Fase 5) ────────────────────────────────────
WANDB_PROJECT   = os.getenv("WANDB_PROJECT", "rutacamba")
WANDB_ENTITY    = os.getenv("WANDB_ENTITY", "")

# ── Traducción (Jose — Fase 4) ───────────────────────────────────────────────
TRANSLATIONS_PATH    = "data/translations.json"
SUPPORTED_LANGUAGES  = ["es", "en", "fr", "it"]

# ── API (Nicole — Fase 6) ────────────────────────────────────────────────────
API_HOST  = "0.0.0.0"
API_PORT  = 8000
UI_PORT   = 7860
TOKEN_TTL = 3600  # segundos de validez del token de sesión
