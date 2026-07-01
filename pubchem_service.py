from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import requests


@dataclass
class Agrotoxico:
    nombre_comun: str
    familia_quimica: str | None = None
    smiles: str | None = None
    logP: float | None = None
    fuente_dato: str | None = None

    def toJson(self):
        return {
            "Nombre comun": self.nombre_comun,
            "Familia quimica": self.familia_quimica,
            "SMILES": self.smiles,
            "LogP": self.logP,
            "Fuente de dato": self.fuente_dato,
        }


class PubChemService:
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def fetch_compound(self, nombre_comun: str, familia_quimica: str | None = None) -> Agrotoxico | None:
        encoded_name = quote(nombre_comun)
        url = (
            f"{self.BASE_URL}/compound/name/{encoded_name}"
            "/property/CanonicalSMILES,XLogP/JSON"
        )
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f"Error al obtener datos de PubChem para {nombre_comun}: {response.status_code}")
            return None

        data = response.json()
        properties = data.get("PropertyTable", {}).get("Properties", [])
        if not properties:
            return None

        first = properties[0]
        return Agrotoxico(
            nombre_comun=nombre_comun,
            familia_quimica=familia_quimica,
            smiles=first.get("CanonicalSMILES"),
            logP=first.get("XLogP"),
            fuente_dato="PubChem PUG REST",
        )


def fetch_compound(nombre_comun: str, familia_quimica: str | None = None) -> Agrotoxico | None:
    return PubChemService().fetch_compound(nombre_comun, familia_quimica)