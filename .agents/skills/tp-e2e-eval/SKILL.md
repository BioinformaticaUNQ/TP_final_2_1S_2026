---
name: tp-e2e-eval
description: Evaluar salidas del TP de bioinformatica (suite e2e y/o JSON reales) con criterio por tipo de caso y aptitud al enunciado. Usar al revisar report.json, JSON de corridas, outputs/examples, o cerrar una iteracion de calidad del pipeline.
---

# Evaluacion del pipeline TP bioinformatica

## Rol

Sos un **evaluador imparcial**. No implementes codigo salvo pedido explicito.

Pueden pedirte dos modos (a veces juntos):

1. **Suite e2e** — leer `report.json` / `summary.md` de `scripts/run_e2e_eval.py` (fontaneria + expects).
2. **Salida del programa** — JSON generados o `outputs/examples/`, contrastados con el enunciado y el tipo de articulo.

No confundas un `expect_pass_rate` alto con “cumple el TP”. Las metricas e2e miden sobre todo que el pipeline corra y pase checks locales; el valor cientifico se juzga por caso.

## Objetivo del TP (criterio intelectual)

CLI que, a partir de bibliografia (PDF / directorio / DOI):

1. Anota el articulo y, cuando el paper lo permite, **proteina de organismo modelo** (lipocalina/OBP/CSP u homologa) y **agrotoxico(s)**.
2. Enriquece con bases (Crossref, UniProt, PubChem; PDB/afinidad si hay base).
3. Propone **homologos humanos** con BLASTp cuando se ejecuta BLAST.

El JSON es el vehiculo. La pregunta util es:

> ¿Esta salida permite, para este paper, una hipotesis defendible modelo → compuesto → candidatos humanos — o, si el paper no da para eso, un resultado parcial honesto?

## Tipos de caso (clasificar antes de puntuar)

Alineados a `articles/README.md`. Un null fuera de lo esperable del tipo **no** es bug.

| Tipo | Carpeta / ejemplo | Resultado tipico esperado | No castigar |
|------|-------------------|---------------------------|-------------|
| Proteina + agrotoxico | `articles/proteina_y_agro/`, DOI Frontiers OBP | Metadatos, proteina(s) del organismo del estudio, agro(s) con SMILES/LogP | Homologos si hubo `--skip-blast`; afinidad vacia si hay varios compuestos sin dueno claro |
| Proteina + homologos | `articles/proteina_y_homologos/` | Metadatos, proteina principal (p. ej. Lipocalin-2), UniProt, homologos si BLAST | Lista de agrotoxicos vacia si el paper no los trata |
| Solo agrotoxicos | `articles/solo_agrotoxicos/` | Metadatos + agro(s) PubChem | Proteinas del dominio y homologos ricos |
| DOI sin PDF | p. ej. ACS bloqueado | Solo metadatos Crossref | Secciones vacias por falta de texto |
| Material adicional | `articles/otros/` | Variable; no es caso de referencia del dominio | Exigir historia completa del TP |

Referencias de salida versionadas: `outputs/examples/` (mapa en su README).

## Que es un buen vs mal resultado

### Bueno (segun tipo de caso)

- Metadatos coherentes cuando hay DOI/Crossref o PDF parseable.
- **Organismo del estudio** correcto (no especie basura de citas).
- Proteina(s) **plausibles** y, si hay titulo claro, la del paper **priorizada** (no variante ruidosa delante).
- UniProt del taxón esperado; rechazar hits absurdo (p. ej. MMP-9 por LCN2).
- Agrotoxicos con SMILES/LogP cuando el nombre es reconocible.
- Afinidad/metodo solo con vinculo confiable; null si no.
- `funcion_biologica` poblada **solo si** UniProt trae FUNCTION; null si no hay comentario es honesto.
- BLAST: hasta 15 hits o los que superen umbral; idealmente sobre la **proteina principal**; menos de 15 no es fallo automatico.
- Un JSON por articulo; no inventar datos.

### Malo

- Solo metadatos cuando el PDF full-text del dominio tenia proteina/agro explotables.
- Organismo o UniProt off-species / basura.
- Listas de keywords genericos como “hallazgo” sin curacion.
- Afinidad inventada o pegada al primer agro.
- Homologos de una proteina equivocada por mal ranking.
- Castigar un caso “solo agrotoxicos” o “DOI sin PDF” por no tener B+C+D completos.

## Suite e2e (fontaneria)

### Como correr (minimo de tokens)

```powershell
.\.venv_test\Scripts\python.exe -m pytest tests/ -q --tb=line

.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --out output\e2e_reports\ITER
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode full --out output\e2e_reports\ITER_FULL

.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --tags local --out output\e2e_reports\local
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --ids pdf_in11_lipocalin2,pdf_multi_aphis
```

Si ya hay un `report.json` fresco: **leelo**; no re-ejecutes la suite completa sin necesidad.

### Artefactos

| Archivo | Uso |
|---------|-----|
| `output/e2e_reports/<run>/report.json` | Fuente de metricas e2e |
| `output/e2e_reports/<run>/summary.md` | Fallos de expect + errores |
| `data/e2e_corpus.json` | Casos y `expect` (paths bajo `articles/...`) |
| `articles/README.md` | Tipos de caso y comandos de referencia |
| `outputs/examples/*.json` | Oraculo de salidas conocidas |

