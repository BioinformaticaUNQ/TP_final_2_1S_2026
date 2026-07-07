from __future__ import annotations

from pathlib import Path

from utils import pdf_parser
from utils.pdf_parser import PdfParser


class FakePage:
    def __init__(self, text: str | None):
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_pdf_parser_extrae_campos_principales(monkeypatch, article_text):
    def fake_open(path):
        return FakePdf([FakePage(article_text), FakePage(None)])

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", fake_open)

    data = PdfParser().parse(Path("paper.pdf"))

    assert data.texto_completo == article_text
    assert data.doi == "10.1234/example.2024.15"
    assert data.titulo == "Lipocalin 2 binds atrazine in zebrafish"
    assert "Danio rerio" in data.organismos
    assert "Lipocalin-2" in data.proteinas_candidatas
    assert "LCN2" in data.proteinas_candidatas
    assert "lipocalin" in data.proteinas_candidatas
    assert data.agrotoxicos_candidatos == ["atrazine", "imidacloprid"]
    assert data.afinidades == [{"tipo": "Kd", "valor": "2.5", "unidad": "mM"}]
    assert "ITC" in data.metodos_experimentales
    assert "molecular docking" in data.metodos_experimentales
    assert data.codigos_pdb == ["1ABC"]


def test_pdf_parser_usa_nombre_de_archivo_si_no_encuentra_titulo(monkeypatch):
    def fake_open(path):
        return FakePdf([FakePage("doi:10.1234/example\nabstract\njournal")])

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", fake_open)

    data = PdfParser().parse(Path("fallback_title.pdf"))

    assert data.titulo == "fallback_title"


def test_extract_doi_limpia_puntuacion_final():
    parser = PdfParser()

    assert parser._extract_doi("Reference doi:10.5555/test.123;") == "10.5555/test.123"


def test_extract_organisms_detecta_nombre_comun():
    parser = PdfParser()

    assert parser._extract_organisms("The zebrafish assay was repeated.") == ["Danio rerio"]
