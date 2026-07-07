from __future__ import annotations

import requests

from conftest import MockResponse
from services.crossref_service import CrossrefService
from services.pubchem_service import PubChemService
from services.uniprot_service import UniProtService


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


def test_crossref_service_descarga_pdf_valido(monkeypatch, tmp_path):
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

    path = CrossrefService().download_pdf_from_doi("10.1234/example", tmp_path)

    assert path == tmp_path / "10.1234_example.pdf"
    assert path.read_bytes() == b"%PDF-1.4\ncontent"


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


def test_pubchem_service_parsea_smiles_logp_y_fuente(monkeypatch, pubchem_payload):
    requested = {}

    def fake_get(url, timeout):
        requested["url"] = url
        requested["timeout"] = timeout
        return MockResponse(200, pubchem_payload)

    monkeypatch.setattr(requests, "get", fake_get)

    compuesto = PubChemService().fetch_compound(" atrazine ")

    assert compuesto is not None
    assert (
        "compound/name/atrazine/property/CanonicalSMILES,ConnectivitySMILES,IsomericSMILES,XLogP/JSON"
        in requested["url"]
    )
    assert requested["timeout"] == 30
    assert compuesto.nombre_comun == "atrazine"
    assert compuesto.smiles == "CCNC1=NC(=NC(=N1)Cl)NC(C)C"
    assert compuesto.logP == 2.6
    assert compuesto.fuente_dato == "PubChem PUG REST"


def test_pubchem_service_acepta_campo_smiles_actual_de_api(monkeypatch):
    payload = {
        "PropertyTable": {
            "Properties": [{"CID": 2256, "SMILES": "CCN", "ConnectivitySMILES": "CCN", "XLogP": 1.2}]
        }
    }
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: MockResponse(200, payload),
    )

    compuesto = PubChemService().fetch_compound("imidacloprid", familia_quimica="Neonicotinoide")

    assert compuesto is not None
    assert compuesto.familia_quimica == "Neonicotinoide"
    assert compuesto.smiles == "CCN"


def test_pubchem_service_devuelve_none_si_no_hay_propiedades(monkeypatch):
    payload = {"PropertyTable": {"Properties": []}}
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: MockResponse(200, payload),
    )

    assert PubChemService().fetch_compound("unknown") is None


def test_uniprot_service_parsea_proteina_y_funcion(monkeypatch, uniprot_payload):
    requested = {}

    def fake_get(url, params=None, timeout=30):
        requested["url"] = url
        requested["params"] = params
        requested["timeout"] = timeout
        return MockResponse(200, uniprot_payload)

    monkeypatch.setattr(requests, "get", fake_get)

    proteina = UniProtService().fetch_protein("Lipocalin 2", "Danio rerio")

    assert proteina is not None
    assert requested["url"] == "https://rest.uniprot.org/uniprotkb/search"
    assert requested["params"] == {
        "query": 'Lipocalin 2 AND organism_name:"Danio rerio"',
        "format": "json",
        "size": 1,
    }
    assert proteina.nombre_proteina == "Lipocalin 2"
    assert proteina.organismo == "Danio rerio"
    assert proteina.uniprot_id == "Q0P4C2"
    assert proteina.funcion_biologica == "Binds small hydrophobic ligands."


def test_uniprot_service_descarga_secuencia_fasta(monkeypatch):
    fasta = ">sp|Q0P4C2|LCN2_DANRE Lipocalin 2\nMKTAYIAK\nQRQISFVK\n"
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: MockResponse(200, text=fasta),
    )

    assert UniProtService().fetch_sequence("Q0P4C2") == "MKTAYIAKQRQISFVK"
