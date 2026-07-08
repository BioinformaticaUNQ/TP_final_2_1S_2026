from __future__ import annotations

import re

from models.candidatos_articulo import AfinidadCandidata, CandidatosArticulo
from utils.pdf_parser import ExtractedArticleData

MAX_PROTEINAS = 10
MAX_AGROTOXICOS = 10

CANDIDATO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\s\-]{1,50}$")
BINOMIAL_RE = re.compile(r"^[A-Z][a-z]+ [a-z]{2,}(?:\s+[a-z]+)?$")
CONCRETE_PROTEIN_RE = re.compile(
    r"^(lipocalin[a-z]*[\s-]?\d+|lcn\d+|obp\d*|csp\d*|[A-Z]{2,}[0-9]+[A-Za-z0-9]*)$",
    re.IGNORECASE,
)

FAMILY_TERMS = frozenset(
    {
        "lipocalin",
        "lipocalina",
        "chemosensory protein",
        "proteina quimiosensorial",
        "proteína quimiosensorial",
        "odorant binding protein",
        "pheromone binding protein",
    }
)

FAMILY_MARKERS = frozenset(
    {
        "lipocalin",
        "lipocalina",
        "odorant",
        "chemosensory",
        "pheromone",
        "quimiosensorial",
    }
)

STOP_TOKENS = frozenset(
    {
        "protein",
        "proteins",
        "proteina",
        "proteína",
        "binding",
        "the",
        "and",
        "of",
    }
)

JUNK_ORGANISM_MARKERS = (
    "protein",
    "proteina",
    "proteína",
    "\n",
    "mrs",
    "iodide",
    "esterase",
)


def es_candidato_proteina_valido(nombre: str) -> bool:
    if not nombre or not CANDIDATO_RE.match(nombre):
        return False
    return 1 <= len(nombre.split()) <= 6


def normalizar_clave(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", texto.lower())


def tokens_significativos(texto: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", texto.lower())
        if token not in STOP_TOKENS and len(token) > 1
    }


def es_organismo_valido(nombre: str) -> bool:
    if not nombre or not BINOMIAL_RE.match(nombre.strip()):
        return False
    lower = nombre.lower()
    return not any(marker in lower for marker in JUNK_ORGANISM_MARKERS)


def score_organismo(nombre: str, titulo: str | None, texto: str) -> tuple[int, int]:
    """Mayor score = mejor. Desempate por frecuencia en texto."""
    score = 0
    lower_nombre = nombre.lower()
    if titulo and lower_nombre in titulo.lower():
        score += 100
    if texto:
        freq = len(re.findall(re.escape(nombre), texto, flags=re.IGNORECASE))
    else:
        freq = 0
    score += min(freq, 20)
    return score, freq


def elegir_organismos(
    organismos: list[str],
    titulo: str | None,
    texto: str = "",
) -> tuple[str | None, list[str]]:
    validos = []
    vistos = set()
    for raw in organismos:
        nombre = " ".join(raw.split())
        if not es_organismo_valido(nombre):
            continue
        clave = normalizar_clave(nombre)
        if clave in vistos:
            continue
        vistos.add(clave)
        validos.append(nombre)

    if not validos:
        return None, []

    ordenados = sorted(
        validos,
        key=lambda n: score_organismo(n, titulo, texto),
        reverse=True,
    )
    return ordenados[0], ordenados[1:]


def score_proteina(nombre: str) -> int:
    compact = nombre.strip()
    lower = compact.lower()
    if compact.isupper() and 2 <= len(compact) <= 8:
        return 70
    if re.match(r"^lipocalin[a-z]*[\s-]?\d+", lower):
        return 100
    if CONCRETE_PROTEIN_RE.match(compact):
        return 90
    if re.search(r"\d", compact) and any(m in lower for m in FAMILY_MARKERS):
        return 85
    if lower in FAMILY_TERMS:
        return 20
    if any(term in lower for term in FAMILY_TERMS):
        return 25
    return 40


def rankear_proteinas(candidatos: list[str], limite: int = MAX_PROTEINAS) -> list[str]:
    mejores: dict[str, tuple[int, int, str]] = {}
    for raw in candidatos:
        nombre = " ".join(raw.split())
        if not es_candidato_proteina_valido(nombre):
            continue
        clave = normalizar_clave(nombre)
        if not clave:
            continue
        item = (score_proteina(nombre), len(nombre), nombre)
        actual = mejores.get(clave)
        if actual is None or item[:2] > actual[:2]:
            mejores[clave] = item

    ranked = sorted(mejores.values(), key=lambda item: (item[0], item[1]), reverse=True)
    return [nombre for _, _, nombre in ranked[:limite]]


def hit_uniprot_aceptable(candidato: str, nombre_hit: str | None) -> bool:
    if not candidato or not nombre_hit:
        return False

    c_norm = normalizar_clave(candidato)
    h_norm = normalizar_clave(nombre_hit)
    if c_norm and (c_norm in h_norm or h_norm in c_norm):
        return True

    c_tokens = tokens_significativos(candidato)
    h_tokens = tokens_significativos(nombre_hit)
    if c_tokens & h_tokens:
        return True

    c_lower = candidato.lower()
    h_lower = nombre_hit.lower()
    if any(marker in c_lower for marker in FAMILY_MARKERS):
        return any(marker in h_lower for marker in FAMILY_MARKERS)

    if candidato.isupper() and 2 <= len(candidato) <= 8:
        return candidato.lower() in h_lower

    return False


def asignar_afinidades(
    afinidades: list[dict],
    agrotoxicos: list[str],
) -> list[AfinidadCandidata]:
    """
    Solo asigna agrotoxico cuando el vínculo es confiable:
    un solo agrotóxico y una o más afinidades medidas.
    Si hay varios agros, las afinidades quedan sin dueño.
    """
    result: list[AfinidadCandidata] = []
    unico_agro = agrotoxicos[0] if len(agrotoxicos) == 1 else None

    for item in afinidades:
        result.append(
            AfinidadCandidata(
                tipo=item.get("tipo"),
                valor=item.get("valor"),
                unidad=item.get("unidad"),
                agrotoxico=unico_agro,
            )
        )
    return result


def build_candidatos_articulo(extraido: ExtractedArticleData) -> CandidatosArticulo:
    titulo = extraido.titulo
    texto = extraido.texto_completo or ""

    organismo, secundarios = elegir_organismos(extraido.organismos, titulo, texto)
    proteinas = rankear_proteinas(extraido.proteinas_candidatas)
    agrotoxicos = list(
        dict.fromkeys(
            " ".join(nombre.split())
            for nombre in extraido.agrotoxicos_candidatos[:MAX_AGROTOXICOS]
            if nombre
        )
    )
    familias = {
        nombre: familia
        for nombre, familia in extraido.familias_agrotoxicos.items()
        if nombre in agrotoxicos
    }
    afinidades = asignar_afinidades(extraido.afinidades, agrotoxicos)

    return CandidatosArticulo(
        organismo_principal=organismo,
        organismos_secundarios=secundarios,
        proteinas=proteinas,
        agrotoxicos=agrotoxicos,
        familias_agrotoxicos=familias,
        afinidades=afinidades,
        metodos_experimentales=list(extraido.metodos_experimentales),
        codigos_pdb=list(extraido.codigos_pdb),
    )
