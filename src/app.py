from __future__ import annotations

import json
import re
from pathlib import Path

import click

from models import Agrotoxico, Articulo, ResultadoArticulo
from pdf_parser import parse_pdf
from services.crossref_service import fetch_doi
from services.pubchem_service import fetch_compound
from services.uniprot_service import fetch_protein

DOI_RE = re.compile(r"^10\.\d{4,9}/[^\s]+$")


class InputType(click.ParamType):
    name = "INPUT"

    def convert(self, value, param, ctx):
        path = Path(value)
        if path.is_dir():
            return {"kind": "dir", "path": path}
        if path.is_file():
            if path.suffix.lower() == ".pdf":
                return {"kind": "pdf", "path": path}
            return {"kind": "file", "path": path}
        if DOI_RE.match(value):
            return {"kind": "doi", "doi": value}
        self.fail(f"'{value}' no es un archivo existente, un directorio ni un DOI valido.", param, ctx)


INPUT = InputType()

CANDIDATO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\s\-]{1,50}$")
MAX_CANDIDATOS_PROTEINA = 10
MAX_CANDIDATOS_AGROTOXICO = 10


def es_candidato_valido(nombre: str) -> bool:
    if not nombre:
        return False
    if not CANDIDATO_RE.match(nombre):
        return False
    palabras = nombre.split()
    return 1 <= len(palabras) <= 6


def build_resultado_desde_pdf(path: Path) -> ResultadoArticulo:
    extraido = parse_pdf(path)

    articulo = None
    if extraido.doi:
        articulo = fetch_doi(extraido.doi)
    if articulo is None:
        articulo = Articulo(doi=extraido.doi or "", titulo=extraido.titulo)

    resultado = ResultadoArticulo(articulo=articulo)

    organismo = extraido.organismos[0] if extraido.organismos else None

    candidatos_proteina = [c for c in extraido.proteinas_candidatas if es_candidato_valido(c)]
    candidatos_proteina = candidatos_proteina[:MAX_CANDIDATOS_PROTEINA]

    ids_vistos = set()
    for candidata in candidatos_proteina:
        try:
            proteina = fetch_protein(candidata, organismo)
        except Exception as exc:
            click.echo(f"Aviso: fallo la consulta a UniProt para '{candidata}': {exc}")
            continue
        if proteina is None:
            continue
        if proteina.uniprot_id in ids_vistos:
            continue
        ids_vistos.add(proteina.uniprot_id)
        resultado.proteinas.append(proteina)

    candidatos_agrotoxico = extraido.agrotoxicos_candidatos[:MAX_CANDIDATOS_AGROTOXICO]

    nombres_vistos = set()
    for nombre in candidatos_agrotoxico:
        try:
            agrotoxico = fetch_compound(nombre)
        except Exception as exc:
            click.echo(f"Aviso: fallo la consulta a PubChem para '{nombre}': {exc}")
            agrotoxico = None
        if agrotoxico is None:
            agrotoxico = Agrotoxico(nombre_comun=nombre)
        if agrotoxico.nombre_comun in nombres_vistos:
            continue
        nombres_vistos.add(agrotoxico.nombre_comun)
        resultado.agrotoxicos.append(agrotoxico)

    return resultado


def guardar_resultado(resultado: ResultadoArticulo, nombre_base: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{nombre_base}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado.to_dict(), f, ensure_ascii=False, indent=2)
    return output_path


def procesar_pdf(path: Path, output_dir: Path) -> Path:
    resultado = build_resultado_desde_pdf(path)
    return guardar_resultado(resultado, path.stem, output_dir)


@click.command()
@click.argument("source", type=INPUT)
@click.option(
    "--output-dir",
    default="output",
    type=click.Path(path_type=Path),
    help="Directorio donde se guardan los JSON generados.",
)
def main(source, output_dir):
    match source["kind"]:
        case "doi":
            articulo = fetch_doi(source["doi"])
            if articulo is None:
                click.echo(f"No se pudo obtener informacion para el DOI {source['doi']}")
                return
            resultado = ResultadoArticulo(articulo=articulo)
            nombre_base = source["doi"].replace("/", "_")
            output_path = guardar_resultado(resultado, nombre_base, output_dir)
            click.echo(f"JSON generado: {output_path}")
        case "pdf":
            output_path = procesar_pdf(source["path"], output_dir)
            click.echo(f"JSON generado: {output_path}")
        case "dir":
            pdfs = sorted(source["path"].glob("*.pdf"))
            if not pdfs:
                click.echo(f"No se encontraron PDFs en {source['path']}")
                return
            for pdf_path in pdfs:
                output_path = procesar_pdf(pdf_path, output_dir)
                click.echo(f"JSON generado: {output_path}")
        case "file":
            click.echo(f"Archivo detectado: {source['path']}")


if __name__ == "__main__":
    main()