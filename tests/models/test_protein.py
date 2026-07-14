from __future__ import annotations

from models.protein import ProteinaOrganismoModelo


def test_proteina_organismo_modelo_defaults():
    proteina = ProteinaOrganismoModelo(nombre_proteina="Lipocalin-2")
    assert proteina.nombre_proteina == "Lipocalin-2"
    assert proteina.organismo is None
    assert proteina.uniprot_id is None
    assert proteina.pdb_code is None
    assert proteina.funcion_biologica is None


def test_proteina_organismo_modelo_to_json():
    proteina = ProteinaOrganismoModelo(
        nombre_proteina="Lipocalin-2",
        organismo="Danio rerio",
        uniprot_id="P12345",
        pdb_code="1DFV",
        funcion_biologica="Transporte de siderophoros",
    )
    assert proteina.toJson() == {
        "Nombre proteina": "Lipocalin-2",
        "Organismo": "Danio rerio",
        "UniProt ID": "P12345",
        "PDB code": "1DFV",
        "Funcion biologica": "Transporte de siderophoros",
    }
