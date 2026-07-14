from __future__ import annotations

from pathlib import Path

from models import Articulo, ResultadoArticulo
from utils.pdf_parser import parse_pdf

ROOT = Path(__file__).resolve().parents[1]
PDF_SMOKE = ROOT / "articles" / "solo_agrotoxicos" / "acute_toxicity_atrazine.pdf"


def test_smoke_parser_extrae_datos_de_pdf_real():
    data = parse_pdf(PDF_SMOKE)

    assert data.texto_completo
    assert "atrazine" in data.agrotoxicos_candidatos


def test_smoke_json_final_tiene_las_cuatro_secciones():
    resultado = ResultadoArticulo(articulo=Articulo(doi="10.0/smoke"))

    salida = resultado.to_dict()

    assert set(salida) == {"articulo", "proteinas", "agrotoxicos", "homologos_humanos"}
