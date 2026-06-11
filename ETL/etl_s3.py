"""etl_s3.py — Script de descarga y preparación del dataset desde S3.

Diego (Fase 1): implementá este script.

Pasos:
1. Descarga imágenes desde S3 (boto3)
2. Descarta corruptas (PIL try/except) y duplicados (hash MD5)
3. Reparte en train/val/test estratificado 70/15/15
4. Guarda en data/train/<clase>/, data/val/<clase>/, data/test/<clase>/

Uso:
    python ETL/etl_s3.py --bucket <nombre-bucket> --output data/
"""
# TODO (Diego): implementar el ETL de S3
