from __future__ import annotations

from dataclasses import dataclass


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