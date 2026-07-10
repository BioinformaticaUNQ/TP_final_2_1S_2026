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
tp-bioinfo articles\c_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\manual_pdf
```

Procesar todos los PDFs de un subdirectorio:

```powershell
tp-bioinfo articles\bc_dominio --skip-blast --output-dir output\manual_dir
```

Procesar un DOI descargando el PDF cuando el publisher lo permite:

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --output-dir output\manual_doi --pdf-dir output\manual_doi\pdfs
```

Si el PDF no se puede descargar, la herramienta genera un JSON con metadatos de Crossref:

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --output-dir output\manual_doi_fallback
```

## Demo oral (3 corridas)

Los papers estan clasificados en `articles/` segun lo que se espera del resultado. Guia completa: `articles/README.md`.

| Orden | Objetivo | Entrada | Flags |
|-------|----------|---------|-------|
| 1 | B+C (OBP + agro) | DOI `10.3389/fphys.2020.00819` | `--skip-blast --no-save-pdf` |
| 2 | B+D (lipocalina + humanos) | `articles\bd_homologos\in-11-342.pdf` | `--blast-mode local` |
| 3 | Limite honesto | `articles\c_agrotoxicos\...` o DOI ACS | `--skip-blast` |

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\demo\bc
tp-bioinfo articles\bd_homologos\in-11-342.pdf --blast-mode local --output-dir output\demo\bd
tp-bioinfo articles\c_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\demo\c
```

Bloques del JSON: **A** articulo, **B** proteina, **C** agrotoxico, **D** homologos humanos.

## Opciones principales

```text
--output-dir PATH            Directorio donde se guardan los JSON generados.
--skip-blast                 Omite BLASTp para pruebas rapidas.
--blast-mode [local|remote]  Usa BLAST local o remoto. Por defecto: remote.
--pdf-dir PATH               Directorio para PDFs descargados desde DOI.
--no-save-pdf                Analiza el PDF en memoria sin guardarlo en disco.
```

## BLAST

Por defecto, si no se usa `--skip-blast`, la herramienta intenta BLAST remoto mediante NCBI. Ese modo puede tardar varios minutos y depende del servicio externo.

Para demos y pruebas repetibles se recomienda BLAST local:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_blast_local.ps1
tp-bioinfo articles\bd_homologos\in-11-342.pdf --blast-mode local --output-dir output\blast_local_test
```

Durante desarrollo, usar `--skip-blast` para validar parser, Crossref, UniProt y PubChem sin esperar BLAST.

## Salidas

Cada articulo genera un JSON con:

```text
articulo
proteinas
agrotoxicos
homologos_humanos
```

Ejemplos versionados (actuales) en `outputs/examples/` — ver `outputs/examples/README.md`.

Las corridas locales de trabajo van a `output/` (ignorada por git).

## Documentacion tecnica

```text
docs/architecture.md
```

## Tests

```powershell
pytest -q
```

Los tests unitarios usan mocks para evitar llamadas reales a servicios externos. Hay una prueba de BLAST local que se saltea si no esta el binario y la base local.

## Build del paquete

```powershell
python -m pip install build
python -m build --wheel
```

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
articles/                 # PDFs de prueba por categoria de demo
  bc_dominio/             # proteina + agro
  bd_homologos/           # proteina + BLAST
  c_agrotoxicos/          # solo compuestos
  otros/                  # no usar como demo principal
outputs/examples/         # JSON de ejemplo versionados
scripts/
tests/
docs/
data/                     # corpus e2e y (local) BLAST
```

- `src/app.py`: CLI.
- `src/services`: Crossref, UniProt, PubChem, BLAST, seleccion de candidatos.
- `src/models`: modelos del JSON.
- `src/utils`: parser de PDFs.
- `articles`: material de prueba y demo (ver `articles/README.md`).
- `outputs/examples`: salidas de referencia.
- `scripts`: helpers (BLAST local, etc.).
- `tests`: unitarios y empaquetado.
