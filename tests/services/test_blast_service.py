from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from services.blast_service import BlastService  # noqa: E402


def _fake_alignment(accession, hit_id, hit_def, expect, identities=50, positives=70, align_length=100):
    hsp = SimpleNamespace(
        expect=expect,
        align_length=align_length,
        identities=identities,
        positives=positives,
    )
    return SimpleNamespace(accession=accession, hit_id=hit_id, hit_def=hit_def, hsps=[hsp])


def _fake_record(alignments):
    return SimpleNamespace(alignments=alignments)


def test_blast_service_default_es_remoto():
    service = BlastService()
    assert service.mode == "remote"


def test_blast_service_acepta_modo_local():
    service = BlastService(mode="local")
    assert service.mode == "local"


def test_normalizar_uniprot_id_sin_version():
    assert BlastService.normalizar_uniprot_id("P14780.3", "sp|P14780.3|MMP9_HUMAN") == "P14780"


def test_normalizar_nombre_formato_ncbi():
    hit_def = (
        "RecName: Full=Apolipoprotein D; Short=Apo-D; Short=ApoD; "
        "Flags: Precursor [Homo sapiens]"
    )
    assert BlastService.normalizar_nombre(hit_def) == "Apolipoprotein D"


def test_normalizar_nombre_formato_uniprot_local():
    hit_def = "Apolipoprotein D OS=Homo sapiens OX=9606 GN=APOD PE=1 SV=1"
    assert BlastService.normalizar_nombre(hit_def) == "Apolipoprotein D"


def test_normalizar_evalue():
    assert BlastService.normalizar_evalue(4.20599e-61) == 4.20599e-61
    assert BlastService.normalizar_evalue(0.0) == 0.0


def test_buscar_homologos_secuencia_vacia_retorna_lista_vacia():
    assert BlastService().buscar_homologos_humanos("") == []


def test_parsear_hits_descarta_hit_con_evalue_no_significativo():
    record = _fake_record(
        [
            _fake_alignment("Q6UWW0", "sp|Q6UWW0|LCN15_HUMAN", "Lipocalin-15 OS=Homo sapiens", 2.08e-21),
            _fake_alignment(
                "O95376",
                "sp|O95376|ARI2_HUMAN",
                "E3 ubiquitin-protein ligase ARIH2 OS=Homo sapiens",
                9.58279,
            ),
        ]
    )

    hits = BlastService()._parsear_hits(record, max_hits=15)

    assert [h.uniprot_id for h in hits] == ["Q6UWW0"]


def test_parsear_hits_conserva_hits_significativos():
    record = _fake_record(
        [_fake_alignment("Q6UWW0", "sp|Q6UWW0|LCN15_HUMAN", "Lipocalin-15", BlastService.EVALUE_THRESHOLD)]
    )

    hits = BlastService()._parsear_hits(record, max_hits=15)

    assert len(hits) == 1
    assert hits[0].pct_identidad == 50.0
    assert hits[0].pct_similitud == 70.0


def test_parsear_hits_respeta_max_hits_sobre_conjunto_filtrado():
    record = _fake_record(
        [_fake_alignment(f"P{i:05d}", f"sp|P{i:05d}|X_HUMAN", "prot", 1e-10) for i in range(20)]
    )

    hits = BlastService()._parsear_hits(record, max_hits=5)

    assert len(hits) == 5


# Secuencia de Apolipoprotein D de Danio rerio (UniProt Q3B7Q5), horneada para que
# la prueba de integracion BLAST local no dependa de la red (solo del binario local).
APOD_ZEBRAFISH_Q3B7Q5 = (
    "MKAGIVFLTPLLFPLVSAQVFRWGPCPTPMVQPNFELDKYLGKWYEIEKLPASFEKGKCI"
    "EANYMLRPDKTVQVLNIQTYKGKIRKAEGTAIIQDIKEPAKLGVSFSYFTPYAPYWILST"
    "DYNSISLVYSCTDVLRLFHVDYAWILSRSRFLPAGAIYHAKEIFSRDNIDVSKMFATDQQ"
    "GCDNPI"
)


@pytest.mark.skipif(
    not (
        (ROOT / "data" / "blast" / "ncbi-blast-2.17.0+" / "bin" / "blastp.exe").exists()
        and (ROOT / "data" / "db" / "human_proteome.phr").exists()
    ),
    reason="BLAST local no instalado (ejecutar scripts/setup_blast_local.ps1)",
)
def test_blast_local_apod():
    hits = BlastService(mode="local").buscar_homologos_humanos(APOD_ZEBRAFISH_Q3B7Q5, max_hits=5)

    assert hits
    assert hits[0].uniprot_id == "P05090"
    assert hits[0].nombre == "Apolipoprotein D"
    assert hits[0].pct_identidad == pytest.approx(50.88, rel=0.01)