from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Articulo:
    doi: str
    titulo: str | None = None
    autores: list[str] = field(default_factory=list)
    anio: int | None = None
    revista: str | None = None

    def toJson(self):
        return {
            "DOI": self.doi,
            "Titulo": self.titulo,
            "Autores": self.autores,
            "Anio de Publicacion": self.anio,
            "Revista": self.revista,
        }