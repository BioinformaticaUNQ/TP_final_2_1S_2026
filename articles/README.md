# Papers de prueba y demo

Los PDFs estan agrupados por **que se espera del pipeline**, no por "calidad del paper".
Usar esta guia en la oral para no mostrar el caso equivocado.

## Leyenda (bloques del TP)

| Bloque | Contenido |
|--------|-----------|
| **A** | Metadatos del articulo (DOI, titulo, autores, anio, revista) |
| **B** | Proteina del organismo modelo + UniProt |
| **C** | Agrotoxico(s) + PubChem (SMILES, LogP; afinidad solo si el texto la trae con dueno claro) |
| **D** | Homologos humanos (BLASTp) |

## Carpetas

### `bc_dominio/` — proteina + agro (demo B+C)

Lo mas cercano al dominio del TP: OBP/CSP + insecticidas.

| Archivo / entrada | Organismo esperado | Salida esperada | No esperar |
|-------------------|--------------------|-----------------|------------|
| `1-s2.0-S0147651325015556-main.pdf` | *Aphis gossypii* | A + varias OBP/CSP + varios agros (PubChem) | Historia BLAST si usas `--skip-blast`; afinidad puede ser null (varios agros) |
| DOI `10.3389/fphys.2020.00819` (sin PDF local; se descarga) | *Tribolium castaneum* | A + OBP + pesticidas PubChem | D con `--skip-blast` |

**Comando demo B+C (recomendado en oral):**

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\demo\bc
tp-bioinfo articles\bc_dominio\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\demo\bc_aphis
```

### `bd_homologos/` — proteina + BLAST (demo B+D)

Lipocalina en organismo modelo; el paper **no** es de agrotóxicos.

| Archivo | Organismo esperado | Salida esperada | No esperar |
|---------|--------------------|-----------------|------------|
| `in-11-342.pdf` | *Danio rerio* | A + Lipocalin-2 prioritario + UniProt + D con `--blast-mode local` | Agrotóxicos (lista vacia es correcta) |

```powershell
tp-bioinfo articles\bd_homologos\in-11-342.pdf --blast-mode local --output-dir output\demo\bd
```

### `c_agrotoxicos/` — solo compuestos (contraste C)

Toxicologia / mezclas; **no** hay lipocalina/OBP del estudio.

| Archivo | Salida esperada | No esperar |
|---------|-----------------|------------|
| `acute_toxicity_atrazine.pdf` | A + varios agros con SMILES/LogP | Proteinas de la familia y BLAST ricos |

Sirve para mostrar **honestidad**: el sistema no inventa proteinas.

```powershell
tp-bioinfo articles\c_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\demo\c
```

### `otros/` — no usar como demo principal

PDF de apoyo, SI, o fuera del relato central. Pueden parsear algo, pero **no** representan el caso ideal del TP.

| Archivo | Nota |
|---------|------|
| `fbioe-11-1193454.pdf` | Material local extra |
| `2020.01.28.922179v1.full.pdf` | Preprint / dominio mixto |
| `jf6c01650_si_001.pdf` | Supporting information |

### DOI sin PDF (fallback A)

Cuando el publisher bloquea el PDF, solo hay metadatos Crossref. Eso es **correcto**, no un crash.

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\demo\fallback
```

Otros DOI OA utiles (B+C si el PDF baja): `10.3389/ftox.2021.627470`, `10.3389/fphys.2018.01729`, `10.3389/fphys.2022.924750`.

## Orden sugerido de la oral (3 corridas)

1. **B+C** — DOI Frontiers OBP *Tribolium* (`bc_dominio` / DOI arriba).
2. **B+D** — `bd_homologos/in-11-342.pdf` con BLAST local.
3. **Limite** — `c_agrotoxicos` **o** DOI ACS fallback (salida pobre a proposito).

No presentar un paper de `otros/` como si fuera el caso "completo" del TP.
