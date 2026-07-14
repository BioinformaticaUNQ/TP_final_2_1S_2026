from __future__ import annotations

from models.homologo import HomologoHumano


def test_homologo_humano_defaults():
    homologo = HomologoHumano()
    assert homologo.uniprot_id == ""
    assert homologo.nombre == ""
    assert homologo.pct_identidad is None
    assert homologo.pct_similitud is None
    assert homologo.evalue is None


def test_homologo_humano_to_json():
    homologo = HomologoHumano(
        uniprot_id="P54886",
        nombre="RBP4",
        pct_identidad=45.2,
        pct_similitud=61.0,
        evalue=1e-30,
    )
    assert homologo.toJson() == {
        "uniprot_id": "P54886",
        "nombre": "RBP4",
        "pct_identidad": 45.2,
        "pct_similitud": 61.0,
        "evalue": 1e-30,
    }
