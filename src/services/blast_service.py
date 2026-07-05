from __future__ import annotations

from dataclasses import dataclass

from Bio.Blast import NCBIWWW, NCBIXML


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
            return []

        result_handle = NCBIWWW.qblast(
            self.PROGRAM,
            self.DATABASE,
            secuencia,
            entrez_query=self.ENTREZ_QUERY,
            hitlist_size=max_hits,
        )

        try:
            blast_record = NCBIXML.read(result_handle)
        finally:
            result_handle.close()

        homologos = []
        for alignment in blast_record.alignments[:max_hits]:
            hsp = alignment.hsps[0]
            uniprot_id = self._extraer_uniprot_id(alignment.accession, alignment.hit_id)
            nombre = alignment.hit_def

            longitud_alineamiento = hsp.align_length or 1
            pct_identidad = round((hsp.identities / longitud_alineamiento) * 100, 2)
            pct_similitud = round((hsp.positives / longitud_alineamiento) * 100, 2)

            homologos.append(
                HomologoHumano(
                    uniprot_id=uniprot_id,
                    nombre=nombre,
                    pct_identidad=pct_identidad,
                    pct_similitud=pct_similitud,
                    evalue=hsp.expect,
                )
            )

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