from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@dataclass
class MockResponse:
    status_code: int
    payload: dict | None = None
    text: str = ""

    def json(self) -> dict:
        return self.payload or {}


@pytest.fixture
def crossref_payload() -> dict:
    return {
        "message": {
            "title": ["Lipocalin binding study"],
            "container-title": ["Bioinformatics Journal"],
            "published-online": {"date-parts": [[2024, 5, 10]]},
            "author": [
                {"given": "Ada", "family": "Lovelace"},
                {"given": "Grace", "family": "Hopper"},
            ],
        }
    }


@pytest.fixture
def pubchem_payload() -> dict:
    return {
        "PropertyTable": {
            "Properties": [
                {
                    "CID": 2256,
                    "CanonicalSMILES": "CCNC1=NC(=NC(=N1)Cl)NC(C)C",
                    "XLogP": 2.6,
                }
            ]
        }
    }


@pytest.fixture
def uniprot_payload() -> dict:
    return {
        "results": [
            {
                "primaryAccession": "Q0P4C2",
                "proteinDescription": {
                    "recommendedName": {
                        "fullName": {"value": "Lipocalin 2"},
                    }
                },
                "organism": {"scientificName": "Danio rerio"},
                "comments": [
                    {
                        "commentType": "FUNCTION",
                        "texts": [{"value": "Binds small hydrophobic ligands."}],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def article_text() -> str:
    return "\n".join(
        [
            "Lipocalin 2 binds atrazine in zebrafish",
            "doi:10.1234/example.2024.15",
            "Danio rerio (zebrafish) was used as model organism.",
            "Lipocalin-2 (LCN2) was tested against atrazine and imidacloprid.",
            "The affinity was Kd = 2.5 mM by ITC and molecular docking.",
            "PDB ID: 1ABC",
        ]
    )
