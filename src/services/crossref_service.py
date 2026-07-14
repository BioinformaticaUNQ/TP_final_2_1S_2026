from __future__ import annotations

import re
import time
from pathlib import Path

import requests
from loguru import logger

from models.article import Articulo

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(texto: str) -> str:
    limpio = _HTML_TAG_RE.sub("", texto)
    return re.sub(r"\s+", " ", limpio).strip()


class CrossrefService:
    BASE_URL = "https://api.crossref.org/works"
    PDF_HEADERS = {
        "User-Agent": "tp-bioinfo/0.1",
        "Accept": "application/pdf,*/*;q=0.8",
    }
    DOWNLOAD_TIMEOUT = 60
    PROGRESS_EVERY_BYTES = 256 * 1024

    def _fetch_work_message(self, doi: str) -> dict | None:
        if not doi:
            logger.warning("DOI vacio recibido.")
            return None

        url = f"{self.BASE_URL}/{doi}"
        logger.info(f"Consultando Crossref para el DOI: {doi}")
        started = time.monotonic()

        try:
            response = requests.get(url, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo de red al consultar Crossref: {e}")
            return None

        elapsed = time.monotonic() - started
        if response.status_code != 200:
            logger.error(
                f"Error {response.status_code} en Crossref para DOI {doi} "
                f"(tardo {elapsed:.1f}s)"
            )
            return None

        logger.debug(f"Crossref respondio HTTP 200 en {elapsed:.1f}s para DOI {doi}")
        return response.json().get("message", {})

    def fetch_doi(self, doi: str) -> Articulo | None:
        message = self._fetch_work_message(doi)
        if message is None:
            return None

        articulo = Articulo(doi)
        titles = message.get("title", [])
        container_titles = message.get("container-title", [])

        raw_title = titles[0] if titles else None
        articulo.titulo = _strip_html(raw_title) if raw_title else None
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
        logger.info(f"Buscando links PDF en Crossref para DOI {doi}")
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

        unique = list(dict.fromkeys(candidates))
        if unique:
            logger.info(f"Crossref devolvio {len(unique)} candidato(s) PDF para DOI {doi}")
            for idx, candidate in enumerate(unique, start=1):
                logger.debug(f"  [{idx}] {candidate}")
        else:
            logger.warning(f"Crossref no devolvio links PDF para DOI {doi}")
        return unique

    @staticmethod
    def _format_bytes(num_bytes: int) -> str:
        if num_bytes < 1024:
            return f"{num_bytes} B"
        if num_bytes < 1024 * 1024:
            return f"{num_bytes / 1024:.1f} KB"
        return f"{num_bytes / (1024 * 1024):.2f} MB"

    def fetch_pdf_bytes(self, doi: str) -> bytes | None:
        """Descarga el PDF en memoria. Fuente canonica; disco es opcional via download_pdf_from_doi."""
        logger.info(
            f"Iniciando descarga de PDF para DOI {doi} "
            f"(timeout {self.DOWNLOAD_TIMEOUT}s; publishers como Frontiers pueden tardar 20-60s)"
        )

        pdf_links = self.fetch_pdf_links(doi)
        if not pdf_links:
            logger.warning(f"No hay URLs PDF para intentar con DOI {doi}.")
            return None

        for index, url in enumerate(pdf_links, start=1):
            logger.info(
                f"Intentando descarga [{index}/{len(pdf_links)}] DOI {doi}: {url}"
            )
            request_started = time.monotonic()
            try:
                logger.info(
                    "Esperando respuesta HTTP del publisher "
                    "(puede demorar; no cancelar si parece quieto)..."
                )
                response = requests.get(
                    url,
                    headers=self.PDF_HEADERS,
                    timeout=self.DOWNLOAD_TIMEOUT,
                    stream=True,
                    allow_redirects=True,
                )
            except KeyboardInterrupt:
                logger.warning(
                    "Descarga cancelada por el usuario (Ctrl+C) mientras se esperaba la respuesta HTTP."
                )
                raise
            except requests.exceptions.RequestException as e:
                elapsed = time.monotonic() - request_started
                logger.warning(
                    f"No se pudo conectar a {url} tras {elapsed:.1f}s: {e}"
                )
                continue

            headers_elapsed = time.monotonic() - request_started
            response_headers = getattr(response, "headers", None) or {}
            content_type = response_headers.get("Content-Type", "desconocido")
            content_length = response_headers.get("Content-Length")
            size_hint = (
                self._format_bytes(int(content_length))
                if content_length and str(content_length).isdigit()
                else "desconocido"
            )
            final_url = getattr(response, "url", url)
            logger.info(
                f"Respuesta HTTP {response.status_code} en {headers_elapsed:.1f}s | "
                f"Content-Type={content_type} | tamano={size_hint} | URL final={final_url}"
            )

            if response.status_code != 200:
                logger.warning(
                    f"Descarga PDF fallo con HTTP {response.status_code}: {url}"
                )
                continue

            total_bytes = 0
            try:
                chunks = response.iter_content(chunk_size=8192)
                first_chunk = next((chunk for chunk in chunks if chunk), b"")
                if not first_chunk.startswith(b"%PDF"):
                    preview = first_chunk[:40]
                    logger.warning(
                        f"La URL no devolvio contenido PDF valido "
                        f"(primeros bytes={preview!r}): {url}"
                    )
                    continue

                logger.info(
                    f"Contenido PDF valido detectado; descargando cuerpo "
                    f"(progreso cada {self._format_bytes(self.PROGRESS_EVERY_BYTES)})..."
                )
                buffer = bytearray(first_chunk)
                total_bytes = len(first_chunk)
                last_log_at = 0
                stream_started = time.monotonic()

                for chunk in chunks:
                    if not chunk:
                        continue
                    buffer.extend(chunk)
                    total_bytes += len(chunk)
                    if total_bytes - last_log_at >= self.PROGRESS_EVERY_BYTES:
                        last_log_at = total_bytes
                        elapsed = time.monotonic() - stream_started
                        rate = total_bytes / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"Descarga en curso: {self._format_bytes(total_bytes)} "
                            f"en {elapsed:.1f}s "
                            f"({self._format_bytes(int(rate))}/s)"
                        )

                content = bytes(buffer)
                total_elapsed = time.monotonic() - request_started
                logger.success(
                    f"PDF en memoria para DOI {doi}: "
                    f"{self._format_bytes(len(content))} en {total_elapsed:.1f}s"
                )
                return content
            except KeyboardInterrupt:
                logger.warning(
                    f"Descarga cancelada por el usuario (Ctrl+C) tras "
                    f"{self._format_bytes(total_bytes)} recibidos."
                )
                raise
            except requests.exceptions.RequestException as e:
                elapsed = time.monotonic() - request_started
                logger.warning(
                    f"Descarga PDF interrumpida desde {url} tras {elapsed:.1f}s: {e}"
                )
                continue

        logger.error(
            f"No se pudo descargar un PDF valido para DOI {doi} "
            f"tras {len(pdf_links)} intento(s)."
        )
        return None

    def download_pdf_from_doi(self, doi: str, output_dir: str | Path) -> Path | None:
        content = self.fetch_pdf_bytes(doi)
        if content is None:
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", doi).strip("_")
        output_path = output_dir / f"{safe_name}.pdf"
        output_path.write_bytes(content)
        logger.success(f"PDF guardado en disco: {output_path}")
        return output_path


def fetch_doi(doi: str) -> Articulo | None:
    return CrossrefService().fetch_doi(doi)


def fetch_pdf_links(doi: str) -> list[str]:
    return CrossrefService().fetch_pdf_links(doi)


def fetch_pdf_bytes(doi: str) -> bytes | None:
    return CrossrefService().fetch_pdf_bytes(doi)


def download_pdf_from_doi(doi: str, output_dir: str | Path) -> Path | None:
    return CrossrefService().download_pdf_from_doi(doi, output_dir)
