# Trabajo Practico Final - Introduccion a la Bioinformatica

Herramienta de linea de comandos para procesar bibliografia cientifica sobre interacciones entre proteinas tipo lipocalina/OBP/CSP y agrotoxicos. A partir de un PDF, un directorio de PDFs o un DOI, genera un JSON por articulo con metadatos, proteinas candidatas, compuestos investigados y homologos humanos cuando se ejecuta BLAST.

## Requisitos

- Python 3.13 o superior.
- Windows PowerShell para los comandos de ejemplo.
- Conexion a internet para Crossref, UniProt, PubChem, descarga de PDFs por DOI y BLAST remoto.

El proyecto se empaqueta con `setuptools` desde `pyproject.toml`. Al instalarlo con `pip`, queda disponible el comando:

```powershell
tp-bioinfo
```

## Instalacion

Crear y activar un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Instalar el paquete en modo editable:

```powershell
python -m pip install --upgrade pip
pip install -e .
```

Instalar tambien las dependencias de tests:

```powershell
pip install -e ".[test]"
```

Verificar que la CLI quedo instalada:

```powershell
tp-bioinfo --help
```

## Uso

Procesar un PDF individual sin BLAST, util para pruebas rapidas:

```powershell
tp-bioinfo articles\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\manual_pdf
```

Procesar todos los PDFs de un directorio:

```powershell
tp-bioinfo articles --skip-blast --output-dir output\manual_dir
```

Procesar un DOI descargando el PDF cuando el publisher lo permite:

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --output-dir output\manual_doi --pdf-dir output\manual_doi\pdfs
```

Si el PDF no se puede descargar, la herramienta conserva un fallback y genera un JSON con metadatos de Crossref:

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --output-dir output\manual_doi_fallback
```

## Opciones principales

```text
--output-dir PATH            Directorio donde se guardan los JSON generados.
--skip-blast                 Omite BLASTp para pruebas rapidas.
--blast-mode [local|remote]  Usa BLAST local o remoto. Por defecto: remote.
--pdf-dir PATH               Directorio para PDFs descargados desde DOI.
```

## BLAST

Por defecto, si no se usa `--skip-blast`, la herramienta intenta BLAST remoto mediante NCBI. Ese modo puede tardar varios minutos por proteina y depende de la disponibilidad del servicio externo.

Para demos y pruebas repetibles se recomienda configurar BLAST local:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_blast_local.ps1
```

Luego ejecutar:

```powershell
tp-bioinfo articles\in-11-342.pdf --blast-mode local --output-dir output\blast_local_test
```

Durante desarrollo, usar `--skip-blast` para validar parser, Crossref, UniProt y PubChem sin esperar BLAST:

```powershell
tp-bioinfo articles --skip-blast --output-dir output\quick_test
```

## Salidas

Cada articulo genera un JSON con esta estructura general:

```text
articulo
proteinas
agrotoxicos
homologos_humanos
```

La carpeta `outputs/examples` contiene salidas de ejemplo versionadas, incluyendo:

- PDF local con agrotoxicos.
- PDF local con afinidad detectada.
- DOI con descarga de PDF.
- DOI con fallback Crossref.
- Ejemplo con BLAST local y 15 homologos humanos.

Tambien hay una lista de DOI utiles para pruebas en:

```text
articles/dois_casos_prueba.md
```

## Tests

Ejecutar la suite:

```powershell
pytest -q
```

Los tests unitarios usan mocks para evitar llamadas reales a servicios externos. Hay una prueba de BLAST local que se saltea automaticamente si no esta instalado el binario y la base local.

## Build del paquete

El proyecto puede construirse como wheel instalable:

```powershell
python -m pip install build
python -m build --wheel
```

Instalar el wheel generado en una venv limpia:

```powershell
python -m venv .venv_packaging_test
.\.venv_packaging_test\Scripts\python.exe -m pip install dist\tp_bioinfo-0.1.0-py3-none-any.whl
.\.venv_packaging_test\Scripts\tp-bioinfo.exe --help
```

## Estructura

```text
src/
  app.py
  models/
  services/
  utils/
articles/
outputs/examples/
scripts/
tests/
docs/
```

- `src/app.py`: punto de entrada de la CLI.
- `src/services`: clientes para Crossref, UniProt, PubChem y BLAST.
- `src/models`: modelos de datos usados en la salida JSON.
- `src/utils`: parser de PDFs.
- `articles`: PDFs y DOI de prueba.
- `outputs/examples`: JSON de ejemplo.
- `scripts`: helpers de ejecucion y configuracion local.
- `tests`: tests unitarios y de empaquetado.

