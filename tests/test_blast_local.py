from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from services.blast_service import BlastService  # noqa: E402


def test_blast_service_default_es_remoto():
    service = BlastService()
    assert service.mode == "remote"


def test_blast_service_acepta_modo_local():
    service = BlastService(mode="local")
    assert service.mode == "local"


def test_extraer_uniprot_id_sin_version():
    assert BlastService._extraer_uniprot_id("P14780.3", "sp|P14780.3|MMP9_HUMAN") == "P14780"


@pytest.mark.skipif(
    not (
        (ROOT / "data" / "blast" / "ncbi-blast-2.17.0+" / "bin" / "blastp.exe").exists()
        and (ROOT / "data" / "db" / "human_proteome.phr").exists()
    ),
    reason="BLAST local no instalado (ejecutar scripts/setup_blast_local.ps1)",
)
def test_blast_local_apod():
    import requests

    response = requests.get("https://rest.uniprot.org/uniprotkb/Q3B7Q5.fasta", timeout=30)
    secuencia = "".join(
        line.strip()
        for line in response.text.splitlines()
        if not line.startswith(">")
    )
    hits = BlastService(mode="local").buscar_homologos_humanos(secuencia, max_hits=5)

    assert hits
    assert hits[0].uniprot_id == "P05090"
    assert hits[0].pct_identidad == pytest.approx(50.88, rel=0.01)