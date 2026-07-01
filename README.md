# Trabajo Práctico Final - Introducción a la Bioinformática

## Guia de Uso

Este proyecto se instala con `setuptools` usando `pip` dentro de un entorno virtual. Ese es el flujo principal de trabajo.

Crear y activar un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Instalar el paquete localmente:

```bash
pip install -e .
```

Instalar tambien las dependencias de prueba:

```bash
pip install -e ".[test]"
```

Ejecutar la CLI instalada:

```bash
tp-bioinfo 10.1042/bj3180001
```

Ejecutar el script de ejemplo:

```bash
python scripts/cli_example.py
```

Ejecutar tests:

```bash
pytest -q
```

Tambien se puede seguir usando Docker, pero queda como alternativa para reproducir la ejecucion en contenedor.

Este proyecto también está preparado para ejecutar Python y sus dependencias dentro de Docker.

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

Comparado con `setuptools` + `venv`, Docker Compose sirve para aislar la ejecución completa en un contenedor reproducible. `setuptools` deja el proyecto instalable como paquete Python real y es el camino recomendado para desarrollo local, pruebas y ejecución de la CLI en una venv.

Construir y ejecutar con Compose:

```bash
docker compose up --build
```

Ejecutar solo el servicio y salir al terminar la verificación:

```bash
docker compose run --rm app
```

El servicio `app` está definido para construir la imagen local y ejecutar `app.py` dentro del contenedor.

## Estructura

La estructura principal queda separada en tres partes:

```text
app.py
src/
	services/
	models/
scripts/
tests/
```

`src/services` agrupa los clientes externos, `src/models` agrupa los modelos de datos y `app.py` queda como punto de entrada de la CLI.

## Resumen de verificación

1. Crear venv: `python -m venv .venv`
2. Activar venv: `.venv\Scripts\activate`
3. Instalar paquete: `pip install -e .`
4. Instalar tests: `pip install -e ".[test]"`
5. Probar CLI: `tp-bioinfo 10.1042/bj3180001`
6. Probar script: `python scripts/cli_example.py`
7. Correr tests: `pytest -q`
