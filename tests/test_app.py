from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import app
from models import Agrotoxico, Articulo, HomologoHumano, ProteinaOrganismoModelo
from utils.pdf_parser import ExtractedArticleData


def test_input_type_detecta_doi():
    converted = app.INPUT.convert("10.1234/example", None, None)

    assert converted == {"kind": "doi", "doi": "10.1234/example"}


def test_input_type_rechaza_entrada_invalida():
    try:
        app.INPUT.convert("no-es-un-doi", None, None)
    except Exception as exc:
        assert "no es un archivo existente" in str(exc)
    else:
        raise AssertionError("La entrada invalida deberia fallar")


def test_build_resultado_desde_pdf_enriquece_y_deduplica(monkeypatch, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_text("fake pdf", encoding="utf-8")

    extraido = ExtractedArticleData(
        doi="10.1234/example",
        titulo="Fallback title",
        organismos=["Danio rerio"],
        proteinas_candidatas=["Lipocalin-2", "Lipocalin 2", "bad/candidate"],
        agrotoxicos_candidatos=["atrazine"],
        familias_agrotoxicos={"atrazine": "Triazina"},
        afinidades=[{"tipo": "Kd", "valor": "2.5", "unidad": "mM"}],
        metodos_experimentales=["ITC"],
        codigos_pdb=["1ABC"],
    )

    protein_by_name = {
        "Lipocalin-2": ProteinaOrganismoModelo(
            nombre_proteina="Lipocalin 2",
            organismo="Danio rerio",
            uniprot_id="Q0P4C2",
        ),
        "Lipocalin 2": ProteinaOrganismoModelo(
            nombre_proteina="Lipocalin 2 duplicate",
            organismo="Danio rerio",
            uniprot_id="Q0P4C2",
        ),
    }

    monkeypatch.setattr(app, "parse_pdf", lambda path: extraido)
    monkeypatch.setattr(
        app,
        "fetch_doi",
        lambda doi: Articulo(doi=doi, titulo="Crossref title", autores=["Ada"], anio=2024),
    )
    monkeypatch.setattr(app, "fetch_protein", lambda name, organism: protein_by_name.get(name))
    monkeypatch.setattr(
        app,
        "fetch_compound",
        lambda name, familia_quimica=None: Agrotoxico(
            nombre_comun=name,
            familia_quimica=familia_quimica,
            smiles="CCN",
            logP=2.6,
            fuente_dato="PubChem PUG REST",
        ),
    )
    monkeypatch.setattr(app, "fetch_sequence", lambda uniprot_id: "MKTAYIAK")
    monkeypatch.setattr(
        app,
        "buscar_homologos_humanos",
        lambda sequence, max_hits, mode: [
            HomologoHumano(uniprot_id="P2", nombre="Hit 2", evalue=1e-5),
            HomologoHumano(uniprot_id="P1", nombre="Hit 1", evalue=1e-10),
        ],
    )

    resultado = app.build_resultado_desde_pdf(pdf_path, ejecutar_blast=True, blast_mode="local")

    assert resultado.articulo.titulo == "Crossref title"
    assert len(resultado.proteinas) == 1
    assert resultado.proteinas[0].uniprot_id == "Q0P4C2"
    assert resultado.proteinas[0].pdb_code == "1ABC"
    assert len(resultado.agrotoxicos) == 1
    assert resultado.agrotoxicos[0].familia_quimica == "Triazina"
    assert resultado.agrotoxicos[0].tipo_afinidad == "Kd"
    assert resultado.agrotoxicos[0].valor_afinidad == "2.5"
    assert resultado.agrotoxicos[0].unidad_afinidad == "mM"
    assert resultado.agrotoxicos[0].metodo_experimental == "ITC"
    assert resultado.agrotoxicos[0].fuente_dato == "PubChem PUG REST; Texto del articulo"
    assert [h.uniprot_id for h in resultado.homologos] == ["P1", "P2"]


def test_guardar_resultado_escribe_json(tmp_path):
    resultado = app.ResultadoArticulo(
        articulo=Articulo(
            doi="10.1234/example",
            titulo="Lipocalin binding study",
            autores=["Ada Lovelace"],
            anio=2024,
            revista="Bioinformatics Journal",
        )
    )

    output_path = app.guardar_resultado(resultado, "paper", tmp_path)

    assert output_path == tmp_path / "paper.json"
    contents = output_path.read_text(encoding="utf-8")
    assert '"doi": "10.1234/example"' in contents
    assert '"anio": 2024' in contents


def test_cli_pdf_invoca_procesar_pdf_con_flags(monkeypatch, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"
    calls = []

    def fake_procesar_pdf(path, output_dir, ejecutar_blast=True, blast_mode="remote"):
        calls.append((path, output_dir, ejecutar_blast, blast_mode))
        return output_dir / "paper.json"

    monkeypatch.setattr(app, "procesar_pdf", fake_procesar_pdf)

    result = CliRunner().invoke(
        app.main,
        [str(pdf_path), "--output-dir", str(output_dir), "--skip-blast", "--blast-mode", "local"],
    )

    assert result.exit_code == 0
    assert calls == [(pdf_path, output_dir, False, "local")]
    assert "JSON generado:" in result.output


def test_cli_directorio_procesa_solo_pdfs_ordenados(monkeypatch, tmp_path):
    (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "not_pdf.txt").write_text("ignore", encoding="utf-8")
    output_dir = tmp_path / "out"
    processed = []

    def fake_procesar_pdf(path, output_dir, ejecutar_blast=True, blast_mode="remote"):
        processed.append(path.name)
        return output_dir / f"{path.stem}.json"

    monkeypatch.setattr(app, "procesar_pdf", fake_procesar_pdf)

    result = CliRunner().invoke(app.main, [str(tmp_path), "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert processed == ["a.pdf", "b.pdf"]
    assert result.output.count("JSON generado:") == 2


def test_cli_doi_guarda_metadatos_de_crossref(monkeypatch, tmp_path):
    saved = {}

    monkeypatch.setattr(app, "download_pdf_from_doi", lambda doi, output_dir: None)
    monkeypatch.setattr(
        app,
        "fetch_doi",
        lambda doi: Articulo(doi=doi, titulo="Lipocalin binding study"),
    )

    def fake_guardar_resultado(resultado, nombre_base, output_dir):
        saved["resultado"] = resultado
        saved["nombre_base"] = nombre_base
        saved["output_dir"] = output_dir
        return output_dir / f"{nombre_base}.json"

    monkeypatch.setattr(app, "guardar_resultado", fake_guardar_resultado)

    result = CliRunner().invoke(
        app.main,
        ["10.1234/example", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert saved["resultado"].articulo.doi == "10.1234/example"
    assert saved["nombre_base"] == "10.1234_example"
    assert saved["output_dir"] == tmp_path
    assert "JSON generado:" in result.output


def test_cli_doi_descarga_pdf_y_continua_flujo(monkeypatch, tmp_path):
    downloaded_pdf = tmp_path / "pdfs" / "10.1234_example.pdf"
    processed = {}

    def fake_download_pdf_from_doi(doi, output_dir):
        downloaded_pdf.parent.mkdir(parents=True, exist_ok=True)
        downloaded_pdf.write_bytes(b"%PDF-1.4")
        processed["download"] = (doi, output_dir)
        return downloaded_pdf

    def fake_procesar_pdf(path, output_dir, ejecutar_blast=True, blast_mode="remote"):
        processed["procesar"] = (path, output_dir, ejecutar_blast, blast_mode)
        return output_dir / "10.1234_example.json"

    monkeypatch.setattr(app, "download_pdf_from_doi", fake_download_pdf_from_doi)
    monkeypatch.setattr(app, "procesar_pdf", fake_procesar_pdf)
    monkeypatch.setattr(
        app,
        "fetch_doi",
        lambda doi: (_ for _ in ()).throw(AssertionError("No debe usar fallback si hay PDF")),
    )

    result = CliRunner().invoke(
        app.main,
        [
            "10.1234/example",
            "--output-dir",
            str(tmp_path / "out"),
            "--pdf-dir",
            str(tmp_path / "pdfs"),
            "--skip-blast",
            "--blast-mode",
            "local",
        ],
    )

    assert result.exit_code == 0
    assert processed["download"] == ("10.1234/example", tmp_path / "pdfs")
    assert processed["procesar"] == (
        downloaded_pdf,
        tmp_path / "out",
        False,
        "local",
    )
    assert "PDF descargado:" in result.output
    assert "JSON generado:" in result.output
