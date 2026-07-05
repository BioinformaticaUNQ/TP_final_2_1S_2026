from __future__ import annotations

from dataclasses import dataclass

from Bio.Blast import NCBIWWW, NCBIXML
from loguru import logger


@dataclass
class HomologoHumano:
    uniprot_id: str = ""
    nombre: str = ""
    pct_identidad: float | None = None
    pct_similitud: float | None = None
    evalue: float | None = None

    def toJson(self):
        return {
            "uniprot_id": self.uniprot_id,
            "nombre": self.nombre,
            "pct_identidad": self.pct_identidad,
            "pct_similitud": self.pct_similitud,
            "evalue": self.evalue,
        }


class BlastService:
    DATABASE = "swissprot"
    PROGRAM = "blastp"
    ENTREZ_QUERY = "Homo sapiens[Organism]"

    def buscar_homologos_humanos(
        self,
        secuencia: str,
        max_hits: int = 15,
    ) -> list[HomologoHumano]:
        if not secuencia:
            logger.warning("Se recibió una secuencia vacía. Cancelando búsqueda.")
            return []

        logger.info(f"Iniciando búsqueda BLASTp online contra la base de datos '{self.DATABASE}'...")
        logger.info(f"Filtro Entrez aplicado: '{self.ENTREZ_QUERY}'")
        
        try:
            result_handle = NCBIWWW.qblast(
                self.PROGRAM,
                self.DATABASE,
                secuencia,
                entrez_query=self.ENTREZ_QUERY,
                hitlist_size=max_hits,
            )
            logger.success("Conexión con el servidor de NCBI exitosa. Respuesta recibida.")
        except Exception as e:
            logger.error(f"Error al conectar o recibir datos del servidor NCBI: {e}")
            raise e

        try:
            logger.info("Comenzando el parseo del archivo XML de resultados...")
            blast_record = NCBIXML.read(result_handle)
        finally:
            result_handle.close()

        homologos = []
        total_alignments = len(blast_record.alignments)
        logger.info(f"Se encontraron {total_alignments} alineamientos en total. Procesando los mejores {min(max_hits, total_alignments)}.")

        for idx, alignment in enumerate(blast_record.alignments[:max_hits], start=1):
            hsp = alignment.hsps[0]
            uniprot_id = self._extraer_uniprot_id(alignment.accession, alignment.hit_id)
            nombre = alignment.hit_def

            longitud_alineamiento = hsp.align_length or 1
            pct_identidad = round((hsp.identities / longitud_alineamiento) * 100, 2)
            pct_similitud = round((hsp.positives / longitud_alineamiento) * 100, 2)

            logger.debug(f"Hit #{idx}: ID={uniprot_id} | Identidad={pct_identidad}% | E-value={hsp.expect}")

            homologos.append(
                HomologoHumano(
                    uniprot_id=uniprot_id,
                    nombre=nombre,
                    pct_identidad=pct_identidad,
                    pct_similitud=pct_similitud,
                    evalue=hsp.expect,
                )
            )

        logger.success(f"Procesamiento finalizado correctamente. Se retornan {len(homologos)} homólogos humanos.")
        return homologos

    @staticmethod
    def _extraer_uniprot_id(accession: str, hit_id: str) -> str:
        if "|" in hit_id:
            partes = hit_id.split("|")
            if len(partes) >= 2:
                return partes[1]
        return accession


def buscar_homologos_humanos(secuencia: str, max_hits: int = 15) -> list[HomologoHumano]:
    return BlastService().buscar_homologos_humanos(secuencia, max_hits)