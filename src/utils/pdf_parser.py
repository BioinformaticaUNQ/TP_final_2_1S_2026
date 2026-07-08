from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pdfplumber

PdfInput = str | Path | bytes | bytearray | BinaryIO


def as_pdfplumber_source(source: PdfInput):
    """Normaliza path o bytes a un objeto aceptado por pdfplumber.open."""
    if isinstance(source, (bytes, bytearray)):
        return BytesIO(source)
    if isinstance(source, (str, Path)):
        return Path(source)
    return source

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+")

ORGANISM_PATTERNS = [
    re.compile(r"\b([A-Z][a-z]+ [a-z]{3,})\s*\(([A-Za-z ]+)\)"),
    re.compile(
        r"\b("
        r"Danio rerio|Apis mellifera|Homo sapiens|Mus musculus|Rattus norvegicus|"
        r"Xenopus laevis|Caenorhabditis elegans|Drosophila melanogaster|"
        r"Aphis gossypii|Tribolium castaneum|Rhopalosiphum padi|Bombyx mori"
        r")\b"
    ),
]

COMMON_NAME_TO_SCIENTIFIC = {
    "zebrafish": "Danio rerio",
    "pez cebra": "Danio rerio",
    "honeybee": "Apis mellifera",
    "honey bee": "Apis mellifera",
    "abeja": "Apis mellifera",
    "fruit fly": "Drosophila melanogaster",
    "mosca de la fruta": "Drosophila melanogaster",
    "house mouse": "Mus musculus",
    "raton": "Mus musculus",
    "ratón": "Mus musculus",
    "clawed frog": "Xenopus laevis",
    "rana": "Xenopus laevis",
    "cotton aphid": "Aphis gossypii",
    "red flour beetle": "Tribolium castaneum",
}

PROTEIN_FAMILY_TERMS = [
    "lipocalin", "lipocalina",
    "chemosensory protein", "proteina quimiosensorial", "proteína quimiosensorial",
    "odorant binding protein", "pheromone binding protein",
]

LIPOCALIN_NAME_RE = re.compile(r"\bLipocalin[a-zA-Z]*[\s-]?\d+\b", re.IGNORECASE)
ACRONYM_NEAR_LIPOCALIN_RE = re.compile(
    r"lipocalin[\w\s\-]{0,25}?\(([A-Z][A-Z0-9]{1,7})\)", re.IGNORECASE
)

AGROTOXICOS_ESPECIFICOS = [
    "atrazine", "atrazina", "imidacloprid", "chlorpyrifos", "clorpirifos",
    "glyphosate", "glifosato", "alachlor", "malathion", "permethrin",
    "flonicamid", "avermectin", "deltamethrin",
]

AGROTOXICO_FAMILIAS = {
    "alachlor": "Cloroacetanilida",
    "atrazine": "Triazina",
    "atrazina": "Triazina",
    "avermectin": "Avermectina",
    "chlorpyrifos": "Organofosforado",
    "clorpirifos": "Organofosforado",
    "deltamethrin": "Piretroide",
    "flonicamid": "Piridinacarboxamida",
    "glyphosate": "Organofosfonato",
    "glifosato": "Organofosfonato",
    "imidacloprid": "Neonicotinoide",
    "malathion": "Organofosforado",
    "permethrin": "Piretroide",
}

FAMILIAS_Y_GENERALES = [
    "neonicotinoid", "neonicotinoide", "triazine", "triazina",
    "herbicide", "herbicida", "pesticide", "pesticida", "insecticide", "insecticida",
]

AFFINITY_RE = re.compile(
    r"\b(K[dDiI]|IC50|EC50)\s*(?:=|of|:)?\s*([\d\.]+)\s*(nM|uM|µM|pM|mM|M)",
    re.IGNORECASE,
)

METHOD_KEYWORDS = [
    "ITC", "isothermal titration calorimetry",
    "fluorescence", "fluorescencia",
    "docking", "molecular docking",
    "surface plasmon resonance", "SPR",
    "crystallography", "cristalografia", "cristalografía",
]


@dataclass
class ExtractedArticleData:
    doi: str | None = None
    titulo: str | None = None
    texto_completo: str = ""
    organismos: list[str] = field(default_factory=list)
    proteinas_candidatas: list[str] = field(default_factory=list)
    agrotoxicos_candidatos: list[str] = field(default_factory=list)
    familias_agrotoxicos: dict[str, str] = field(default_factory=dict)
    afinidades: list[dict] = field(default_factory=list)
    metodos_experimentales: list[str] = field(default_factory=list)
    codigos_pdb: list[str] = field(default_factory=list)


