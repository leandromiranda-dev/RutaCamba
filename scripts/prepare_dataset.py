"""prepare_dataset.py — Materializa data/train|val|test/<clase>/ desde el manifest.

El dataset original está en Google Drive (carpeta "Places"), organizado SOLO por
clase: Places/<clase>/<archivo>. La división train/val/test la define
data/manifest.csv (columnas: path, class, split). Este script copia cada imagen
a la estructura que espera src/data/dataset.py:

    data/<split>/<clase>/<archivo>

Uso:
    # 1) Descargá la carpeta "Places" de Drive y descomprimila en algún lado.
    # 2) Apuntá --places-dir a esa carpeta:
    python scripts/prepare_dataset.py --places-dir "C:/Users/alfre/Downloads/Places"

    # Para mover en vez de copiar (ahorra espacio):
    python scripts/prepare_dataset.py --places-dir ... --move
"""
import argparse
import csv
import shutil
import sys
from collections import Counter
from pathlib import Path

# La consola de Windows usa cp1252 y rompe al imprimir caracteres Unicode
# (✓, ⚠). Igual que en src/landmarks/train.py, forzamos UTF-8 en stdout/stderr.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

MANIFEST_PATH = Path("data/manifest.csv")
OUTPUT_ROOT = Path("data")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--places-dir",
        required=True,
        help="Carpeta 'Places' descargada de Drive (con subcarpetas por clase).",
    )
    parser.add_argument(
        "--manifest",
        default=str(MANIFEST_PATH),
        help=f"Ruta al manifest (default: {MANIFEST_PATH}).",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Mover los archivos en vez de copiarlos (ahorra espacio en disco).",
    )
    args = parser.parse_args()

    places_dir = Path(args.places_dir)
    if not places_dir.is_dir():
        print(f"ERROR: no existe la carpeta {places_dir}", file=sys.stderr)
        return 1

    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(f"ERROR: no existe el manifest {manifest}", file=sys.stderr)
        return 1

    op = shutil.move if args.move else shutil.copy2
    copied, missing = 0, []
    per_split: Counter = Counter()

    with open(manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cls, split = row["class"], row["split"]
            filename = Path(row["path"]).name
            src = places_dir / cls / filename
            dst_dir = OUTPUT_ROOT / split / cls
            dst = dst_dir / filename

            if dst.exists():
                copied += 1
                per_split[split] += 1
                continue
            if not src.exists():
                missing.append(f"{cls}/{filename}")
                continue

            dst_dir.mkdir(parents=True, exist_ok=True)
            op(str(src), str(dst))
            copied += 1
            per_split[split] += 1

    print(f"\nProcesadas: {copied} imágenes")
    for split in ("train", "val", "test"):
        print(f"  {split}: {per_split[split]}")

    if missing:
        print(f"\n⚠ {len(missing)} archivos del manifest NO se encontraron en {places_dir}:")
        for m in missing[:15]:
            print(f"  - {m}")
        if len(missing) > 15:
            print(f"  ... y {len(missing) - 15} más")
        print("Revisá que --places-dir apunte a la carpeta correcta y esté completa.")
        return 1

    print("\n✓ Dataset listo en data/train|val|test/. Ya podés entrenar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
