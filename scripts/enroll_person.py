"""enroll_person.py — Alta de una persona en la galería de Re-ID (CLI).

Sirve para el ARRANQUE del sistema: crear el primer administrador (que no puede
registrarse desde el panel web porque el panel exige estar logueado como admin).
Una vez que exista un admin, las demás personas se registran desde la app
(panel Administración → Registrar persona).

Uso:
    # Crear el primer admin a partir de una o varias selfies
    python scripts/enroll_person.py --name jose --role admin \
        --images data/admin1.jpg data/admin2.jpg

    # Empezar la galería de cero (descarta las identidades previas)
    python scripts/enroll_person.py --name jose --role admin --reset \
        --images data/admin.jpg

Detalles:
    - Calcula el embedding facial de cada imagen con src.reid.embeddings.get_embedding
      (facenet_pytorch: MTCNN + InceptionResnetV1 / VGGFace2, 512-d).
    - Las imágenes sin rostro detectable se descartan (con aviso).
    - Persiste en data/gallery/gallery_cache.pkl (formato {id: [emb, ...]}) y
      registra el rol en data/roles.json.
    - Tras correrlo, REINICIÁ el backend para que recargue la galería.
"""
from dotenv import load_dotenv
load_dotenv()

import argparse
import os
import sys

# Funciona desde cualquier carpeta: las rutas de la galería/roles se resuelven
# contra la raíz del proyecto, y las fotos (--images) contra el directorio desde
# el que invocás el script.
_ORIG_CWD = os.getcwd()
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)
os.chdir(_PROJECT_ROOT)  # para que "data/gallery" y "data/roles.json" caigan en su lugar


def _resolve_image(path: str) -> str:
    """Resuelve la ruta de una foto relativa al cwd original del usuario."""
    return path if os.path.isabs(path) else os.path.join(_ORIG_CWD, path)

from src.config import GALLERY_DIR
from src.reid.embeddings import get_embedding
from src.reid.gallery import load_gallery, save_gallery
from src.reid.roles import set_role


def main() -> None:
    parser = argparse.ArgumentParser(description="Alta de una persona en la galería de Re-ID.")
    parser.add_argument("--name", required=True, help="Nombre/identidad (lo que se declara al loguear).")
    parser.add_argument("--role", default="user", choices=["user", "admin"], help="Rol (default: user).")
    parser.add_argument("--images", nargs="+", required=True, help="Una o más rutas a fotos del rostro.")
    parser.add_argument("--reset", action="store_true", help="Vacía la galería antes de agregar (empezar de cero).")
    args = parser.parse_args()

    cache_path = os.path.join(GALLERY_DIR, "gallery_cache.pkl")

    gallery = {} if args.reset else (load_gallery(cache_path) or {})
    if args.reset:
        print("⚠️  --reset: la galería se reconstruye desde cero.")

    embeddings = []
    for raw_path in args.images:
        path = _resolve_image(raw_path)
        if not os.path.exists(path):
            print(f"✗ No existe: {path}")
            continue
        emb = get_embedding(path)
        if emb is None:
            print(f"✗ Sin rostro detectable: {path}")
            continue
        embeddings.append(emb)
        print(f"✓ Embedding extraído: {path}")

    if not embeddings:
        print("\n❌ No se obtuvo ningún embedding válido. Probá con fotos del rostro nítidas y de frente.")
        sys.exit(1)

    gallery.setdefault(args.name, [])
    gallery[args.name].extend(embeddings)
    save_gallery(gallery, cache_path)
    set_role(args.name, args.role)

    print(
        f"\n✅ '{args.name}' registrado/a como {args.role} "
        f"({len(embeddings)} embedding(s) nuevo(s); total {len(gallery[args.name])}).\n"
        f"   Galería: {cache_path}\n"
        f"   Identidades ahora: {list(gallery.keys())}\n\n"
        f"➡️  Reiniciá el backend (uvicorn) para que recargue la galería."
    )


if __name__ == "__main__":
    main()
