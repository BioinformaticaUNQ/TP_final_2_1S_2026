from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Agrotoxico:
    nombre_comun: str
    familia_quimica: str | None = None
    smiles: str | None = None
    logP: float | None = None
    tipo_afinidad: str | None = None
    valor_afinidad: str | None = None
    unidad_afinidad: str | None = None
    metodo_experimental: str | None = None
    fuente_dato: str | None = None

    def toJson(self):
        return {
            "Nombre comun": self.nombre_comun,
            "Familia quimica": self.familia_quimica,
            "SMILES": self.smiles,
            "LogP": self.logP,
            "Tipo de afinidad": self.tipo_afinidad,
            "Valor de afinidad": self.valor_afinidad,
            "Unidad de afinidad": self.unidad_afinidad,
            "Metodo experimental": self.metodo_experimental,
            "Fuente de dato": self.fuente_dato,
        }