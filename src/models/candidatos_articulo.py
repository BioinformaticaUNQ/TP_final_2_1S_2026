from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AfinidadCandidata:
    tipo: str | None = None
    valor: str | None = None
    unidad: str | None = None
    agrotoxico: str | None = None


@dataclass
class CandidatosArticulo:
    """Entidades del paper que se van a consultar en bases externas."""

    organismo_principal: str | None = None
    organismos_secundarios: list[str] = field(default_factory=list)
    proteinas: list[str] = field(default_factory=list)
    agrotoxicos: list[str] = field(default_factory=list)
    familias_agrotoxicos: dict[str, str] = field(default_factory=dict)
    afinidades: list[AfinidadCandidata] = field(default_factory=list)
    metodos_experimentales: list[str] = field(default_factory=list)
    codigos_pdb: list[str] = field(default_factory=list)
