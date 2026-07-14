from __future__ import annotations

import requests

from conftest import MockResponse
from services.pubchem_service import PubChemService


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
