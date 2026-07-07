from __future__ import annotations

import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_setuptools_config_es_portable():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    setuptools_config = pyproject["tool"]["setuptools"]
    modules = setuptools_config["py-modules"]
    package_find = pyproject["tool"]["setuptools"]["packages"]["find"]

    assert modules == ["app"]
    assert all((ROOT / "src" / f"{module}.py").exists() for module in modules)
    assert package_find["where"] == ["src"]
    assert "utils*" in package_find["include"]


def test_utils_es_paquete_importable():
    sys.path.insert(0, str(ROOT / "src"))

    from utils import PdfParser, parse_pdf

    assert PdfParser is not None
    assert parse_pdf is not None
