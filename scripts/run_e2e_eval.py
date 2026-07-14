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


def _extract_case_signals(result: dict) -> dict:
    """Normaliza señales usadas por expects y quality_score."""
    status = result.get("status")
    if "candidatos" in result:
        cand = result["candidatos"]
        return {
            "status": status,
            "organismo": cand.get("organismo_principal"),
            "proteinas": list(cand.get("proteinas") or []),
            "n_proteinas": len(cand.get("proteinas") or []),
            "agrotoxicos": list(cand.get("agrotoxicos") or []),
            "n_agrotoxicos": len(cand.get("agrotoxicos") or []),
            "uniprot_ids": [],
            "protein_names": list(cand.get("proteinas") or []),
            "smiles_ok": None,
        }

    res = result.get("resultado") or {}
    prots = res.get("proteinas") or []
    agros = res.get("agrotoxicos") or []
    orgs = list(res.get("organismos") or [])
    if res.get("organismo_principal") and res["organismo_principal"] not in orgs:
        orgs.insert(0, res["organismo_principal"])
    smiles_flags = [bool(a.get("smiles")) for a in agros if isinstance(a, dict)]
    return {
        "status": status,
        "organismo": res.get("organismo_principal") or (orgs[0] if orgs else None),
        "organismos": orgs,
        "proteinas": prots,
        "n_proteinas": res.get("n_proteinas", len(prots)),
        "agrotoxicos": agros,
        "n_agrotoxicos": res.get("n_agrotoxicos", len(agros)),
        "uniprot_ids": list(res.get("uniprot_ids") or []),
        "protein_names": [
            p.get("nombre") for p in prots if isinstance(p, dict) and p.get("nombre")
        ],
        "smiles_ok": (sum(smiles_flags) / len(smiles_flags)) if smiles_flags else None,
    }


def _quality_score(case: dict, result: dict, expect_score: dict) -> dict:
    """
    Score continuo 0..1 por caso.
    - Con expects: fraccion de checks OK (mas fiable).
    - Sin expects: heuristica de completitud del analisis.
    """
    components: dict[str, float] = {}
    signals = _extract_case_signals(result)
    status = signals["status"]

    if status == "error":
        return {"quality_score": 0.0, "components": {"status": 0.0}, "kind": "error"}
    if status == "metadata_only":
        # Util solo como fallback controlado
        base = 0.35 if (case.get("expect") or {}).get("allow_metadata_only") else 0.15
        return {
            "quality_score": base,
            "components": {"metadata_only": base},
            "kind": "metadata_only",
        }

    if expect_score.get("has_expect") and expect_score.get("checks"):
        checks = expect_score["checks"]
        frac = sum(1 for c in checks if c.get("ok")) / len(checks)
        components["expect_fraction"] = round(frac, 3)
        # Bonus leve por completitud extra
        if signals["n_agrotoxicos"] > 0:
            components["has_agro"] = 0.05
        if signals["n_proteinas"] > 0:
            components["has_prot"] = 0.05
        if signals.get("smiles_ok"):
            components["smiles"] = 0.05 * float(signals["smiles_ok"])
        score = min(1.0, frac * 0.9 + sum(v for k, v in components.items() if k != "expect_fraction"))
        components["expect_fraction"] = round(frac, 3)
        return {
            "quality_score": round(score, 3),
            "components": components,
            "kind": "expect",
        }

    # Heuristica sin gold
    components["status_ok"] = 0.25
    if signals.get("organismo"):
        components["organismo"] = 0.2
    if signals["n_proteinas"] > 0:
        components["proteinas"] = min(0.3, 0.1 + 0.05 * min(signals["n_proteinas"], 4))
    if signals["n_agrotoxicos"] > 0:
        components["agrotoxicos"] = min(0.25, 0.1 + 0.05 * min(signals["n_agrotoxicos"], 3))
    if signals.get("smiles_ok"):
        components["smiles"] = 0.1 * float(signals["smiles_ok"])
    if signals.get("uniprot_ids"):
        components["uniprot"] = min(0.15, 0.05 * len(signals["uniprot_ids"]))

    # Penalizar mezcla de organismos en proteinas (hits off-species)
    prots = signals.get("proteinas") or []
    orgs_hit = {
        p.get("organismo")
        for p in prots
        if isinstance(p, dict) and p.get("organismo")
    }
    principal = signals.get("organismo")
    if principal and orgs_hit:
        off = [o for o in orgs_hit if o and principal.split()[0].lower() not in o.lower()]
        if off:
            components["off_species_penalty"] = -0.15 * min(1.0, len(off) / max(1, len(orgs_hit)))

    score = max(0.0, min(1.0, sum(components.values())))
    return {"quality_score": round(score, 3), "components": components, "kind": "heuristic"}


