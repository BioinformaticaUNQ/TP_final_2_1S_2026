from __future__ import annotations

from models.article import Articulo


def test_articulo_defaults():
    articulo = Articulo(doi="10.1000/xyz")
    assert articulo.doi == "10.1000/xyz"
    assert articulo.titulo is None
    assert articulo.autores == []
    assert articulo.anio is None
    assert articulo.revista is None


def test_articulo_to_json():
    articulo = Articulo(
        doi="10.1000/xyz",
        titulo="Titulo",
        autores=["Autor A", "Autor B"],
        anio=2024,
        revista="Revista X",
    )
    assert articulo.toJson() == {
        "DOI": "10.1000/xyz",
        "Titulo": "Titulo",
        "Autores": ["Autor A", "Autor B"],
        "Anio de Publicacion": 2024,
        "Revista": "Revista X",
    }


def test_articulo_autores_son_independientes_entre_instancias():
    primero = Articulo(doi="10.1/a")
    segundo = Articulo(doi="10.1/b")
    primero.autores.append("Autor A")
    assert segundo.autores == []
