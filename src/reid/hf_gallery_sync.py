"""hf_gallery_sync.py — Sincronización de galería biométrica con HF Dataset Hub.

Permite persistencia gratuita en HF Spaces: al arrancar se descarga la galería
actualizada; al enrolar se sube inmediatamente. Requiere dos variables de entorno:
    HF_GALLERY_REPO  — repo de tipo dataset, ej. "usuario/rutacamba-gallery"
    HF_TOKEN         — token de HF con permiso de escritura sobre ese repo

Si alguna de las dos no está configurada, las funciones retornan sin error
(modo local o mock, donde la galería viene del repo o del disco).
"""

import logging
import os

from src.config import GALLERY_DIR

logger = logging.getLogger(__name__)

_REPO = os.getenv("HF_GALLERY_REPO", "")
_TOKEN = os.getenv("HF_TOKEN", "")

_GALLERY_FILES = ["gallery_cache.pkl", "embeddings_autorizados.pt"]
_ROLES_PATH = os.path.join("data", "roles.json")


def pull_gallery() -> None:
    """Descarga galería y roles desde HF Dataset Hub al disco local.

    Sobreescribe los archivos locales para garantizar que el servidor arranca
    con los datos más recientes (incluyendo enrolamientos hechos en el pasado).
    Si un archivo todavía no existe en el repo (primera vez), lo omite sin error.
    """
    if not _REPO or not _TOKEN:
        logger.info("HF_GALLERY_REPO / HF_TOKEN no configurados — galería local.")
        return

    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError

    os.makedirs(GALLERY_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    for filename in _GALLERY_FILES:
        dest = os.path.join(GALLERY_DIR, filename)
        try:
            hf_hub_download(
                repo_id=_REPO,
                filename=filename,
                repo_type="dataset",
                token=_TOKEN,
                local_dir=GALLERY_DIR,
                force_download=True,
            )
            logger.info(f"[HF pull] {filename} → {dest}")
        except EntryNotFoundError:
            logger.info(f"[HF pull] {filename} no existe en el repo aún, se omite.")
        except Exception as e:
            logger.warning(f"[HF pull] No se pudo descargar {filename}: {e}")

    try:
        hf_hub_download(
            repo_id=_REPO,
            filename="roles.json",
            repo_type="dataset",
            token=_TOKEN,
            local_dir="data",
            force_download=True,
        )
        logger.info(f"[HF pull] roles.json → {_ROLES_PATH}")
    except EntryNotFoundError:
        logger.info("[HF pull] roles.json no existe en el repo aún, se omite.")
    except Exception as e:
        logger.warning(f"[HF pull] No se pudo descargar roles.json: {e}")


def push_gallery() -> None:
    """Sube galería y roles al HF Dataset Hub tras un enrolamiento.

    Solo sube los archivos que existen en disco. Los errores se loguean pero
    no interrumpen la respuesta al cliente (el enrolamiento ya fue persistido
    localmente por save_gallery / set_role).
    """
    if not _REPO or not _TOKEN:
        return

    from huggingface_hub import upload_file

    uploads = [
        (os.path.join(GALLERY_DIR, f), f) for f in _GALLERY_FILES
    ] + [(_ROLES_PATH, "roles.json")]

    for local_path, repo_filename in uploads:
        if not os.path.exists(local_path):
            continue
        try:
            upload_file(
                path_or_fileobj=local_path,
                path_in_repo=repo_filename,
                repo_id=_REPO,
                repo_type="dataset",
                token=_TOKEN,
            )
            logger.info(f"[HF push] {local_path} → {repo_filename}")
        except Exception as e:
            logger.warning(f"[HF push] No se pudo subir {repo_filename}: {e}")
