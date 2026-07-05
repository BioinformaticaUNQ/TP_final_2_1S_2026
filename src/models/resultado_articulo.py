from __future__ import annotations

from dataclasses import dataclass, field

from .article import Articulo
from .compound import Agrotoxico
from .homologo import HomologoHumano
from .protein import ProteinaOrganismoModelo


@dataclass
class ResultadoArticulo:
    articulo: Articulo = field(default_factory=Articulo)
    proteinas: list[ProteinaOrganismoModelo] = field(default_factory=list)
    agrotoxicos: list[Agrotoxico] = field(default_factory=list)
    homologos: list[HomologoHumano] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "articulo": {
                "doi": self.articulo.doi,
                "titulo": self.articulo.titulo,
                "autores": self.articulo.autores,
                "año": self.articulo.anio,
                "revista": self.articulo.revista,
            },
            "proteinas": [
                {
                    "nombre": p.nombre_proteina,
                    "organismo": p.organismo,
                    "uniprot_id": p.uniprot_id,
                    "pdb_code": p.pdb_code,
                    "funcion_biologica": p.funcion_biologica,
                }
                for p in self.proteinas
            ],
            "agrotoxicos": [
                {
                    "nombre_comun": a.nombre_comun,
                    "familia_quimica": a.familia_quimica,
                    "smiles": a.smiles,
                    "logP": a.logP,
                    "tipo_afinidad": a.tipo_afinidad,
                    "valor_afinidad": a.valor_afinidad,
                    "unidad_afinidad": a.unidad_afinidad,
                    "metodo_experimental": a.metodo_experimental,
                    "fuente_dato": a.fuente_dato,
                }
                for a in self.agrotoxicos
            ],
            "homologos_humanos": [
                {
                    "uniprot_id": h.uniprot_id,
                    "nombre": h.nombre,
                    "pct_identidad": h.pct_identidad,
                    "pct_similitud": h.pct_similitud,
                    "evalue": h.evalue,
                }
                for h in self.homologos
            ],
        }