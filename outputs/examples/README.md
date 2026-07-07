# Ejemplos de salida

Estos JSON son salidas de ejemplo. La mayoria fueron generadas con `--skip-blast` para que sean rapidas y reproducibles. El ejemplo `pdf_blast_local_in_11_342.json` incluye homologos humanos calculados con BLAST local.

## Archivos

| Archivo | Entrada | Que muestra |
| --- | --- | --- |
| `pdf_agrotoxicos_atrazine.json` | `articles/acute_toxicity_atrazine.pdf` | Metadatos, agrotoxicos, familias quimicas, SMILES y LogP |
| `pdf_afinidad_multi_insecticide.json` | `articles/1-s2.0-S0147651325015556-main.pdf` | Proteinas, agrotoxicos y un valor de afinidad extraido del texto |
| `doi_descarga_frontiers.json` | DOI `10.3389/fphys.2020.00819` | Flujo DOI con PDF descargado y posterior parseo |
| `doi_fallback_crossref.json` | DOI `10.1021/acs.jafc.4c03368` | Fallback a metadatos Crossref cuando el publisher bloquea PDF |
| `pdf_blast_local_in_11_342.json` | `articles/in-11-342.pdf` | Proteinas y 15 homologos humanos obtenidos con BLAST local |

## Reproducir

```powershell
.\.venv_test\Scripts\tp-bioinfo.exe articles\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\examples_source\pdf_agrotoxicos

.\.venv_test\Scripts\tp-bioinfo.exe articles\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\examples_source\pdf_afinidad

.\.venv_test\Scripts\tp-bioinfo.exe 10.3389/fphys.2020.00819 --skip-blast --output-dir output\examples_source\doi_descarga --pdf-dir output\examples_source\doi_descarga\pdfs

.\.venv_test\Scripts\tp-bioinfo.exe 10.1021/acs.jafc.4c03368 --skip-blast --output-dir output\examples_source\doi_fallback --pdf-dir output\examples_source\doi_fallback\pdfs
```

Para reproducir el ejemplo con homologos humanos, primero configurar BLAST local:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_blast_local.ps1

.\.venv_test\Scripts\tp-bioinfo.exe articles\in-11-342.pdf --blast-mode local --output-dir output\examples_source\blast_local
```
