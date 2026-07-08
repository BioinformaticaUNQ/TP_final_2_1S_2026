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

    monkeypatch.setattr(app, "fetch_pdf_bytes", lambda doi: None)
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
    """DOI: analiza desde bytes; por defecto tambien persiste el PDF."""
    pdf_bytes = b"%PDF-1.4 content"
    processed = {}
    pdf_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "out"

    def fake_procesar_pdf(
        source,
        output_dir,
        ejecutar_blast=True,
        blast_mode="remote",
        nombre_base=None,
    ):
        processed["procesar"] = (source, output_dir, ejecutar_blast, blast_mode, nombre_base)
        return output_dir / f"{nombre_base}.json"

    monkeypatch.setattr(app, "fetch_pdf_bytes", lambda doi: pdf_bytes)
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
            str(output_dir),
            "--pdf-dir",
            str(pdf_dir),
            "--skip-blast",
            "--blast-mode",
            "local",
        ],
    )

    assert result.exit_code == 0
    saved_pdf = pdf_dir / "10.1234_example.pdf"
    assert saved_pdf.read_bytes() == pdf_bytes
    assert processed["procesar"] == (pdf_bytes, output_dir, False, "local", "10.1234_example")
    assert "PDF descargado:" in result.output
    assert "JSON generado:" in result.output


def test_cli_doi_no_save_pdf_no_escribe_disco(monkeypatch, tmp_path):
    """--no-save-pdf: mismo analisis en memoria, sin archivo PDF."""
    pdf_bytes = b"%PDF-1.4 content"
    pdf_dir = tmp_path / "pdfs"
    output_dir = tmp_path / "out"
    processed = {}

    def fake_procesar_pdf(
        source,
        output_dir,
        ejecutar_blast=True,
        blast_mode="remote",
        nombre_base=None,
    ):
        processed["source"] = source
        processed["nombre_base"] = nombre_base
        return output_dir / f"{nombre_base}.json"

    monkeypatch.setattr(app, "fetch_pdf_bytes", lambda doi: pdf_bytes)
    monkeypatch.setattr(app, "procesar_pdf", fake_procesar_pdf)

    result = CliRunner().invoke(
        app.main,
        [
            "10.1234/example",
            "--output-dir",
            str(output_dir),
            "--pdf-dir",
            str(pdf_dir),
            "--no-save-pdf",
            "--skip-blast",
        ],
    )

    assert result.exit_code == 0
    assert processed["source"] == pdf_bytes
    assert processed["nombre_base"] == "10.1234_example"
    assert not pdf_dir.exists() or not list(pdf_dir.glob("*.pdf"))
    assert "no se guarda en disco" in result.output.lower() or "memoria" in result.output.lower()
    assert "JSON generado:" in result.output


def test_build_resultado_es_agnostico_al_origen(monkeypatch, tmp_path):
    """Path y bytes usan el mismo pipeline de enriquecimiento."""
    extraido = ExtractedArticleData(
        doi="10.1234/example",
        titulo="T",
        organismos=["Danio rerio"],
        proteinas_candidatas=["Lipocalin-2"],
        agrotoxicos_candidatos=["atrazine"],
    )
    seen_sources = []

    def fake_parse(source):
        seen_sources.append(source)
        return extraido

    monkeypatch.setattr(app, "parse_pdf", fake_parse)
    monkeypatch.setattr(
        app,
        "fetch_doi",
        lambda doi: Articulo(doi=doi, titulo="Crossref title"),
    )
    monkeypatch.setattr(
        app,
        "fetch_protein",
        lambda name, organism: ProteinaOrganismoModelo(
            nombre_proteina=name,
            organismo=organism,
            uniprot_id="Q0P4C2",
        ),
    )
    monkeypatch.setattr(
        app,
        "fetch_compound",
        lambda name, familia_quimica=None: Agrotoxico(nombre_comun=name),
    )

    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-fake")
    pdf_bytes = b"%PDF-fake"

    from_path = app.build_resultado_desde_pdf(pdf_path, ejecutar_blast=False)
    from_bytes = app.build_resultado_desde_pdf(pdf_bytes, ejecutar_blast=False)

    assert seen_sources == [pdf_path, pdf_bytes]
    assert from_path.articulo.titulo == from_bytes.articulo.titulo == "Crossref title"
    assert from_path.proteinas[0].uniprot_id == from_bytes.proteinas[0].uniprot_id
    assert from_path.agrotoxicos[0].nombre_comun == from_bytes.agrotoxicos[0].nombre_comun
