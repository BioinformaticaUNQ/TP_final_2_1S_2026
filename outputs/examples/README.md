# Ejemplos de salida

JSON versionados alineados con las categorias de `articles/README.md`.
Regenerados con el pipeline actual (organismo filtrado, ranking de la proteina principal, BLAST solo sobre esa proteina).

## Mapa ejemplo ↔ caso

| Archivo | Entrada | Que demuestra |
| --- | --- | --- |
| `doi_descarga_frontiers.json` | DOI `10.3389/fphys.2020.00819` | OBP *Tribolium* + pesticidas (PubChem) |
| `pdf_obp_csp_aphis.json` | `articles/proteina_y_agro/1-s2.0-S0147651325015556-main.pdf` | OBP/CSP *Aphis* + insecticidas |
| `pdf_blast_local_in_11_342.json` | `articles/proteina_y_homologos/in-11-342.pdf` | Lipocalin-2 prioritario + homologos humanos (BLAST local) |
| `pdf_agrotoxicos_atrazine.json` | `articles/solo_agrotoxicos/acute_toxicity_atrazine.pdf` | Solo agrotoxicos (sin proteinas inventadas) |
| `doi_fallback_crossref.json` | DOI `10.1021/acs.jafc.4c03368` | PDF bloqueado → solo metadatos Crossref |

## Notas honestas

- En el ejemplo BLAST, los homologos son los que devuelve el proteoma local para la secuencia principal (pueden ser menos de 15 si no hay mas hits utiles).
- Afinidad vacia con varios agrotoxicos es intencional: no se pega un valor al primer compuesto al azar.
- `funcion_biologica` vacia es frecuente cuando UniProt no trae ese comentario.

## Reproducir

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\examples_source\frontiers

tp-bioinfo articles\proteina_y_agro\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\examples_source\aphis

tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\examples_source\atrazine

tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\examples_source\fallback
```

BLAST local (requiere `scripts\setup_blast_local.ps1`):

```powershell
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\examples_source\blast
```
