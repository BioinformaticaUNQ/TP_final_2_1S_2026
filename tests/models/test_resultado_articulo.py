from __future__ import annotations

from models.article import Articulo
from models.compound import Agrotoxico
from models.homologo import HomologoHumano
from models.protein import ProteinaOrganismoModelo
from models.resultado_articulo import ResultadoArticulo


def test_resultado_articulo_defaults():
    resultado = ResultadoArticulo(articulo=Articulo(doi=""))
    assert resultado.articulo == Articulo(doi="")
    assert resultado.proteinas == []
    assert resultado.agrotoxicos == []
    assert resultado.homologos == []


def test_resultado_articulo_to_dict_vacio():
    resultado = ResultadoArticulo(articulo=Articulo(doi="10.1000/xyz"))
    assert resultado.to_dict() == {
        "articulo": {
            "doi": "10.1000/xyz",
            "titulo": None,
            "autores": [],
            "anio": None,
            "revista": None,
        },
        "proteinas": [],
        "agrotoxicos": [],
        "homologos_humanos": [],
    }


def test_resultado_articulo_to_dict_completo():
    resultado = ResultadoArticulo(
        articulo=Articulo(
            doi="10.1000/xyz",
            titulo="Titulo",
            autores=["Autor A"],
            anio=2024,
            revista="Revista X",
        ),
        proteinas=[
            ProteinaOrganismoModelo(
                nombre_proteina="Lipocalin-2",
                organismo="Danio rerio",
                uniprot_id="P12345",
                pdb_code="1DFV",
                funcion_biologica="Transporte",
            )
        ],
        agrotoxicos=[
            Agrotoxico(
                nombre_comun="Atrazina",
                familia_quimica="Triazina",
                smiles="CCN",
                logP=2.5,
                tipo_afinidad="Kd",
                valor_afinidad="2.5",
                unidad_afinidad="uM",
                metodo_experimental="ITC",
                fuente_dato="Texto del articulo",
            )
        ],
        homologos=[
            HomologoHumano(
                uniprot_id="P54886",
                nombre="RBP4",
                pct_identidad=45.2,
                pct_similitud=61.0,
                evalue=1e-30,
            )
        ],
    )
    assert resultado.to_dict() == {
        "articulo": {
            "doi": "10.1000/xyz",
            "titulo": "Titulo",
            "autores": ["Autor A"],
            "anio": 2024,
            "revista": "Revista X",
        },
        "proteinas": [
            {
                "nombre": "Lipocalin-2",
                "organismo": "Danio rerio",
                "uniprot_id": "P12345",
                "pdb_code": "1DFV",
                "funcion_biologica": "Transporte",
            }
        ],
        "agrotoxicos": [
            {
                "nombre_comun": "Atrazina",
                "familia_quimica": "Triazina",
                "smiles": "CCN",
                "logP": 2.5,
                "tipo_afinidad": "Kd",
                "valor_afinidad": "2.5",
                "unidad_afinidad": "uM",
                "metodo_experimental": "ITC",
                "fuente_dato": "Texto del articulo",
            }
        ],
        "homologos_humanos": [
            {
                "uniprot_id": "P54886",
                "nombre": "RBP4",
                "pct_identidad": 45.2,
                "pct_similitud": 61.0,
                "evalue": 1e-30,
            }
        ],
    }


def test_resultado_articulo_listas_son_independientes_entre_instancias():
    primero = ResultadoArticulo(articulo=Articulo(doi=""))
    segundo = ResultadoArticulo(articulo=Articulo(doi=""))
    primero.proteinas.append(ProteinaOrganismoModelo(nombre_proteina="X"))
    assert segundo.proteinas == []
