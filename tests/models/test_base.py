from __future__ import annotations

from models.base import BaseModel


def test_base_model_defaults():
    base = BaseModel()
    assert base.nombre == ""
    assert base.descripcion is None


def test_base_model_valores_explicitos():
    base = BaseModel(nombre="X", descripcion="Y")
    assert base.nombre == "X"
    assert base.descripcion == "Y"
