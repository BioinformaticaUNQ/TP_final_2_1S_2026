# Trabajo Práctico Final - Introducción a la Bioinformática

## Guia de Uso

Este proyecto está preparado para ejecutar Python y sus dependencias dentro de Docker.

Construir la imagen:

```bash
docker build -t tp-bioinfo .
```

Ejecutar el contenedor:

```bash
docker run --rm tp-bioinfo
```

Ese comando levanta una verificación básica de que Python y las dependencias instaladas cargan bien dentro del contenedor.

## Docker Compose

Además del uso directo con `docker build` y `docker run`, el proyecto también se puede levantar con Docker Compose.

Construir y ejecutar con Compose:

```bash
docker compose up --build
```

Ejecutar solo el servicio y salir al terminar la verificación:

```bash
docker compose run --rm app
```

El servicio `app` está definido para construir la imagen local y ejecutar `app.py` dentro del contenedor.
