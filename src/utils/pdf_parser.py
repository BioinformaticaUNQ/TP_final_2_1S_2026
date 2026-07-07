from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+")

ORGANISM_PATTERNS = [
    re.compile(r"\b([A-Z][a-z]+ [a-z]{3,})\s*\(([A-Za-z ]+)\)"),
    re.compile(r"\b(Danio rerio|Apis mellifera|Homo sapiens|Mus musculus|Rattus norvegicus|Xenopus laevis|Caenorhabditis elegans|Drosophila melanogaster)\b"),
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
    afinidades: list[dict] = field(default_factory=list)
    metodos_experimentales: list[str] = field(default_factory=list)
    codigos_pdb: list[str] = field(default_factory=list)


class PdfParser:
    PDB_RE = re.compile(r"\b(?:PDB\s*(?:ID|code|entry)?\s*[:\-]?\s*)([1-9][A-Za-z0-9]{3})\b", re.IGNORECASE)
    TITLE_IGNORE = ("doi", "abstract", "resumen", "university", "copyright", "downloaded", "author", "issn", "journal")

    def parse(self, path: str | Path) -> ExtractedArticleData:
        path = Path(path)
        texto_completo = self._extract_text(path)

        data = ExtractedArticleData(texto_completo=texto_completo)
        data.doi = self._extract_doi(texto_completo)
        data.titulo = self._extract_title(path, texto_completo)
        data.organismos = self._extract_organisms(texto_completo)
        data.proteinas_candidatas = self._extract_proteins(texto_completo)
        data.agrotoxicos_candidatos = self._extract_agrotoxicos(texto_completo)
        data.afinidades = self._extract_affinities(texto_completo)
        data.metodos_experimentales = self._extract_methods(texto_completo)
        data.codigos_pdb = self._extract_pdb_codes(texto_completo)

        return data

    def _extract_text(self, path: Path) -> str:
        pages_text = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        return "\n".join(pages_text)

    def _extract_doi(self, texto: str) -> str | None:
        match = DOI_RE.search(texto)
        if match:
            return match.group(0).rstrip(".,;")
        return None

    def _extract_title(self, path: Path, texto: str) -> str | None:
        lines = [line.strip() for line in texto.splitlines() if line.strip()]
        for line in lines[:20]:
            if len(line) > 20 and not line.lower().startswith(self.TITLE_IGNORE):
                return line
        return path.stem

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


def parse_pdf(path: str | Path) -> ExtractedArticleData:
    return PdfParser().parse(path)
