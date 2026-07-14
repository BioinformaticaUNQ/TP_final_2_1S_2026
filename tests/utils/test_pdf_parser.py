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
    assert data.familias_agrotoxicos == {
        "atrazine": "Triazina",
        "imidacloprid": "Neonicotinoide",
    }
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


def test_pdf_parser_path_y_bytes_equivalentes(monkeypatch, article_text):
    """Misma carga util de texto => mismos campos, sin importar Path o bytes."""
    def fake_open(_source):
        return FakePdf([FakePage(article_text)])

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", fake_open)
    parser = PdfParser()

    from_path = parser.parse(Path("paper.pdf"))
    from_bytes = parser.parse(b"%PDF-1.4 fake")

    assert from_path.doi == from_bytes.doi
    assert from_path.titulo == from_bytes.titulo
    assert from_path.organismos == from_bytes.organismos
    assert from_path.proteinas_candidatas == from_bytes.proteinas_candidatas
    assert from_path.agrotoxicos_candidatos == from_bytes.agrotoxicos_candidatos
    assert from_path.afinidades == from_bytes.afinidades


def test_extract_doi_limpia_puntuacion_final():
    parser = PdfParser()

    assert parser._extract_doi("Reference doi:10.5555/test.123;") == "10.5555/test.123"


def test_extract_doi_recompone_sufijo_partido_por_salto_de_linea():
    parser = PdfParser()

    texto = "Published in Journal; doi: 10.1016/j.pestbp\n.2022.105271"

    assert parser._extract_doi(texto) == "10.1016/j.pestbp.2022.105271"


def test_extract_title_normaliza_lineas_con_glifos_duplicados():
    parser = PdfParser()
    texto = "\n".join(
        [
            "UUnniivveerrssiittyy ooff NNeebbrraasskkaa -- LLiinnccoollnn",
            "AAccuuttee TTooxxiicciittyy ooff AAttrraazziinnee,, AAllaacchhlloorr,, aanndd",
            "CChhlloorrppyyrriiffooss MMiixxttuurreess ttoo HHoonneeyy BBeeeess",
        ]
    )

    assert (
        parser._extract_title(Path("paper.pdf"), texto)
        == "Acute Toxicity of Atrazine, Alachlor, and Chlorpyrifos Mixtures to Honey Bees"
    )


def test_extract_organisms_detecta_nombre_comun():
    parser = PdfParser()

    assert parser._extract_organisms("The zebrafish assay was repeated.") == ["Danio rerio"]
