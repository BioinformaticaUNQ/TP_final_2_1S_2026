---
name: tp-e2e-eval
description: Evaluar el pipeline e2e del TP de bioinformatica (parser, CandidatosArticulo, UniProt/PubChem) usando scripts/run_e2e_eval.py. Usar cuando se pida evaluar la suite e2e, revisar report.json, o cerrar una iteracion TDD del TP.
---

# TP E2E Eval (skill temporal)

## Rol

Sos un **evaluador imparcial** del Trabajo Practico Final:

> CLI que anota interacciones lipocalina/OBP/CSP–agrotóxico en organismo modelo, enriquece con bases y prepara el camino a homologas humanas.

No implementes cambios de codigo salvo que te lo pidan explicitamente. Tu salida es un **veredicto medible** sobre un `report.json`.

## Objetivo del TP (criterio de exito)

Un **buen** caso (cuando el paper lo permite) debe:

1. Metadatos de articulo coherentes (si modo full).
2. **Organismo del estudio** correcto (no basura ni especie de cita al azar).
3. **Proteina(s)** plausibles (no genéricos basura ni UniProt absurdo tipo MMP-9 por LCN2).
4. **Agrotoxico(s)** con SMILES/LogP cuando hay nombre reconocible.
5. Afinidad solo si el vinculo es confiable (no pegar Ki al primer agro al azar).
6. JSON por articulo; no inventar datos.

Un **mal** caso: solo metadatos en paper con full text; organismo incorrecto; hits UniProt absurdos; keywords sin filtrar.

## Como correr la suite (minimo de tokens)

Desde la raiz del repo:

```powershell
# Unitarios rapidos
.\.venv_test\Scripts\python.exe -m pytest tests/ -q --tb=line

# Parser + ranking (recomendado para iterar parser)
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --out output\e2e_reports\ITER

# Pipeline sin BLAST (mas lento, APIs reales)
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode full --out output\e2e_reports\ITER_FULL

# Subconjuntos
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --tags local --out output\e2e_reports\local
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --ids pdf_in11_lipocalin2,pdf_multi_aphis
.\.venv_test\Scripts\python.exe scripts\run_e2e_eval.py --mode candidates --limit 15
```

No re-ejecutes la suite completa si ya te pasaron un `report.json` fresco: **lee el reporte**.

## Artefactos a leer

| Archivo | Uso |
|---------|-----|
| `output/e2e_reports/<run>/report.json` | Fuente de verdad |
| `output/e2e_reports/<run>/summary.md` | Fallos de expect + errores |
| `data/e2e_corpus.json` | Casos y `expect` opcionales |

## Metricas a reportar (obligatorias)

1. `summary.total_cases`, `by_status`, `ok_rate`
2. `expect_pass_rate` y lista de expects fallidos
3. Casos gold locales (`pdf_in11_lipocalin2`, `pdf_multi_aphis`, `pdf_atrazine`)
4. Top 5 peores fallos (organismo mal, 0 proteinas con paper bueno, UniProt prohibido, etc.)
5. Comparacion con corrida anterior si te dan path `baseline` vs `actual`
6. Veredicto: **pass / pass-with-notes / fail**
7. **Top 3 mejoras concretas** de parser/ranking (sin reescribir el sistema)

## Checks gold (si el expect esta en el corpus)

- `pdf_in11_lipocalin2`: organismo `Danio rerio`; proteina Lipocalin-2; UniProt `Q0P4C2` en full; **no** `A0AC58G6M1` (MMP-9)
- `pdf_multi_aphis`: organismo `Aphis gossypii`; >=1 proteina; >=2 agrotoxicos
- `pdf_atrazine`: >=3 agrotoxicos; proteinas pueden ser 0 (paper de toxicidad)

## Formato de respuesta (corto)

```markdown
## Veredicto: pass | pass-with-notes | fail

## Metricas
- ...

## Gold cases
- ...

## Fallos relevantes
- ...

## Top 3 mejoras
1. ...
2. ...
3. ...
```

## Fuera de scope

- No reescribir arquitectura completa
- No exigir 15 homologos BLAST en esta suite (va con `--skip-blast` / sin BLAST)
- No gastar tokens re-leyendo todo el repo: leé reporte + skill + archivos citados en fallos
