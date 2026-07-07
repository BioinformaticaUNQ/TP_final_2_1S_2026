# DOIs para casos de prueba

Estos DOI tienen PDF accesible desde Crossref/Frontiers y sirven para probar el flujo:

```powershell
.\.venv_test\Scripts\tp-bioinfo.exe <DOI> --skip-blast --output-dir output\doi_test --pdf-dir output\doi_test\pdfs
```

Usar `--skip-blast` para pruebas rapidas de descarga, parser y APIs de metadatos/compuestos. Para probar homologos, quitar `--skip-blast` o usar `--blast-mode local` si BLAST local esta configurado.

## Recomendados

| DOI | Que deberia validar | Resultado observado |
| --- | --- | --- |
| `10.3389/fphys.2020.00819` | Descarga PDF, detecta OBP/CSP y pesticidas | 2 proteinas, 3 agrotoxicos |
| `10.3389/ftox.2021.627470` | Descarga PDF, detecta OBP/CSP y deltamethrin | 2 proteinas, 1 agrotoxico |
| `10.3389/fphys.2018.01729` | Descarga PDF, detecta chemosensory protein y varios agrotoxicos | 1 proteina, 7 agrotoxicos |
| `10.3389/fphys.2022.924750` | Descarga PDF, detecta CSP/OBP y pesticidas | 2 proteinas, 2 agrotoxicos |

## Comandos listos

```powershell
.\.venv_test\Scripts\tp-bioinfo.exe 10.3389/fphys.2020.00819 --skip-blast --output-dir output\doi_test_00819 --pdf-dir output\doi_test_00819\pdfs

.\.venv_test\Scripts\tp-bioinfo.exe 10.3389/ftox.2021.627470 --skip-blast --output-dir output\doi_test_627470 --pdf-dir output\doi_test_627470\pdfs

.\.venv_test\Scripts\tp-bioinfo.exe 10.3389/fphys.2018.01729 --skip-blast --output-dir output\doi_test_01729 --pdf-dir output\doi_test_01729\pdfs

.\.venv_test\Scripts\tp-bioinfo.exe 10.3389/fphys.2022.924750 --skip-blast --output-dir output\doi_test_924750 --pdf-dir output\doi_test_924750\pdfs
```

## DOIs utiles pero con PDF bloqueado

Estos articulos son relevantes por tema, pero el publisher puede devolver HTTP 403 al intentar descargar el PDF automaticamente. Sirven para validar el fallback a metadatos Crossref, no para el flujo completo con parser:

| DOI | Motivo |
| --- | --- |
| `10.1021/acs.jafc.4c03368` | CSP e insecticida, PDF de ACS bloqueado |
| `10.1021/acs.jafc.2c05973` | CSP e insecticida, PDF de ACS bloqueado |
| `10.1002/arch.21148` | CSP e insecticida, PDF de Wiley bloqueado |

