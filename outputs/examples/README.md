# Ejemplos de salida

JSON versionados alineados con las categorias de `articles/README.md`.
Regenerados con el pipeline actual (organismo filtrado, ranking de proteina principal, BLAST solo sobre esa proteina).

## Mapa ejemplo ↔ caso

| Archivo | Entrada | Que demuestra | Bloques |
| --- | --- | --- | --- |
| `doi_descarga_frontiers.json` | DOI `10.3389/fphys.2020.00819` | OBP *Tribolium* + pesticidas PubChem | A + B + C |
| `pdf_obp_csp_aphis.json` | `articles/bc_dominio/1-s2.0-S0147651325015556-main.pdf` | OBP/CSP *Aphis* + insecticidas | A + B + C |
| `pdf_blast_local_in_11_342.json` | `articles/bd_homologos/in-11-342.pdf` | Lipocalin-2 prioritario + homologos humanos (BLAST local) | A + B + D |
| `pdf_agrotoxicos_atrazine.json` | `articles/c_agrotoxicos/acute_toxicity_atrazine.pdf` | Solo agrotóxicos (sin proteinas inventadas) | A + C |
| `doi_fallback_crossref.json` | DOI `10.1021/acs.jafc.4c03368` | PDF bloqueado → solo metadatos Crossref | A |

## Notas honestas

- En `pdf_blast_local_in_11_342.json` los homologos son los que devuelve el proteoma local para la secuencia principal (pueden ser menos de 15 si BLAST no encuentra mas hits utiles).
- Afinidad null en multi-agro es intencional: no se pega un Ki al primer compuesto al azar.
- `funcion_biologica` null es frecuente en entradas UniProt sin comentario FUNCTION.

## Reproducir

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\examples_source\bc_frontiers

tp-bioinfo articles\bc_dominio\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\examples_source\bc_aphis

tp-bioinfo articles\c_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\examples_source\c_atrazine

tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\examples_source\fallback
```

BLAST local (requiere `scripts\setup_blast_local.ps1`):

```powershell
tp-bioinfo articles\bd_homologos\in-11-342.pdf --blast-mode local --output-dir output\examples_source\bd_blast
```
