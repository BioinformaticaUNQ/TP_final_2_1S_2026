from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseModel:
    nombre: str = ""
    descripcion: str | None = None
