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

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

# Respeta $PORT (Render/Railway lo inyectan). Sin --reload en producción.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
