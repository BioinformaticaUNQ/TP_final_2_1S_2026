import click
from pathlib import Path
import re

from services.crossref_service import fetch_doi

DOI_RE = re.compile(r"^10\.\d{4,9}/[^\s]+$")


class InputType(click.ParamType):
    name = "INPUT"

    def convert(self, value, param, ctx):
        path = Path(value)
        if path.is_file():
            if path.suffix.lower() == ".pdf":
                return {"kind": "pdf", "path": path}
            return {"kind": "file", "path": path}
        if DOI_RE.match(value):
            return {"kind": "doi", "doi": value}
        self.fail(f"'{value}' no es un archivo existente ni un DOI valido.", param, ctx)


INPUT = InputType()


@click.command()
@click.argument("source", type=INPUT)
def main(source):
    match source["kind"]:
        case "doi":
            articulo = fetch_doi(source["doi"])
            if articulo:
                click.echo(articulo.toJson())
        case "pdf":
            click.echo(f"PDF detectado: {source['path']}")
        case "file":
            click.echo(f"Archivo detectado: {source['path']}")


if __name__ == "__main__":
    main()
