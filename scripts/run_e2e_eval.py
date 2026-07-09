#!/usr/bin/env python
"""Suite e2e del TP: corre casos del corpus y escribe un reporte JSON evaluable.

Modos:
  candidates  — parse + CandidatosArticulo (evalua parser/ranking; requiere PDF)
  full        — pipeline app sin BLAST (metadatos + UniProt + PubChem)

Uso (desde la raiz del repo, con paquete instalado o PYTHONPATH=src):

  python scripts/run_e2e_eval.py --mode candidates --out output/e2e_reports/baseline
  python scripts/run_e2e_eval.py --mode full --limit 10 --out output/e2e_reports/smoke
  python scripts/run_e2e_eval.py --tags local,oa --mode candidates
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import asdict, is_dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_corpus(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _filter_cases(cases: list[dict], tags: set[str] | None, limit: int | None, ids: set[str] | None):
    selected = cases
    if ids:
        selected = [c for c in selected if c["id"] in ids]
    if tags:
        selected = [c for c in selected if tags.intersection(c.get("tags") or [])]
    if limit is not None:
        selected = selected[:limit]
    return selected


def _safe_name(case_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in case_id)


def _resolve_pdf_source(case: dict) -> Path | bytes | None:
    kind = case["kind"]
    source = case["source"]
    if kind == "pdf":
        path = ROOT / source
        if not path.exists():
            return None
        return path
    if kind == "doi":
        from services.crossref_service import fetch_pdf_bytes

        return fetch_pdf_bytes(source)
    raise ValueError(f"kind desconocido: {kind}")


def _candidatos_to_dict(candidatos) -> dict:
    afinidades = []
    for a in candidatos.afinidades:
        afinidades.append(
            {
                "tipo": a.tipo,
                "valor": a.valor,
                "unidad": a.unidad,
                "agrotoxico": a.agrotoxico,
            }
        )
    return {
        "organismo_principal": candidatos.organismo_principal,
        "organismos_secundarios": list(candidatos.organismos_secundarios),
        "proteinas": list(candidatos.proteinas),
        "agrotoxicos": list(candidatos.agrotoxicos),
        "familias_agrotoxicos": dict(candidatos.familias_agrotoxicos),
        "afinidades": afinidades,
        "metodos_experimentales": list(candidatos.metodos_experimentales),
        "codigos_pdb": list(candidatos.codigos_pdb),
    }


def _run_candidates(case: dict) -> dict:
    from services.candidatos_articulo import build_candidatos_articulo
    from utils.pdf_parser import parse_pdf

    started = time.monotonic()
    source = _resolve_pdf_source(case)
    if source is None:
        return {
            "status": "error",
            "error": "pdf_no_disponible",
            "elapsed_s": round(time.monotonic() - started, 2),
        }

    extraido = parse_pdf(source)
    candidatos = build_candidatos_articulo(extraido)
    elapsed = round(time.monotonic() - started, 2)

    return {
        "status": "ok",
        "elapsed_s": elapsed,
        "pdf_bytes": isinstance(source, (bytes, bytearray)),
        "extracted": {
            "doi": extraido.doi,
            "titulo": extraido.titulo,
            "organismos_raw": list(extraido.organismos),
            "proteinas_raw": list(extraido.proteinas_candidatas),
            "agrotoxicos_raw": list(extraido.agrotoxicos_candidatos),
            "n_afinidades_raw": len(extraido.afinidades),
        },
        "candidatos": _candidatos_to_dict(candidatos),
    }


def _run_full(case: dict, out_dir: Path) -> dict:
    from app import build_resultado_desde_pdf
    from services.candidatos_articulo import build_candidatos_articulo
    from services.crossref_service import fetch_doi, fetch_pdf_bytes
    from utils.pdf_parser import parse_pdf

    started = time.monotonic()
    kind = case["kind"]
    source = case["source"]
    case_out = out_dir / "json" / _safe_name(case["id"])
    case_out.mkdir(parents=True, exist_ok=True)
    pdf_source: Path | bytes | None = None

    if kind == "pdf":
        path = ROOT / source
        if not path.exists():
            return {
                "status": "error",
                "error": "pdf_missing",
                "elapsed_s": round(time.monotonic() - started, 2),
            }
        pdf_source = path
        resultado = build_resultado_desde_pdf(path, ejecutar_blast=False)
        payload = resultado.to_dict()
        (case_out / f"{path.stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        pdf_bytes = fetch_pdf_bytes(source)
        if pdf_bytes is None:
            articulo = fetch_doi(source)
            payload = {
                "articulo": {
                    "doi": articulo.doi if articulo else source,
                    "titulo": articulo.titulo if articulo else None,
                    "autores": articulo.autores if articulo else [],
                    "anio": articulo.anio if articulo else None,
                    "revista": articulo.revista if articulo else None,
                },
                "proteinas": [],
                "agrotoxicos": [],
                "homologos_humanos": [],
                "metadata_only": True,
            }
            (case_out / "metadata_only.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {
                "status": "metadata_only",
                "elapsed_s": round(time.monotonic() - started, 2),
                "resultado": payload,
            }
        pdf_source = pdf_bytes
        resultado = build_resultado_desde_pdf(pdf_bytes, ejecutar_blast=False)
        payload = resultado.to_dict()
        safe = source.replace("/", "_")
        (case_out / f"{safe}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    candidatos = None
    if pdf_source is not None:
        candidatos = build_candidatos_articulo(parse_pdf(pdf_source))

    organismos = sorted(
        {
            p.get("organismo")
            for p in (payload.get("proteinas") or [])
            if p.get("organismo")
        }
    )
    if candidatos and candidatos.organismo_principal:
        if candidatos.organismo_principal not in organismos:
            organismos = [candidatos.organismo_principal, *organismos]

    return {
        "status": "ok",
        "elapsed_s": round(time.monotonic() - started, 2),
        "resultado": {
            "articulo": payload.get("articulo"),
            "n_proteinas": len(payload.get("proteinas") or []),
            "n_agrotoxicos": len(payload.get("agrotoxicos") or []),
            "proteinas": payload.get("proteinas") or [],
            "agrotoxicos": [
                {
                    "nombre_comun": a.get("nombre_comun"),
                    "familia_quimica": a.get("familia_quimica"),
                    "smiles": bool(a.get("smiles")),
                    "logP": a.get("logP"),
                    "tipo_afinidad": a.get("tipo_afinidad"),
                }
                for a in (payload.get("agrotoxicos") or [])
            ],
            "organismos": organismos,
            "organismo_principal": candidatos.organismo_principal if candidatos else None,
            "proteinas_candidatas": list(candidatos.proteinas) if candidatos else [],
            "uniprot_ids": [
                p.get("uniprot_id")
                for p in (payload.get("proteinas") or [])
                if p.get("uniprot_id")
            ],
        },
    }


def _score_expectations(case: dict, result: dict) -> dict:
    expect = case.get("expect") or {}
    if not expect:
        return {"has_expect": False, "checks": [], "passed": None, "failed": []}

    checks = []
    failed = []

    def ok(name: str, cond: bool, detail: str = ""):
        checks.append({"name": name, "ok": cond, "detail": detail})
        if not cond:
            failed.append(name)

    status = result.get("status")
    if expect.get("allow_metadata_only") and status == "metadata_only":
        ok("metadata_only_allowed", True)
        return {"has_expect": True, "checks": checks, "passed": len(failed) == 0, "failed": failed}

    if status not in {"ok", "metadata_only"}:
        ok("status_ok", False, status)
        return {"has_expect": True, "checks": checks, "passed": False, "failed": failed}

    if "candidatos" in result:
        cand = result["candidatos"]
        org = cand.get("organismo_principal")
        prots = cand.get("proteinas") or []
        agros = cand.get("agrotoxicos") or []
        if "organism_any_of" in expect:
            ok(
                "organism_any_of",
                org in expect["organism_any_of"],
                f"got={org}",
            )
        if "min_agrotoxicos" in expect:
            ok(
                "min_agrotoxicos",
                len(agros) >= expect["min_agrotoxicos"],
                f"got={len(agros)}",
            )
        if "min_proteinas" in expect:
            ok(
                "min_proteinas",
                len(prots) >= expect["min_proteinas"],
                f"got={len(prots)}",
            )
        if "protein_name_any_of" in expect:
            ok(
                "protein_name_any_of",
                any(p in expect["protein_name_any_of"] for p in prots),
                f"got={prots[:5]}",
            )
    elif "resultado" in result:
        res = result["resultado"]
        orgs = res.get("organismos") or []
        if res.get("articulo") and res["articulo"].get("organismo"):
            orgs = list(orgs) + [res["articulo"]["organismo"]]
        protein_names = [p.get("nombre") for p in (res.get("proteinas") or [])]
        uniprots = res.get("uniprot_ids") or []
        n_agro = res.get("n_agrotoxicos", len(res.get("agrotoxicos") or []))
        n_prot = res.get("n_proteinas", len(res.get("proteinas") or []))

        if "organism_any_of" in expect:
            ok(
                "organism_any_of",
                any(o in expect["organism_any_of"] for o in orgs)
                or any(
                    expect_org in " ".join(orgs)
                    for expect_org in expect["organism_any_of"]
                ),
                f"got={orgs}",
            )
        if "min_agrotoxicos" in expect:
            ok("min_agrotoxicos", n_agro >= expect["min_agrotoxicos"], f"got={n_agro}")
        if "min_proteinas" in expect:
            ok("min_proteinas", n_prot >= expect["min_proteinas"], f"got={n_prot}")
        if "protein_name_any_of" in expect:
            ok(
                "protein_name_any_of",
                any(n in expect["protein_name_any_of"] for n in protein_names if n),
                f"got={protein_names}",
            )
        if "uniprot_any_of" in expect:
            ok(
                "uniprot_any_of",
                any(u in expect["uniprot_any_of"] for u in uniprots),
                f"got={uniprots}",
            )
        if "forbid_uniprot" in expect:
            bad = [u for u in uniprots if u in expect["forbid_uniprot"]]
            ok("forbid_uniprot", not bad, f"bad={bad}")

    return {
        "has_expect": True,
        "checks": checks,
        "passed": len(failed) == 0,
        "failed": failed,
    }


def _summarize(results: list[dict]) -> dict:
    total = len(results)
    by_status: dict[str, int] = {}
    expect_total = 0
    expect_pass = 0
    for r in results:
        st = r.get("result", {}).get("status", "missing")
        by_status[st] = by_status.get(st, 0) + 1
        sc = r.get("score") or {}
        if sc.get("has_expect"):
            expect_total += 1
            if sc.get("passed"):
                expect_pass += 1

    return {
        "total_cases": total,
        "by_status": by_status,
        "expect_cases": expect_total,
        "expect_passed": expect_pass,
        "expect_pass_rate": (expect_pass / expect_total) if expect_total else None,
        "ok_rate": (by_status.get("ok", 0) / total) if total else 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suite e2e TP bioinfo")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "data" / "e2e_corpus.json",
    )
    parser.add_argument(
        "--mode",
        choices=("candidates", "full"),
        default="candidates",
        help="candidates=parser+ranking; full=pipeline sin BLAST",
    )
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "e2e_reports" / "latest")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--tags", type=str, default=None, help="csv de tags, ej local,oa")
    parser.add_argument("--ids", type=str, default=None, help="csv de case ids")
    args = parser.parse_args(argv)

    corpus = _load_corpus(args.corpus)
    tags = {t.strip() for t in args.tags.split(",")} if args.tags else None
    ids = {i.strip() for i in args.ids.split(",")} if args.ids else None
    cases = _filter_cases(corpus.get("cases") or [], tags, args.limit, ids)

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, case in enumerate(cases, start=1):
        print(f"[{idx}/{len(cases)}] {case['id']} ({case['kind']}: {case['source']})")
        try:
            if args.mode == "candidates":
                result = _run_candidates(case)
            else:
                result = _run_full(case, out_dir)
        except Exception as exc:
            result = {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=5),
            }
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  -> {result.get('status')} ({result.get('elapsed_s', '?')}s)")

        score = _score_expectations(case, result)
        results.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "source": case["source"],
                "tags": case.get("tags") or [],
                "expect": case.get("expect"),
                "result": result,
                "score": score,
            }
        )

    report = {
        "mode": args.mode,
        "corpus": str(args.corpus),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": _summarize(results),
        "cases": results,
    }
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = out_dir / "summary.md"
    s = report["summary"]
    lines = [
        f"# E2E report ({args.mode})",
        "",
        f"- total: {s['total_cases']}",
        f"- by_status: `{json.dumps(s['by_status'])}`",
        f"- ok_rate: {s['ok_rate']}",
        f"- expect_pass_rate: {s['expect_pass_rate']}",
        "",
        "## Failed expectations",
        "",
    ]
    for r in results:
        sc = r.get("score") or {}
        if sc.get("has_expect") and sc.get("passed") is False:
            lines.append(f"- **{r['id']}**: failed `{sc.get('failed')}`")
    lines.append("")
    lines.append("## Errors")
    lines.append("")
    for r in results:
        if r.get("result", {}).get("status") == "error":
            lines.append(f"- **{r['id']}**: {r['result'].get('error')}")
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(json.dumps(s, indent=2))
    print(f"report: {report_path}")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
