# Ejemplos de salida

JSON de referencia alineados con las categorias de `articles/README.md`.
Generados con el pipeline actual (filtro de organismo, ranking de la proteina principal, BLAST sobre esa proteina).

## Correspondencia archivo ↔ entrada

| Archivo | Entrada | Contenido principal de la salida |
| --- | --- | --- |
| `doi_descarga_frontiers.json` | DOI `10.3389/fphys.2020.00819` | OBP *Tribolium* y pesticidas (PubChem) |
| `pdf_obp_csp_aphis.json` | `articles/proteina_y_agro/1-s2.0-S0147651325015556-main.pdf` | OBP/CSP *Aphis* e insecticidas |
| `pdf_blast_local_in_11_342.json` | `articles/proteina_y_homologos/in-11-342.pdf` | Lipocalin-2 prioritario y homologos humanos (BLAST local) |
| `pdf_agrotoxicos_atrazine.json` | `articles/solo_agrotoxicos/acute_toxicity_atrazine.pdf` | Agrotoxicos sin proteinas del dominio |
| `doi_fallback_crossref.json` | DOI `10.1021/acs.jafc.4c03368` | Solo metadatos Crossref (PDF no disponible) |

## Limitaciones observadas en estos ejemplos

- En el ejemplo BLAST, la cantidad de homologos depende de los hits del proteoma local (puede ser menor a 15).
- Con varios agrotoxicos, la afinidad puede quedar vacia si no hay asociacion unívoca en el texto.
- `funcion_biologica` queda vacia cuando la entrada UniProt no incluye ese comentario.

## Reproduccion

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\ejemplos\frontiers

tp-bioinfo articles\proteina_y_agro\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\ejemplos\aphis

tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\ejemplos\atrazine

tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\ejemplos\fallback
```

BLAST local (requiere `scripts\setup_blast_local.ps1`):

```powershell
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\ejemplos\blast
```
