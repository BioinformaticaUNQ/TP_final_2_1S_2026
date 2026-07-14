# Trabajo Practico Final - Introduccion a la Bioinformatica

Trabajo practico final de la materia **Introduccion a la Bioinformatica**, 1er cuatrimestre de 2026, Universidad Nacional de Quilmes.

**Grupo 2**

| Participantes |
|--------------|
| Acosta, Federico |
| Aguero, Fernando |
| Fuentes, Jeremias |

Herramienta de linea de comandos para procesar bibliografia cientifica sobre interacciones entre proteinas tipo lipocalina/OBP/CSP y agrotoxicos. A partir de un PDF, un directorio de PDFs o un DOI, genera un JSON por articulo con metadatos, proteinas candidatas, compuestos investigados y homologos humanos cuando se ejecuta BLAST.

## Requisitos

- Python 3.13 o superior.
- Windows PowerShell para los comandos de ejemplo.
- Conexion a internet para Crossref, UniProt, PubChem, descarga de PDFs por DOI y BLAST remoto.
  Crossref/PubChem/UniProt suelen sumar varios segundos por consulta; un DOI con PDF remoto puede demorar mas.

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

Procesar un PDF individual sin BLAST:

```powershell
tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\manual_pdf
```

Procesar todos los PDFs de un subdirectorio:

```powershell
tp-bioinfo articles\proteina_y_agro --skip-blast --output-dir output\manual_dir
```

Procesar un DOI descargando el PDF cuando el publisher lo permite:

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --output-dir output\manual_doi --pdf-dir output\manual_doi\pdfs
```

Si el PDF no se puede descargar, la herramienta genera un JSON con metadatos de Crossref:

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --output-dir output\manual_doi_fallback
```

La corrida termina cuando aparece `JSON generado: ...` en la consola.

## Casos de prueba de referencia

Los articulos de ejemplo estan clasificados en `articles/` segun el tipo de resultado esperado. Detalle: `articles/README.md`.

| Tipo de caso | Entrada | Flags tipicos |
|--------------|---------|---------------|
| Proteina + agrotoxico | DOI `10.3389/fphys.2020.00819` | `--skip-blast --no-save-pdf` |
| Proteina + homologos humanos | `articles\proteina_y_homologos\in-11-342.pdf` | `--blast-mode local` |
| Solo agrotoxicos | `articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf` | `--skip-blast` |
| DOI sin PDF | DOI `10.1021/acs.jafc.4c03368` | `--skip-blast --no-save-pdf` |

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\casos\proteina_agro
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\casos\homologos
tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\casos\solo_agro
```

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

Para pruebas repetibles conviene BLAST local. Ejecutar el setup y la CLI en la misma sesion de PowerShell (el script define `BLASTP_BIN` y `HUMAN_PROTEOME_DB` para esa sesion). Si `data\blast` y `data\db` ya existen, el setup no vuelve a descargar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_blast_local.ps1
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\blast_local_test
```

Con `--skip-blast` no se ejecuta BLAST; Crossref, UniProt y PubChem siguen usando red.

## Salidas

Cada articulo genera un JSON con:

```text
articulo            # metadatos del paper
proteinas           # organismo modelo + UniProt
agrotoxicos         # compuestos + PubChem
homologos_humanos   # BLASTp (si no se omite)
```

Algunos campos (funcion, afinidad, PDB) quedan vacios si no hay dato en el articulo o en la API. BLAST reporta hasta 15 hits o los que superen el umbral.

JSON de referencia en `outputs/examples/` (ver `outputs/examples/README.md`). Las corridas propias van a `output/` (ignorada por git); no es la misma carpeta que `outputs/examples/`.

## Documentacion tecnica

```text
docs/architecture.md
```

## Tests

```powershell
pytest -q
```

Los tests unitarios usan mocks para evitar llamadas reales a servicios externos. Hay una prueba de BLAST local que se saltea si no estan el binario y la base local.

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
articles/                      # articulos de ejemplo por tipo de resultado
  proteina_y_agro/             # OBP/CSP + insecticidas
  proteina_y_homologos/        # lipocalina + BLAST a humanos
  solo_agrotoxicos/            # toxicologia sin proteina del dominio
  otros/                       # material adicional
outputs/examples/              # JSON de referencia
scripts/
tests/
docs/
data/                          # corpus e2e y (local) BLAST
```

- `src/app.py`: CLI.
- `src/services`: Crossref, UniProt, PubChem, BLAST, seleccion de candidatos.
- `src/models`: modelos del JSON.
- `src/utils`: parser de PDFs.
- `articles`: articulos de ejemplo (ver `articles/README.md`).
- `outputs/examples`: salidas de referencia.
- `scripts`: helpers (BLAST local, etc.).
- `tests`: unitarios y empaquetado.
