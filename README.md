# RutaCamba — Sistema de Asistencia Turística Inteligente

> **README en construcción** — Nicole (Fase 7) lo completa al final.

Sistema de clasificación de landmarks de Santa Cruz de la Sierra con verificación
de identidad y traducción multilingüe.

## Estructura del proyecto

Ver [context.md](context.md) para el mapa completo de carpetas y responsables.

## Instalación rápida (por fase)

```bash
# Instalar dependencias de tu fase
pip install -r requirements/faseN.txt   # cambiá N por tu número de fase
```

## Arranque (Fase 6 — Nicole completa esto)

```bash
# API (puerto 8000)
uvicorn api.main:app --reload

# Interfaz (puerto 7860)
python ui/app.py
```

## WandB

Proyecto: `rutacamba` — enlace: _(Nicole agrega el enlace al cerrar Fase 5)_

## Flujo del sistema

```
selfie + id → Re-ID (verify_identity) → token
foto lugar  → CNN/TL (predict) → nombre + top-k
            → LLM (get_landmark_translations) → es/en/fr/it
```
