from __future__ import annotations

import os
import re
import subprocess
import tempfile
from io import StringIO
from pathlib import Path

from Bio import SeqIO
from Bio.Blast import NCBIWWW, NCBIXML
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from loguru import logger

from models.homologo import HomologoHumano

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BLASTP = PROJECT_ROOT / "data" / "blast" / "ncbi-blast-2.17.0+" / "bin" / "blastp.exe"
DEFAULT_HUMAN_DB = PROJECT_ROOT / "data" / "db" / "human_proteome"

RECNAMEFULL_RE = re.compile(r"RecName:\s*Full=([^;\[]+)", re.IGNORECASE)


class BlastService:
    DATABASE = "swissprot"
    PROGRAM = "blastp"
    ENTREZ_QUERY = "Homo sapiens[Organism]"

    def __init__(
        self,
        mode: str | None = None,
        blastp_bin: str | Path | None = None,
        human_db: str | Path | None = None,
    ) -> None:
        self.mode = (mode or os.environ.get("BLAST_MODE", "remote")).lower()
        self.blastp_bin = Path(blastp_bin or os.environ.get("BLASTP_BIN", DEFAULT_BLASTP))
        self.human_db = Path(human_db or os.environ.get("HUMAN_PROTEOME_DB", DEFAULT_HUMAN_DB))

    def buscar_homologos_humanos(
        self,
        secuencia: str,
        max_hits: int = 15,
    ) -> list[HomologoHumano]:
        if not secuencia:
            logger.warning("Se recibio una secuencia vacia. Cancelando busqueda.")
            return []

        if self.mode == "local":
            if not self._local_disponible():
                raise FileNotFoundError(
                    "BLAST local no configurado. Ejecuta: .\\scripts\\setup_blast_local.ps1"
                )
            logger.info("Iniciando BLASTp local contra proteoma humano UniProt...")
            blast_record = self._ejecutar_blast_local(secuencia, max_hits)
        else:
            logger.info(f"Iniciando BLASTp remoto contra '{self.DATABASE}' (filtro: {self.ENTREZ_QUERY})...")
            blast_record = self._ejecutar_blast_remoto(secuencia, max_hits)

        logger.info("Comenzando el parseo y normalizacion de resultados BLAST...")
        homologos = self._parsear_hits(blast_record, max_hits)
        logger.success(f"BLASTp ({self.mode}) finalizado. Se retornan {len(homologos)} homologos.")
        return homologos

    def _local_disponible(self) -> bool:
        return self.blastp_bin.exists() and self.human_db.with_suffix(".phr").exists()

    def _ejecutar_blast_remoto(self, secuencia: str, max_hits: int):
        try:
            result_handle = NCBIWWW.qblast(
                self.PROGRAM,
                self.DATABASE,
                secuencia,
                entrez_query=self.ENTREZ_QUERY,
                hitlist_size=max_hits,
            )
            logger.success("Conexion con servidor NCBI exitosa.")
        except Exception as exc:
            logger.error(f"Error al consultar NCBI: {exc}")
            raise

        try:
            return NCBIXML.read(result_handle)
        finally:
            result_handle.close()

    def _ejecutar_blast_local(self, secuencia: str, max_hits: int):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            query_fasta = tmp / "query.fasta"
            out_xml = tmp / "result.xml"

            record = SeqRecord(Seq(secuencia), id="query", description="model organism protein")
            SeqIO.write(record, query_fasta, "fasta")

            cmd = [
                str(self.blastp_bin),
                "-query",
                str(query_fasta),
                "-db",
                str(self.human_db),
                "-out",
                str(out_xml),
                "-outfmt",
                "5",
                "-evalue",
                "1e-3",
                "-max_target_seqs",
                str(max_hits),
                "-num_threads",
                str(os.cpu_count() or 4),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            with open(out_xml, encoding="utf-8") as handle:
                xml_text = handle.read()

        if not xml_text.strip():
            raise ValueError("BLAST local devolvio un XML vacio")

        return NCBIXML.read(StringIO(xml_text))

    def _parsear_hits(self, blast_record, max_hits: int) -> list[HomologoHumano]:
        homologos: list[HomologoHumano] = []
        total_alignments = len(blast_record.alignments)
        logger.info(
            f"Se encontraron {total_alignments} alineamientos en total. "
            f"Procesando los mejores {min(max_hits, total_alignments)}."
        )

        for idx, alignment in enumerate(blast_record.alignments[:max_hits], start=1):
            hsp = alignment.hsps[0]
            hit_def_raw = alignment.hit_def or ""
            uniprot_id = self.normalizar_uniprot_id(alignment.accession, alignment.hit_id)
            nombre = self.normalizar_nombre(hit_def_raw)

            longitud_alineamiento = hsp.align_length or 1
            pct_identidad = round((hsp.identities / longitud_alineamiento) * 100, 2)
            pct_similitud = round((hsp.positives / longitud_alineamiento) * 100, 2)
            evalue = self.normalizar_evalue(hsp.expect)

            logger.debug(
                f"Hit #{idx}: ID={uniprot_id} | Nombre={nombre} | "
                f"Identidad={pct_identidad}% | E-value={evalue}"
            )

            homologos.append(
                HomologoHumano(
                    uniprot_id=uniprot_id,
                    nombre=nombre,
                    pct_identidad=pct_identidad,
                    pct_similitud=pct_similitud,
                    evalue=evalue,
                )
            )
        return homologos

    @staticmethod
    def normalizar_uniprot_id(accession: str, hit_id: str) -> str:
        candidato = accession or ""
        if "|" in hit_id:
            partes = hit_id.split("|")
            if len(partes) >= 2 and partes[0] in {"sp", "tr"}:
                candidato = partes[1]
            elif len(partes) >= 2:
                candidato = partes[1]
        return candidato.split(".")[0]

    @staticmethod
    def normalizar_nombre(hit_def: str) -> str:
        if not hit_def:
            return ""

        fragmento = hit_def.split(" >")[0].strip()

        match = RECNAMEFULL_RE.search(fragmento)
        if match:
            return match.group(1).strip()

        if " OS=" in fragmento:
            return fragmento.split(" OS=")[0].strip()

        if "[Homo sapiens]" in fragmento:
            return fragmento.split("[Homo sapiens]")[0].strip().rstrip("; ")

        return fragmento[:200].strip()

    @staticmethod
    def normalizar_evalue(evalue: float | None) -> float | None:
        if evalue is None:
            return None
        if evalue == 0.0:
            return 0.0
        return float(f"{evalue:.6g}")


def buscar_homologos_humanos(
    secuencia: str,
    max_hits: int = 15,
    mode: str | None = None,
) -> list[HomologoHumano]:
    return BlastService(mode=mode).buscar_homologos_humanos(secuencia, max_hits)