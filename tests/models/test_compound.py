from __future__ import annotations

from models.compound import Agrotoxico


def test_agrotoxico_defaults():
    agrotoxico = Agrotoxico(nombre_comun="Atrazina")
    assert agrotoxico.nombre_comun == "Atrazina"
    assert agrotoxico.familia_quimica is None
    assert agrotoxico.smiles is None
    assert agrotoxico.logP is None
    assert agrotoxico.tipo_afinidad is None
    assert agrotoxico.valor_afinidad is None
    assert agrotoxico.unidad_afinidad is None
    assert agrotoxico.metodo_experimental is None
    assert agrotoxico.fuente_dato is None


def test_agrotoxico_to_json():
    agrotoxico = Agrotoxico(
        nombre_comun="Atrazina",
        familia_quimica="Triazina",
        smiles="CCN(c1nc(Cl)nc(NC(C)C)n1)C(C)C",
        logP=2.5,
        tipo_afinidad="Kd",
        valor_afinidad="2.5",
        unidad_afinidad="uM",
        metodo_experimental="ITC",
        fuente_dato="Texto del articulo",
    )
    assert agrotoxico.toJson() == {
        "Nombre comun": "Atrazina",
        "Familia quimica": "Triazina",
        "SMILES": "CCN(c1nc(Cl)nc(NC(C)C)n1)C(C)C",
        "LogP": 2.5,
        "Tipo de afinidad": "Kd",
        "Valor de afinidad": "2.5",
        "Unidad de afinidad": "uM",
        "Metodo experimental": "ITC",
        "Fuente de dato": "Texto del articulo",
    }