class PdfParser:
    PDB_RE = re.compile(r"\b(?:PDB\s*(?:ID|code|entry)?\s*[:\-]?\s*)([1-9][A-Za-z0-9]{3})\b", re.IGNORECASE)
    TITLE_IGNORE = (
        "doi",
        "abstract",
        "resumen",
        "university",
        "digitalcommons",
        "department",
        "publications",
        "follow this",
        "part of the",
        "this article",
        "published in",
        "copyright",
        "downloaded",
        "author",
        "issn",
        "journal",
    )

    def parse(self, source: PdfInput) -> ExtractedArticleData:
        path_for_title = Path(source) if isinstance(source, (str, Path)) else None
        texto_completo = self._extract_text(source)

        data = ExtractedArticleData(texto_completo=texto_completo)
        data.doi = self._extract_doi(texto_completo)
        data.titulo = self._extract_title(path_for_title, texto_completo)
        data.organismos = self._extract_organisms(texto_completo)
        data.proteinas_candidatas = self._extract_proteins(texto_completo)
        data.agrotoxicos_candidatos = self._extract_agrotoxicos(texto_completo)
        data.familias_agrotoxicos = self._extract_agrotoxic_families(data.agrotoxicos_candidatos)
        data.afinidades = self._extract_affinities(texto_completo)
        data.metodos_experimentales = self._extract_methods(texto_completo)
        data.codigos_pdb = self._extract_pdb_codes(texto_completo)

        return data

    def _extract_text(self, source: PdfInput) -> str:
        pages_text = []
        with pdfplumber.open(as_pdfplumber_source(source)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        return "\n".join(pages_text)

    def _extract_doi(self, texto: str) -> str | None:
        texto_normalizado = re.sub(r"(10\.\d{4,9}/[^\s]+)\s+(\.[^\s]+)", r"\1\2", texto)
        match = DOI_RE.search(texto_normalizado)
        if match:
            return match.group(0).rstrip(".,;")
        return None

    def _extract_title(self, path: Path | None, texto: str) -> str | None:
        lines = [self._normalize_extracted_line(line) for line in texto.splitlines()]
        lines = [line for line in lines if line]
        for idx, line in enumerate(lines[:30]):
            lower = line.lower()
            if len(line) <= 20 or lower.startswith(self.TITLE_IGNORE):
                continue
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                next_lower = next_line.lower()
                if (
                    8 < len(next_line) <= 90
                    and not next_lower.startswith(self.TITLE_IGNORE)
                    and not DOI_RE.search(next_line)
                ):
                    return f"{line} {next_line}"
            return line
        return path.stem if path is not None else None

    def _normalize_extracted_line(self, line: str) -> str:
        line = " ".join(line.strip().split())
        if not line:
            return ""
        return self._collapse_repeated_glyphs(line)

    def _collapse_repeated_glyphs(self, text: str) -> str:
        chars = [char for char in text if not char.isspace()]
        if not chars:
            return text

        repeated_pairs = sum(
            1
            for idx in range(len(text) - 1)
            if not text[idx].isspace() and text[idx] == text[idx + 1]
        )
        if repeated_pairs / len(chars) >= 0.35:
            collapsed = []
            idx = 0
            while idx < len(text):
                collapsed.append(text[idx])
                if idx + 1 < len(text) and not text[idx].isspace() and text[idx] == text[idx + 1]:
                    idx += 2
                else:
                    idx += 1
            return "".join(collapsed)
        return text

    def _extract_organisms(self, texto: str) -> list[str]:
        found = set()
        for pattern in ORGANISM_PATTERNS:
            for match in pattern.finditer(texto):
                if match.groups():
                    found.add(match.group(0).strip())
                else:
                    found.add(match.group(0))

        lower = texto.lower()
        for nombre_comun, nombre_cientifico in COMMON_NAME_TO_SCIENTIFIC.items():
            if nombre_comun in lower:
                found.add(nombre_cientifico)

        return sorted(found)

    def _extract_proteins(self, texto: str) -> list[str]:
        found = set()

        for match in LIPOCALIN_NAME_RE.finditer(texto):
            nombre = re.sub(r"\s*-\s*", "-", match.group(0))
            found.add(nombre)

        for match in ACRONYM_NEAR_LIPOCALIN_RE.finditer(texto):
            found.add(match.group(1))

        lower = texto.lower()
        for term in PROTEIN_FAMILY_TERMS:
            if term in lower:
                found.add(term)

        return sorted(found)

    def _extract_agrotoxicos(self, texto: str) -> list[str]:
        found = set()
        lower = texto.lower()
        for keyword in AGROTOXICOS_ESPECIFICOS:
            if keyword.lower() in lower:
                found.add(keyword)
        return sorted(found)

    def _extract_agrotoxic_families(self, agrotoxicos: list[str]) -> dict[str, str]:
        return {
            nombre: familia
            for nombre in agrotoxicos
            if (familia := AGROTOXICO_FAMILIAS.get(nombre.lower()))
        }

    def _extract_affinities(self, texto: str) -> list[dict]:
        results = []
        for match in AFFINITY_RE.finditer(texto):
            results.append(
                {
                    "tipo": match.group(1),
                    "valor": match.group(2),
                    "unidad": match.group(3),
                }
            )
        return results

    def _extract_methods(self, texto: str) -> list[str]:
        found = set()
        lower = texto.lower()
        for keyword in METHOD_KEYWORDS:
            if keyword.lower() in lower:
                found.add(keyword)
        return sorted(found)

    def _extract_pdb_codes(self, texto: str) -> list[str]:
        found = set()
        for match in self.PDB_RE.finditer(texto):
            found.add(match.group(1).upper())
        return sorted(found)


def parse_pdf(source: PdfInput) -> ExtractedArticleData:
    return PdfParser().parse(source)
