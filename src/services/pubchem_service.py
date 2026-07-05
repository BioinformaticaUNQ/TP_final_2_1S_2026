from __future__ import annotations

from urllib.parse import quote

import requests

from models.compound import Agrotoxico


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