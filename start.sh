#!/bin/sh
# start.sh — Descarga el modelo desde WandB y arranca el servidor.
# HF Spaces inyecta PORT=7860; Render/Railway inyectan su propio PORT.
set -e

python scripts/download_model_wandb.py

exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-7860}"
