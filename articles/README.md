# Articulos de ejemplo

PDFs y DOI de prueba agrupados segun el tipo de resultado esperado del pipeline.

Cada corrida genera un JSON con cuatro secciones (cuando el articulo y las APIs lo permiten).
Las consultas externas pueden demorar; el indicador de fin es el mensaje `JSON generado`.

| Seccion del JSON | Contenido |
|------------------|-----------|
| `articulo` | DOI, titulo, autores, anio, revista |
| `proteinas` | Proteina del organismo modelo, UniProt, funcion si UniProt la publica |
| `agrotoxicos` | Compuestos, familia, SMILES, LogP; afinidad solo si el texto la asocia de forma unívoca |
| `homologos_humanos` | Hits BLASTp contra el proteoma humano (hasta 15 o los disponibles) |

---

## Carpetas

### `proteina_y_agro/`

Articulos con proteinas del dominio (OBP/CSP u homologas) y agrotoxicos o insecticidas.

| Entrada | Organismo esperado | Resultado tipico | Resultado no esperado |
|---------|--------------------|------------------|------------------------|
| `1-s2.0-S0147651325015556-main.pdf` | *Aphis gossypii* | Metadatos, varias OBP/CSP, varios agrotoxicos con PubChem | Homologos con `--skip-blast`; afinidad puede quedar vacia si hay varios compuestos |
| DOI `10.3389/fphys.2020.00819` (descarga; sin PDF local) | *Tribolium castaneum* | Metadatos, OBP, pesticidas con PubChem | Homologos con `--skip-blast` |

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\casos\proteina_agro
tp-bioinfo articles\proteina_y_agro\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\casos\proteina_agro_aphis
```

### `proteina_y_homologos/`

Articulos centrados en una proteina modelo (p. ej. lipocalina) sin foco en agrotoxicos. Aptos para evaluar BLAST.

| Entrada | Organismo esperado | Resultado tipico | Resultado no esperado |
|---------|--------------------|------------------|------------------------|
| `in-11-342.pdf` | *Danio rerio* | Metadatos, Lipocalin-2 prioritario, UniProt, homologos con `--blast-mode local` | Agrotoxicos (lista vacia si el articulo no los trata) |

```powershell
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\casos\homologos
```

### `solo_agrotoxicos/`

Articulos de toxicologia o mezclas de compuestos **sin** lipocalina/OBP/CSP como objeto del estudio.

| Entrada | Resultado tipico | Resultado no esperado |
|---------|------------------|------------------------|
| `acute_toxicity_atrazine.pdf` | Metadatos y agrotoxicos con SMILES/LogP | Proteinas del dominio del TP y homologos humanos |

```powershell
tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\casos\solo_agro
```

### `otros/`

Material adicional (preprint, supporting information, dominio mixto). No son casos de referencia del dominio principal del TP.

| Archivo | Nota |
|---------|------|
| `fbioe-11-1193454.pdf` | Material local extra |
| `2020.01.28.922179v1.full.pdf` | Preprint / dominio mixto |
| `jf6c01650_si_001.pdf` | Supporting information |

### DOI sin PDF

Si el publisher no entrega el PDF (p. ej. HTTP 403), la salida conserva metadatos de Crossref y deja vacias las secciones que dependen del texto completo.

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\casos\fallback
```

DOI open-access adicionales (proteina + agro si el PDF es accesible):  
`10.3389/ftox.2021.627470`, `10.3389/fphys.2018.01729`, `10.3389/fphys.2022.924750`.

---

## Casos de referencia sugeridos

Para cubrir tipos de resultado distintos:

1. Proteina + agrotoxico — DOI Frontiers OBP *Tribolium* (arriba).
2. Proteina + homologos humanos — `proteina_y_homologos/in-11-342.pdf` con BLAST local.
3. Solo agrotoxicos o DOI sin PDF — `solo_agrotoxicos` o DOI ACS.
