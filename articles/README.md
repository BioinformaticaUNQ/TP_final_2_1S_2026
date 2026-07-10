# Papers de prueba y demo

Los PDFs estan agrupados por **que se espera del resultado**, no por "calidad del paper".
Usar esta guia en la oral para no mostrar el caso equivocado.

Cada corrida genera un JSON con cuatro secciones (cuando el paper y las APIs lo permiten):

| Seccion del JSON | Contenido |
|------------------|-----------|
| `articulo` | DOI, titulo, autores, anio, revista |
| `proteinas` | Proteina del organismo modelo, UniProt, funcion si existe |
| `agrotoxicos` | Compuestos, familia, SMILES, LogP; afinidad solo si el texto la trae con dueno claro |
| `homologos_humanos` | Hits BLASTp contra proteoma humano |

---

## Carpetas

### `proteina_y_agro/` — proteina + agrotoxico

Lo mas cercano al dominio del TP: OBP/CSP (u homologas) e insecticidas.

| Entrada | Organismo esperado | Que deberia salir | Que no exigir |
|---------|--------------------|-------------------|---------------|
| `1-s2.0-S0147651325015556-main.pdf` | *Aphis gossypii* | Metadatos, varias OBP/CSP, varios agrotoxicos con PubChem | Homologos si usas `--skip-blast`; afinidad puede quedar vacia (varios compuestos) |
| DOI `10.3389/fphys.2020.00819` (se descarga, no hay PDF local) | *Tribolium castaneum* | Metadatos, OBP, pesticidas con PubChem | Homologos con `--skip-blast` |

```powershell
tp-bioinfo 10.3389/fphys.2020.00819 --skip-blast --no-save-pdf --output-dir output\demo\proteina_agro
tp-bioinfo articles\proteina_y_agro\1-s2.0-S0147651325015556-main.pdf --skip-blast --output-dir output\demo\proteina_agro_aphis
```

### `proteina_y_homologos/` — proteina + BLAST a humanos

Lipocalina en organismo modelo. El paper **no** es de agrotoxicos.

| Entrada | Organismo esperado | Que deberia salir | Que no exigir |
|---------|--------------------|-------------------|---------------|
| `in-11-342.pdf` | *Danio rerio* | Metadatos, Lipocalin-2 prioritario, UniProt, homologos con `--blast-mode local` | Agrotoxicos (lista vacia es correcta) |

```powershell
tp-bioinfo articles\proteina_y_homologos\in-11-342.pdf --blast-mode local --output-dir output\demo\homologos
```

### `solo_agrotoxicos/` — solo compuestos

Toxicologia / mezclas: **no** hay lipocalina u OBP del estudio.

| Entrada | Que deberia salir | Que no exigir |
|---------|-------------------|---------------|
| `acute_toxicity_atrazine.pdf` | Metadatos y varios agrotoxicos con SMILES/LogP | Proteinas de la familia ni homologos humanos ricos |

Sirve para mostrar **honestidad**: el sistema no inventa proteinas.

```powershell
tp-bioinfo articles\solo_agrotoxicos\acute_toxicity_atrazine.pdf --skip-blast --output-dir output\demo\solo_agro
```

### `otros/` — no usar como demo principal

Material de apoyo, supporting information o dominio mixto. Pueden parsear algo, pero **no** representan el caso ideal del TP.

| Archivo | Nota |
|---------|------|
| `fbioe-11-1193454.pdf` | Material local extra |
| `2020.01.28.922179v1.full.pdf` | Preprint / dominio mixto |
| `jf6c01650_si_001.pdf` | Supporting information |

### DOI sin PDF (solo metadatos)

Cuando el publisher bloquea el PDF, el JSON tiene metadatos de Crossref y el resto vacio. Eso es **correcto**, no un crash.

```powershell
tp-bioinfo 10.1021/acs.jafc.4c03368 --skip-blast --no-save-pdf --output-dir output\demo\fallback
```

Otros DOI open-access utiles (proteina + agro si el PDF baja):  
`10.3389/ftox.2021.627470`, `10.3389/fphys.2018.01729`, `10.3389/fphys.2022.924750`.

---

## Orden sugerido de la oral (3 corridas)

1. **Proteina + agro** — DOI Frontiers OBP *Tribolium* (arriba).
2. **Proteina + homologos humanos** — `proteina_y_homologos/in-11-342.pdf` con BLAST local.
3. **Limite del sistema** — `solo_agrotoxicos` **o** DOI ACS (salida pobre a proposito).

No presentar un paper de `otros/` como si fuera el caso "completo" del TP.
