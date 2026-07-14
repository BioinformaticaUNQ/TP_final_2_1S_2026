from __future__ import annotations

import requests

from conftest import MockResponse
from services.crossref_service import CrossrefService


def test_crossref_service_parsea_metadatos(monkeypatch, crossref_payload):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return MockResponse(200, crossref_payload)

    monkeypatch.setattr(requests, "get", fake_get)

    articulo = CrossrefService().fetch_doi("10.1234/example")

    assert articulo is not None
    assert calls == [("https://api.crossref.org/works/10.1234/example", 30)]
    assert articulo.doi == "10.1234/example"
    assert articulo.titulo == "Lipocalin binding study"
    assert articulo.revista == "Bioinformatics Journal"
    assert articulo.anio == 2024
    assert articulo.autores == ["Ada Lovelace", "Grace Hopper"]


def test_crossref_service_devuelve_none_si_http_falla(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: MockResponse(404, text="not found"),
    )

    assert CrossrefService().fetch_doi("10.404/missing") is None


def test_crossref_service_devuelve_none_si_hay_error_de_red(monkeypatch):
    def fake_get(url, timeout):
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr(requests, "get", fake_get)

    assert CrossrefService().fetch_doi("10.1234/example") is None


def test_crossref_service_extrae_links_pdf_y_deriva_frontiers(monkeypatch):
    payload = {
        "message": {
            "link": [
                {
                    "URL": "https://example.org/article/full",
                    "content-type": "text/html",
                },
                {
                    "URL": "https://example.org/article.pdf",
                    "content-type": "application/pdf",
                },
                {
                    "URL": "https://www.frontiersin.org/articles/10.3389/test/full",
                    "content-type": "unspecified",
                },
            ]
        }
    }
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: MockResponse(200, payload),
    )

    links = CrossrefService().fetch_pdf_links("10.1234/example")

    assert links == [
        "https://example.org/article.pdf",
        "https://www.frontiersin.org/articles/10.3389/test/pdf",
    ]


def test_crossref_service_pdf_bytes_y_disco_coinciden(monkeypatch, tmp_path):
    """fetch_pdf_bytes es la fuente canonica; disco debe ser la misma carga util."""
    class PdfResponse:
        status_code = 200

        def iter_content(self, chunk_size):
            yield b"%PDF-1.4\n"
            yield b"content"

    crossref_payload = {
        "message": {
            "link": [
                {
                    "URL": "https://example.org/article.pdf",
                    "content-type": "application/pdf",
                }
            ]
        }
    }

    def fake_get(url, **kwargs):
        if url.startswith("https://api.crossref.org"):
            return MockResponse(200, crossref_payload)
        assert kwargs["headers"]["Accept"].startswith("application/pdf")
        assert kwargs["stream"] is True
        return PdfResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    service = CrossrefService()

    content = service.fetch_pdf_bytes("10.1234/example")
    path = service.download_pdf_from_doi("10.1234/example", tmp_path)

    assert content is not None
    assert content.startswith(b"%PDF")
    assert path == tmp_path / "10.1234_example.pdf"
    assert path.read_bytes() == content
    assert content == b"%PDF-1.4\ncontent"


def test_crossref_service_no_guarda_respuesta_no_pdf(monkeypatch, tmp_path):
    class HtmlResponse:
        status_code = 200

        def iter_content(self, chunk_size):
            yield b"<html>"

    crossref_payload = {
        "message": {
            "link": [
                {
                    "URL": "https://example.org/article.pdf",
                    "content-type": "application/pdf",
                }
            ]
        }
    }

    def fake_get(url, **kwargs):
        if url.startswith("https://api.crossref.org"):
            return MockResponse(200, crossref_payload)
        return HtmlResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    assert CrossrefService().download_pdf_from_doi("10.1234/example", tmp_path) is None
    assert not list(tmp_path.glob("*.pdf"))


def test_crossref_service_no_crashea_si_stream_se_corta(monkeypatch, tmp_path):
    class BrokenPdfResponse:
        status_code = 200

        def iter_content(self, chunk_size):
            yield b"%PDF-1.4\n"
            raise requests.exceptions.ChunkedEncodingError("connection reset")

    crossref_payload = {
        "message": {
            "link": [
                {
                    "URL": "https://example.org/article.pdf",
                    "content-type": "application/pdf",
                }
            ]
        }
    }

    def fake_get(url, **kwargs):
        if url.startswith("https://api.crossref.org"):
            return MockResponse(200, crossref_payload)
        return BrokenPdfResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    assert CrossrefService().download_pdf_from_doi("10.1234/example", tmp_path) is None
    assert not list(tmp_path.glob("*.tmp"))
