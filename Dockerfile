# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar librerías del sistema requeridas por SDL/Pygame en entornos headless (sin monitor)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Variables de entorno para ejecución headless en la nube
ENV SDL_VIDEODRIVER=dummy
ENV SDL_AUDIODRIVER=dummy
ENV PYTHONUNBUFFERED=1
ENV PORT=5555
ENV HOST=0.0.0.0

# Exponer el puerto del servidor
EXPOSE 5555

# Ejecutar el servidor
CMD ["python", "server.py"]