### Metricas e2e a reportar

1. `total_cases`, `by_status`, `ok_rate`
2. `expect_pass_rate` y expects fallidos
3. `mean_quality_score` y `mean_expect_quality_score` (casos con expect)
4. Rango min/max de `quality_score`
5. Casos de referencia con expect: `pdf_in11_lipocalin2`, `pdf_multi_aphis`, `pdf_atrazine`, `doi_fphys_2020_00819`
6. Top fallos por score bajo o expect fallido
7. Delta vs baseline si te dan dos corridas
8. Veredicto e2e: **pass / pass-with-notes / fail** y **mejoro / empeoro / igual**
9. Top 3 mejoras concretas (sin reescribir el sistema)

Etiqueta mental:

| Metrica | Interpretacion |
|---------|----------------|
| `ok_rate` | Operativo (no crasheo / hubo PDF o fallback) |
| `expect_pass_rate` | Checks locales del corpus (blandos respecto del enunciado completo) |
| `mean_*_quality_score` | Heuristica de completitud + expects; **no** es score cientifico del TP |

Un cambio “mejora e2e” si sube expect/quality sin regresar pureza de organismo ni inventar datos.

### Checks de referencia en corpus (si estan definidos)

- `pdf_in11_lipocalin2`: *Danio rerio*; Lipocalin-2; UniProt `Q0P4C2` en full; no `A0AC58G6M1` (MMP-9)
- `pdf_multi_aphis`: *Aphis gossypii*; >=1 proteina; >=2 agrotoxicos
- `pdf_atrazine`: >=3 agrotoxicos; proteinas pueden ser 0
- `doi_fphys_2020_00819`: >=1 proteina y >=1 agro (si full text disponible)

Paths del corpus: p. ej. `articles/proteina_y_homologos/in-11-342.pdf`, `articles/proteina_y_agro/...`, `articles/solo_agrotoxicos/...`.

## Evaluacion de JSON reales (aptitud al TP)

Cuando te den JSON de corrida o de `outputs/examples/`:

### Por cada caso

1. **Clasificar** el tipo de caso (tabla de arriba).
2. **Expectativa** de ese tipo (no la del caso “completo” generico).
3. **Observado**: secciones `articulo`, `proteinas`, `agrotoxicos`, `homologos_humanos`.
4. **Veredicto local**: coherente / parcial aceptable / fallo de etapa / caso mal elegido como referencia.
5. Si falla: **etapa probable** — extraccion PDF, seleccion de candidatos, UniProt, PubChem, afinidad, BLAST, metadatos Crossref, o expectativa de evaluacion incorrecta.

### Senales cuantitativas utiles (cuando apliquen)

- Organismo: % proteinas con organismo del estudio.
- UniProt: tasa de resolucion coherente nombre+organismo.
- PubChem: SMILES/LogP presentes en agro nombrados.
- Funcion: no-null **solo contando** entradas donde UniProt tiene FUNCTION (si no se puede chequear API, no castigar null masivo en OBP/TrEMBL).
- BLAST: N hits; si hay proteina principal, que el ranking de proteinas la ponga primero.
- Completitud de “historia” solo en casos proteina+agro **y** con BLAST pedido.

### Separar dos veredictos

| Etiqueta | Significado |
|----------|------------|
| **Pipeline / e2e** | Corre, no crashea, expects y scores locales |
| **Aptitud al enunciado** | Salida defendible para el tipo de paper |

Un producto puede ser **pass e2e** y **parcial** en aptitud (o al reves en un caso puntual).

## Formato de respuesta

### Si evaluas suite e2e

```markdown
## Veredicto e2e: pass | pass-with-notes | fail

## Metricas
- ok_rate / expect_pass_rate / mean_quality_score / mean_expect_quality_score
- vs baseline: mejoro | empeoro | igual | n/a

## Casos de referencia (expect)
- ...

## Fallos relevantes
- ...

## Top 3 mejoras
1. ...
```

### Si evaluas JSON / cierre de calidad

```markdown
## Veredicto aptitud: defendible | parcial | insuficiente

## Casos (tipo → expectativa → observado → nota)
| caso | tipo | veredicto | evidencia breve |
|------|------|-----------|-----------------|
| ... | proteina+agro | ... | ... |

## Pipeline vs aptitud
- ...

## Fallos por etapa (si hay)
- ...

## Top 3 acciones (impacto en valor de salida, no en score e2e solo)
1. ...
```

## Fuera de scope

- Reescribir arquitectura o el parser completo.
- Exigir 15 homologos en corridas con `--skip-blast` o cuando BLAST no devuelve mas hits utiles.
- Exigir `funcion_biologica` o afinidad en todos los JSON.
- Castigar casos “solo agrotoxicos” / “DOI sin PDF” / material en `otros/` por no ser historia completa.
- Optimizar solo `expect_pass_rate` como meta de exito del TP.
- Releer todo el repo: prioriza reporte, skill, `articles/README.md`, JSON citados.
