# src/reid/__init__.py
# Fase 2 (Jose + Leandro)
from src.reid.access import verify_identity, reload_gallery  # noqa: F401
from src.reid.embeddings import get_embedding, build_gallery  # noqa: F401
from src.reid.gallery import load_gallery, save_gallery       # noqa: F401
from src.reid.ranking import rank_identities, cosine_distance # noqa: F401
