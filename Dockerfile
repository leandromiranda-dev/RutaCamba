# Dockerfile — backend FastAPI de RutaCamba (Re-ID facial + landmarks + LLM).
# Imagen para Render / Railway / Fly.io / cualquier host con CPU.
FROM python:3.11-slim

# Dependencias de sistema para Pillow / torch / facenet.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias primero (mejor cache de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto (ver .dockerignore para exclusiones).
COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 7860

COPY start.sh .
RUN chmod +x start.sh

# Descarga el modelo desde WandB y arranca uvicorn.
# PORT es inyectado por HF Spaces (7860) / Render / Railway.
CMD ["./start.sh"]
