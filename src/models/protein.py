from __future__ import annotations

from dataclasses import dataclass


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