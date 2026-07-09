from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from loguru import logger

GENE_LIKE_RE = re.compile(
    r"^(?:[A-Z][a-z]{0,4})?(?:OBP|CSP|PBP|GOBP|ABP|LCN)\d+[a-zA-Z]?$",
    re.IGNORECASE,
)
SPECIES_PREFIX_RE = re.compile(r"^([A-Z][a-z]{1,4})((?:OBP|CSP|PBP|GOBP|ABP|LCN)\d+[a-zA-Z]?)$")


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

    def _search(
        self,
        query: str,
        nombre_fallback: str | None = None,
    ) -> ProteinaOrganismoModelo | None:
        logger.info(f"Consultando UniProt con query: '{query}'")
        try:
            response = requests.get(
                self.BASE_URL,
                params={"query": query, "format": "json", "size": 1},
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo de red en UniProt para '{query}': {e}")
            return None

        if response.status_code != 200:
            logger.error(f"Error {response.status_code} en UniProt.")
            return None

        results = response.json().get("results", [])
        if not results:
            logger.warning(f"UniProt no arrojó resultados para '{query}'.")
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

        nombre = (
            recommended_name.get("fullName", {}).get("value")
            or nombre_fallback
            or first.get("uniProtkbId")
            or "unknown"
        )
        uniprot_id = first.get("primaryAccession")
        logger.success(f"Proteína encontrada: {nombre} (ID: {uniprot_id})")

        return ProteinaOrganismoModelo(
            nombre_proteina=nombre,
            organismo=organism.get("scientificName"),
            uniprot_id=uniprot_id,
            pdb_code=None,
            funcion_biologica=funcion_biologica,
        )

    @staticmethod
    def _query_variants(nombre_proteina: str, organismo: str | None) -> list[str]:
        """Arma queries de mayor a menor especificidad.

        Si hay organismo y el nombre parece gen (OBP/CSP), no se buscan
        hits sin organismo: evita devolver otra especie y filtrarla despues.
        """
        name = nombre_proteina.strip()
        variants: list[str] = []
        is_gene = bool(GENE_LIKE_RE.match(name))

        def add(q: str) -> None:
            if q and q not in variants:
                variants.append(q)

        if organismo:
            add(f'{name} AND organism_name:"{organismo}"')
        elif not is_gene:
            add(name)

        if is_gene:
            core = name
            m = SPECIES_PREFIX_RE.match(name)
            if m:
                core = m.group(2)  # BmorOBP27 -> OBP27
            if organismo:
                add(f'gene:{core} AND organism_name:"{organismo}"')
                add(f'gene_exact:{core} AND organism_name:"{organismo}"')
                add(f'{core} AND organism_name:"{organismo}"')
                # Fallback de familia en el mismo organismo (TP insectos)
                if re.search(r"OBP|PBP|GOBP|ABP", core, re.I):
                    add(f'organism_name:"{organismo}" AND (odorant binding OR OBP)')
                if re.search(r"CSP", core, re.I):
                    add(f'organism_name:"{organismo}" AND (chemosensory OR CSP)')
            else:
                add(f"gene:{core}")
                add(core)
        elif not organismo:
            add(name)

        return variants

    def fetch_protein(
        self,
        nombre_proteina: str,
        organismo: str | None = None,
    ) -> ProteinaOrganismoModelo | None:
        if not nombre_proteina:
            logger.warning("Nombre de proteína vacío. Omitiendo búsqueda en UniProt.")
            return None

        for query in self._query_variants(nombre_proteina, organismo):
            hit = self._search(query, nombre_fallback=nombre_proteina)
            if hit is not None:
                return hit
        return None

    def fetch_sequence(self, uniprot_id: str) -> str | None:
        if not uniprot_id:
            return None

        url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
        logger.info(f"Descargando secuencia FASTA para ID: {uniprot_id}")

        try:
            response = requests.get(url, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo al descargar secuencia para {uniprot_id}: {e}")
            return None

        if response.status_code != 200:
            logger.error(f"Error {response.status_code} al bajar secuencia FASTA.")
            return None

        lineas = response.text.splitlines()
        secuencia = "".join(linea.strip() for linea in lineas if not linea.startswith(">"))
        
        if secuencia:
            logger.success(f"Secuencia descargada ({len(secuencia)} aminoácidos).")
        else:
            logger.warning(f"Secuencia vacía para {uniprot_id}.")
            
        return secuencia or None


def fetch_protein(
    nombre_proteina: str,
    organismo: str | None = None,
) -> ProteinaOrganismoModelo | None:
    return UniProtService().fetch_protein(nombre_proteina, organismo)


def fetch_sequence(uniprot_id: str) -> str | None:
    return UniProtService().fetch_sequence(uniprot_id)