"""download_models.py — Descarga los modelos TorchScript desde S3 (Nicole, Fase 6).

Los modelos no se suben al repo (están en .gitignore). Este script los baja
antes de levantar la API.

Uso:
    python scripts/download_models.py --bucket <nombre-bucket>
    python scripts/download_models.py --bucket rutacamba-models --prefix checkpoints

Requiere credenciales AWS configuradas (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
en el entorno o en ~/.aws/credentials).
"""
import argparse
import os

import boto3
from botocore.exceptions import ClientError

MODELS_DIR = "models"
MODEL_FILES = ["cnn_scratch.pt", "transfer_learning.pt"]


def download_models(bucket: str, prefix: str = "models") -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    s3 = boto3.client("s3")

    for filename in MODEL_FILES:
        s3_key = f"{prefix}/{filename}" if prefix else filename
        local_path = os.path.join(MODELS_DIR, filename)

        if os.path.exists(local_path):
            print(f"[skip] {filename} ya existe en {local_path}")
            continue

        print(f"Descargando s3://{bucket}/{s3_key} → {local_path} ...")
        try:
            s3.download_file(bucket, s3_key, local_path)
            print(f"  ✓ {filename}")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "404":
                print(f"  ✗ No encontrado en S3: {s3_key}")
            else:
                raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descarga modelos TorchScript desde S3 al directorio models/."
    )
    parser.add_argument("--bucket", required=True, help="Nombre del bucket S3")
    parser.add_argument(
        "--prefix",
        default="models",
        help="Prefijo (carpeta) dentro del bucket (default: models)",
    )
    args = parser.parse_args()
    download_models(args.bucket, args.prefix)
