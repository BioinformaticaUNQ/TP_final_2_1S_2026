import re
from pathlib import Path

import click
import requests

DOI_RE = re.compile(r"^10\.\d{4,9}/[^\s]+$")

url_crossref = "https://api.crossref.org"
endpoint_works = f"{url_crossref}/works/"


def doi_to_url(doi):
    return f"{endpoint_works}{doi}"


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


class Articulo:
    def __init__(self, doi):
        self.doi = doi
        self.titulo = None
        self.autores = []
        self.año = None
        self.revista = None

    def toJson(self):
        return {
            "DOI": self.doi,
            "Título": self.titulo,
            "Autores": self.autores,
            "Año de Publicacion": self.año,
            "Revista": self.revista,
        }


class ProteinaOrganismoModelo:
    def __init__(self, nombre_proteina, organismo, uniprot_id=None, pdb_code=None, funcion_biologica=None):
        self.nombre_proteina = nombre_proteina
        self.organismo = organismo
        self.uniprot_id = uniprot_id
        self.pdb_code = pdb_code
        self.funcion_biologica = funcion_biologica


class Agrotoxico:
    def __init__(self, nombre_comun, familia_quimica, smiles=None, logP=None, tipo_afinidad=None, valor_unidad=None, metodo_experimental=None, fuente_dato=None):
        self.nombre_comun = nombre_comun
        self.familia_quimica = familia_quimica
        self.smiles = smiles
        self.logP = logP
        self.tipo_afinidad = tipo_afinidad
        self.valor_unidad = valor_unidad
        self.metodo_experimental = metodo_experimental
        self.fuente_dato = fuente_dato


def fetch_doi(doi):
    url = doi_to_url(doi)
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        articulo = Articulo(doi)

        articulo.titulo = data["message"]["title"][0]
        articulo.revista = data["message"]["container-title"][0]

        if "published-print" in data["message"]:
            articulo.año = data["message"]["published-print"]["date-parts"][0][0]
        elif "published-online" in data["message"]:
            articulo.año = data["message"]["published-online"]["date-parts"][0][0]

        for autor in data["message"]["author"]:
            nombre = autor.get("given", "")
            apellido = autor.get("family", "")
            articulo.autores.append(f"{nombre} {apellido}")

        return articulo
    else:
        click.echo(f"Error al obtener datos para DOI {doi}: {response.status_code}", err=True)
        return None


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