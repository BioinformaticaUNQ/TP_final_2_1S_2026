FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala el paquete (deja disponible el comando `tp-bioinfo`).
# Se copia primero lo necesario para el build para aprovechar la cache de capas.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# PDFs de ejemplo para probar los casos de PDF y de directorio dentro del contenedor.
COPY articles/ ./articles/

# Los JSON generados van a /app/output (montar un volumen para verlos en el host).
ENTRYPOINT ["tp-bioinfo"]
CMD ["--help"]