def _score_expectations(case: dict, result: dict) -> dict:
    expect = case.get("expect") or {}
    signals = _extract_case_signals(result)

    if not expect:
        quality = _quality_score(case, result, {"has_expect": False})
        return {
            "has_expect": False,
            "checks": [],
            "passed": None,
            "failed": [],
            **quality,
        }

    checks = []
    failed = []

    def ok(name: str, cond: bool, detail: str = ""):
        checks.append({"name": name, "ok": cond, "detail": detail})
        if not cond:
            failed.append(name)

    status = result.get("status")
    if expect.get("allow_metadata_only") and status == "metadata_only":
        ok("metadata_only_allowed", True)
        base = {
            "has_expect": True,
            "checks": checks,
            "passed": True,
            "failed": [],
        }
        quality = _quality_score(case, result, base)
        return {**base, **quality}

    if status not in {"ok", "metadata_only"}:
        ok("status_ok", False, str(status))
        base = {
            "has_expect": True,
            "checks": checks,
            "passed": False,
            "failed": failed,
        }
        quality = _quality_score(case, result, base)
        return {**base, **quality}

    org = signals.get("organismo")
    orgs = signals.get("organismos") or ([org] if org else [])
    prots = signals.get("proteinas") or []
    protein_names = signals.get("protein_names") or []
    uniprots = signals.get("uniprot_ids") or []
    n_agro = signals["n_agrotoxicos"]
    n_prot = signals["n_proteinas"]

    if "organism_any_of" in expect:
        ok(
            "organism_any_of",
            (org in expect["organism_any_of"])
            or any(o in expect["organism_any_of"] for o in orgs if o),
            f"got={org or orgs}",
        )
    if "min_agrotoxicos" in expect:
        ok("min_agrotoxicos", n_agro >= expect["min_agrotoxicos"], f"got={n_agro}")
    if "min_proteinas" in expect:
        ok("min_proteinas", n_prot >= expect["min_proteinas"], f"got={n_prot}")
    if "protein_name_any_of" in expect:
        names = protein_names or [p if isinstance(p, str) else "" for p in prots]
        names = [n for n in names if n]
        ok(
            "protein_name_any_of",
            any(
                n in expect["protein_name_any_of"]
                or any(exp.lower() in n.lower() for exp in expect["protein_name_any_of"])
                for n in names
            ),
            f"got={names[:5]}",
        )
    # UniProt solo aplica en mode full (candidates no consulta APIs)
    if uniprots or "resultado" in result:
        if "uniprot_any_of" in expect:
            ok(
                "uniprot_any_of",
                any(u in expect["uniprot_any_of"] for u in uniprots),
                f"got={uniprots}",
            )
        if "forbid_uniprot" in expect:
            bad = [u for u in uniprots if u in expect["forbid_uniprot"]]
            ok("forbid_uniprot", not bad, f"bad={bad}")

    base = {
        "has_expect": True,
        "checks": checks,
        "passed": len(failed) == 0,
        "failed": failed,
    }
    quality = _quality_score(case, result, base)
    return {**base, **quality}


def _summarize(results: list[dict]) -> dict:
    total = len(results)
    by_status: dict[str, int] = {}
    expect_total = 0
    expect_pass = 0
    quality_scores: list[float] = []
    expect_quality: list[float] = []

    for r in results:
        st = r.get("result", {}).get("status", "missing")
        by_status[st] = by_status.get(st, 0) + 1
        sc = r.get("score") or {}
        q = sc.get("quality_score")
        if isinstance(q, (int, float)):
            quality_scores.append(float(q))
        if sc.get("has_expect"):
            expect_total += 1
            if sc.get("passed"):
                expect_pass += 1
            if isinstance(q, (int, float)):
                expect_quality.append(float(q))

    return {
        "total_cases": total,
        "by_status": by_status,
        "expect_cases": expect_total,
        "expect_passed": expect_pass,
        "expect_pass_rate": (expect_pass / expect_total) if expect_total else None,
        "ok_rate": (by_status.get("ok", 0) / total) if total else 0,
        "mean_quality_score": (
            round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else None
        ),
        "mean_expect_quality_score": (
            round(sum(expect_quality) / len(expect_quality), 3) if expect_quality else None
        ),
        "min_quality_score": round(min(quality_scores), 3) if quality_scores else None,
        "max_quality_score": round(max(quality_scores), 3) if quality_scores else None,
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
        f"- mean_quality_score: {s.get('mean_quality_score')}",
        f"- mean_expect_quality_score: {s.get('mean_expect_quality_score')}",
        f"- quality range: {s.get('min_quality_score')} .. {s.get('max_quality_score')}",
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
