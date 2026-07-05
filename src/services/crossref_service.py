from __future__ import annotations

from dataclasses import dataclass, field

import requests
from loguru import logger


@dataclass
class Articulo:
    doi: str
    titulo: str | None = None
    autores: list[str] = field(default_factory=list)
    anio: int | None = None
    revista: str | None = None

    def toJson(self):
        return {
            "DOI": self.doi,
            "Titulo": self.titulo,
            "Autores": self.autores,
            "Anio de Publicacion": self.anio,
            "Revista": self.revista,
        }


class CrossrefService:
    BASE_URL = "https://api.crossref.org/works"

    def fetch_doi(self, doi: str) -> Articulo | None:
        if not doi:
            logger.warning("DOI vacío recibido.")
            return None

        url = f"{self.BASE_URL}/{doi}"
        logger.info(f"Consultando Crossref para el DOI: {doi}")

        try:
            response = requests.get(url, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo de red al consultar Crossref: {e}")
            return None

        if response.status_code != 200:
            logger.error(f"Error {response.status_code} en Crossref para DOI {doi}")
            return None

        data = response.json()
        articulo = Articulo(doi)

        message = data.get("message", {})
        titles = message.get("title", [])
        container_titles = message.get("container-title", [])

        articulo.titulo = titles[0] if titles else None
        articulo.revista = container_titles[0] if container_titles else None

        if "published-print" in message:
            articulo.anio = message["published-print"]["date-parts"][0][0]
        elif "published-online" in message:
            articulo.anio = message["published-online"]["date-parts"][0][0]

        for autor in message.get("author", []):
            nombre = autor.get("given", "")
            apellido = autor.get("family", "")
            articulo.autores.append(f"{nombre} {apellido}".strip())

        logger.success(f"Datos obtenidos de Crossref: {articulo.titulo}")
        return articulo


def fetch_doi(doi: str) -> Articulo | None:
    return CrossrefService().fetch_doi(doi)