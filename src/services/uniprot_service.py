from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class ProteinaOrganismoModelo:
    nombre_proteina: str
    organismo: str | None = None
    uniprot_id: str | None = None
    pdb_code: str | None = None
    funcion_biologica: str | None = None

    def toJson(self):
        return {
            "Nombre proteina": self.nombre_proteina,
            "Organismo": self.organismo,
            "UniProt ID": self.uniprot_id,
            "PDB code": self.pdb_code,
            "Funcion biologica": self.funcion_biologica,
        }


class UniProtService:
    BASE_URL = "https://rest.uniprot.org/uniprotkb/search"

    def fetch_protein(
        self,
        nombre_proteina: str,
        organismo: str | None = None,
    ) -> ProteinaOrganismoModelo | None:
        query_parts = [nombre_proteina]
        if organismo:
            query_parts.append(f'organism_name:"{organismo}"')

        query = " AND ".join(query_parts)
        response = requests.get(
            self.BASE_URL,
            params={"query": query, "format": "json", "size": 1},
            timeout=30,
        )

        if response.status_code != 200:
            print(f"Error al obtener datos de UniProt para {nombre_proteina}: {response.status_code}")
            return None

        data = response.json()
        results = data.get("results", [])
        if not results:
            return None

        first = results[0]
        protein_desc = first.get("proteinDescription", {})
        recommended_name = protein_desc.get("recommendedName", {})
        organism = first.get("organism", {})
        comments = first.get("comments", [])

        funcion_biologica = None
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    funcion_biologica = texts[0].get("value")
                break

        nombre = recommended_name.get("fullName", {}).get("value") or nombre_proteina

        return ProteinaOrganismoModelo(
            nombre_proteina=nombre,
            organismo=organism.get("scientificName") or organismo,
            uniprot_id=first.get("primaryAccession"),
            pdb_code=None,
            funcion_biologica=funcion_biologica,
        )


def fetch_protein(
    nombre_proteina: str,
    organismo: str | None = None,
) -> ProteinaOrganismoModelo | None:
    return UniProtService().fetch_protein(nombre_proteina, organismo)