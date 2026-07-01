from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HomologoHumano:
    uniprot_id: str = ""
    nombre: str = ""
    pct_identidad: float | None = None
    pct_similitud: float | None = None
    evalue: float | None = None

    def toJson(self):
        return {
            "uniprot_id": self.uniprot_id,
            "nombre": self.nombre,
            "pct_identidad": self.pct_identidad,
            "pct_similitud": self.pct_similitud,
            "evalue": self.evalue,
        }