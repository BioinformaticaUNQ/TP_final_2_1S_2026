from __future__ import annotations

import requests

from conftest import MockResponse
from services.uniprot_service import UniProtService


def test_uniprot_query_variants_incluyen_fallback_gen():
    queries = UniProtService._query_variants("OBP11", "Tribolium castaneum")
    assert any('organism_name:"Tribolium castaneum"' in q for q in queries)
    assert any("gene:OBP11" in q for q in queries)
    # No buscar gen suelto sin organismo (evita off-species)
    assert "OBP11" not in queries
    assert any("odorant binding" in q for q in queries)


def test_uniprot_fetch_protein_prueba_fallbacks(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, results):
            self.status_code = 200
            self._results = results

        def json(self):
            return {"results": self._results}

    def fake_get(url, params=None, timeout=30):
        calls.append(params["query"])
        if "gene:OBP11" in params["query"] and "Tribolium" in params["query"]:
            return FakeResponse(
                [
                    {
                        "primaryAccession": "A0A1B2C3D4",
                        "proteinDescription": {
                            "recommendedName": {"fullName": {"value": "Odorant-binding protein 11"}}
                        },
                        "organism": {"scientificName": "Tribolium castaneum"},
                        "comments": [],
                    }
                ]
            )
        return FakeResponse([])

    monkeypatch.setattr(requests, "get", fake_get)
    hit = UniProtService().fetch_protein("OBP11", "Tribolium castaneum")
    assert hit is not None
    assert hit.uniprot_id == "A0A1B2C3D4"
    assert any("gene:OBP11" in q for q in calls)
    assert all("Locusta" not in q for q in calls)


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
