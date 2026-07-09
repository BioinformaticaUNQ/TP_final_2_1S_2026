from __future__ import annotations

from services.candidatos_articulo import (
    asignar_afinidades,
    build_candidatos_articulo,
    elegir_organismos,
    hit_uniprot_aceptable,
    rankear_proteinas,
    score_proteina,
)
from utils.pdf_parser import ExtractedArticleData


def test_elige_organismo_del_titulo_sobre_orden_alfabetico():
    principal, secundarios = elegir_organismos(
        ["Apis mellifera", "Aphis gossypii", "Danio rerio"],
        titulo="Resistance in Aphis gossypii Glover to insecticides",
        texto="Aphis gossypii Aphis gossypii Apis mellifera",
    )

    assert principal == "Aphis gossypii"
    assert "Apis mellifera" in secundarios


def test_descarta_organismos_basura():
    principal, secundarios = elegir_organismos(
        ["Acetylthiocholine iodide", "Chemosensory proteins\n(MRS)", "Danio rerio"],
        titulo="Lipocalin-2 in zebrafish",
        texto="Danio rerio",
    )

    assert principal == "Danio rerio"
    assert secundarios == []


def test_rankea_proteinas_concretas_sobre_familia():
    ranked = rankear_proteinas(
        [
            "lipocalin",
            "LCN2",
            "Lipocalin-2",
            "chemosensory protein",
            "bad/candidate",
        ],
        titulo="Modulation by Lipocalin-2 in Zebrafish",
    )

    assert ranked[0] == "Lipocalin-2"
    assert "lipocalin" in ranked
    assert (
        score_proteina("Lipocalin-2", titulo="Lipocalin-2 study")
        > score_proteina("LCN2")
        > score_proteina("lipocalin")
    )
    assert "bad/candidate" not in ranked


def test_rankea_gen_obp_sobre_familia():
    ranked = rankear_proteinas(
        ["odorant binding protein", "AgOBP1", "CSP6"],
        titulo="AgOBP1 and CSP6 in Aphis gossypii",
    )
    assert ranked[0] in {"AgOBP1", "CSP6"}
    assert score_proteina("AgOBP1") > score_proteina("odorant binding protein")


def test_penaliza_lipocalin_numerica_fuera_del_titulo():
    ranked = rankear_proteinas(
        ["lipocalin 21", "Lipocalin-2", "lipocalin"],
        titulo="Lipocalin-2 in zebrafish",
    )
    assert ranked[0] == "Lipocalin-2"


def test_hit_uniprot_rechaza_falso_positivo_de_acronimo():
    assert hit_uniprot_aceptable(
        "Lipocalin-2",
        "Lipocalin 2",
        organismo_esperado="Danio rerio",
        organismo_hit="Danio rerio",
    )
    assert hit_uniprot_aceptable(
        "chemosensory protein",
        "chemosensory protein 3",
        organismo_esperado="Aphis gossypii",
        organismo_hit="Aphis gossypii",
    )
    assert not hit_uniprot_aceptable("LCN2", "Matrix metalloproteinase-9")


def test_hit_uniprot_rechaza_especie_incorrecta():
    from services.candidatos_articulo import organismo_uniprot_aceptable

    assert organismo_uniprot_aceptable("Tribolium castaneum", "Tribolium castaneum")
    assert organismo_uniprot_aceptable("Aphis gossypii", "Aphis gossypii")
    assert not organismo_uniprot_aceptable("Tribolium castaneum", "Locusta migratoria")
    assert not organismo_uniprot_aceptable("Danio rerio", "Homo sapiens")
    assert not hit_uniprot_aceptable(
        "OBP11",
        "Odorant-binding protein 11",
        organismo_esperado="Tribolium castaneum",
        organismo_hit="Locusta migratoria",
    )
    assert hit_uniprot_aceptable(
        "OBP11",
        "Odorant-binding protein 11",
        organismo_esperado="Tribolium castaneum",
        organismo_hit="Tribolium castaneum",
    )


def test_afinidad_solo_se_asigna_con_un_agrotoxico():
    con_uno = asignar_afinidades(
        [{"tipo": "Kd", "valor": "2.5", "unidad": "mM"}],
        ["atrazine"],
    )
    assert con_uno[0].agrotoxico == "atrazine"

    con_varios = asignar_afinidades(
        [{"tipo": "Ki", "valor": "48.33", "unidad": "μM"}],
        ["chlorpyrifos", "imidacloprid"],
    )
    assert con_varios[0].agrotoxico is None


def test_build_candidatos_articulo_integra_reglas():
    extraido = ExtractedArticleData(
        titulo="Lipocalin-2 in Danio rerio",
        texto_completo="Danio rerio Danio rerio Apis mellifera Lipocalin-2",
        organismos=["Apis mellifera", "Danio rerio"],
        proteinas_candidatas=["lipocalin", "Lipocalin-2", "LCN2"],
        agrotoxicos_candidatos=["atrazine"],
        familias_agrotoxicos={"atrazine": "Triazina"},
        afinidades=[{"tipo": "Kd", "valor": "1.0", "unidad": "uM"}],
        metodos_experimentales=["ITC"],
        codigos_pdb=["1ABC"],
    )

    candidatos = build_candidatos_articulo(extraido)

    assert candidatos.organismo_principal == "Danio rerio"
    assert candidatos.proteinas[0] == "Lipocalin-2"
    assert candidatos.agrotoxicos == ["atrazine"]
    assert candidatos.afinidades[0].agrotoxico == "atrazine"
    assert candidatos.codigos_pdb == ["1ABC"]
