from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

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
    PDF_HEADERS = {
        "User-Agent": "tp-bioinfo/0.1",
        "Accept": "application/pdf,*/*;q=0.8",
    }

    def _fetch_work_message(self, doi: str) -> dict | None:
        if not doi:
            logger.warning("DOI vacio recibido.")
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

        return response.json().get("message", {})

    def fetch_doi(self, doi: str) -> Articulo | None:
        message = self._fetch_work_message(doi)
        if message is None:
            return None

        articulo = Articulo(doi)
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

    def fetch_pdf_links(self, doi: str) -> list[str]:
        message = self._fetch_work_message(doi)
        if message is None:
            return []

        candidates = []
        for link in message.get("link", []):
            url = link.get("URL")
            if not url:
                continue
            content_type = (link.get("content-type") or "").lower()
            lower_url = url.lower()
            if (
                "pdf" in content_type
                or lower_url.endswith(".pdf")
                or "/pdf/" in lower_url
                or "/pdf?" in lower_url
            ):
                candidates.append(url)
            if "frontiersin.org" in lower_url and lower_url.endswith("/full"):
                candidates.append(url.removesuffix("/full") + "/pdf")

        doi_url = message.get("URL")
        if doi_url and doi_url.lower().endswith(".pdf"):
            candidates.append(doi_url)

        return list(dict.fromkeys(candidates))

    def download_pdf_from_doi(self, doi: str, output_dir: str | Path) -> Path | None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_links = self.fetch_pdf_links(doi)
        if not pdf_links:
            logger.warning(f"Crossref no devolvio links PDF para DOI {doi}.")
            return None

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", doi).strip("_")
        output_path = output_dir / f"{safe_name}.pdf"
        temp_path = output_dir / f"{safe_name}.pdf.tmp"

        for url in pdf_links:
            logger.info(f"Intentando descargar PDF para DOI {doi}: {url}")
            try:
                response = requests.get(
                    url,
                    headers=self.PDF_HEADERS,
                    timeout=60,
                    stream=True,
                    allow_redirects=True,
                )
            except requests.exceptions.RequestException as e:
                logger.warning(f"No se pudo descargar PDF desde {url}: {e}")
                continue

            if response.status_code != 200:
                logger.warning(f"Descarga PDF fallo con HTTP {response.status_code}: {url}")
                continue

            try:
                try:
                    chunks = response.iter_content(chunk_size=8192)
                    first_chunk = next((chunk for chunk in chunks if chunk), b"")
                    if not first_chunk.startswith(b"%PDF"):
                        logger.warning(f"La URL no devolvio contenido PDF valido: {url}")
                        continue

                    with open(temp_path, "wb") as handle:
                        handle.write(first_chunk)
                        for chunk in chunks:
                            if chunk:
                                handle.write(chunk)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Descarga PDF interrumpida desde {url}: {e}")
                    continue

                temp_path.replace(output_path)
                logger.success(f"PDF descargado desde DOI {doi}: {output_path}")
                return output_path
            finally:
                if temp_path.exists():
                    temp_path.unlink()

        return None


def fetch_doi(doi: str) -> Articulo | None:
    return CrossrefService().fetch_doi(doi)


def fetch_pdf_links(doi: str) -> list[str]:
    return CrossrefService().fetch_pdf_links(doi)


def download_pdf_from_doi(doi: str, output_dir: str | Path) -> Path | None:
    return CrossrefService().download_pdf_from_doi(doi, output_dir)
