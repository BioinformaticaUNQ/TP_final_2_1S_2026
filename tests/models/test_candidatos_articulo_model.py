from __future__ import annotations

from models.candidatos_articulo import AfinidadCandidata, CandidatosArticulo


def test_afinidad_candidata_defaults():
    afinidad = AfinidadCandidata()
    assert afinidad.tipo is None
    assert afinidad.valor is None
    assert afinidad.unidad is None
    assert afinidad.agrotoxico is None


def test_afinidad_candidata_valores_explicitos():
    afinidad = AfinidadCandidata(
        tipo="Kd", valor="2.5", unidad="uM", agrotoxico="Atrazina"
    )
    assert afinidad.tipo == "Kd"
    assert afinidad.valor == "2.5"
    assert afinidad.unidad == "uM"
    assert afinidad.agrotoxico == "Atrazina"


def test_candidatos_articulo_defaults():
    candidatos = CandidatosArticulo()
    assert candidatos.organismo_principal is None
    assert candidatos.organismos_secundarios == []
    assert candidatos.proteinas == []
    assert candidatos.agrotoxicos == []
    assert candidatos.familias_agrotoxicos == {}
    assert candidatos.afinidades == []
    assert candidatos.metodos_experimentales == []
    assert candidatos.codigos_pdb == []


def test_candidatos_articulo_valores_explicitos():
    afinidad = AfinidadCandidata(tipo="Ki", valor="10", unidad="nM", agrotoxico="Imidacloprid")
    candidatos = CandidatosArticulo(
        organismo_principal="Danio rerio",
        organismos_secundarios=["Apis mellifera"],
        proteinas=["Lipocalin-2"],
        agrotoxicos=["Imidacloprid"],
        familias_agrotoxicos={"Imidacloprid": "Neonicotinoide"},
        afinidades=[afinidad],
        metodos_experimentales=["ITC"],
        codigos_pdb=["1DFV"],
    )
    assert candidatos.organismo_principal == "Danio rerio"
    assert candidatos.organismos_secundarios == ["Apis mellifera"]
    assert candidatos.proteinas == ["Lipocalin-2"]
    assert candidatos.agrotoxicos == ["Imidacloprid"]
    assert candidatos.familias_agrotoxicos == {"Imidacloprid": "Neonicotinoide"}
    assert candidatos.afinidades == [afinidad]
    assert candidatos.metodos_experimentales == ["ITC"]
    assert candidatos.codigos_pdb == ["1DFV"]


def test_candidatos_articulo_listas_son_independientes_entre_instancias():
    primero = CandidatosArticulo()
    segundo = CandidatosArticulo()
    primero.proteinas.append("Lipocalin-2")
    assert segundo.proteinas == []
