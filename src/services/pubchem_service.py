from __future__ import annotations

from urllib.parse import quote

import requests
from loguru import logger

from models.compound import Agrotoxico


class PubChemService:
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def fetch_compound(self, nombre_comun: str, familia_quimica: str | None = None) -> Agrotoxico | None:
        if not nombre_comun:
            logger.warning("Se recibió un nombre de compuesto vacío. Omitiendo búsqueda.")
            return None

        clean_name = nombre_comun.strip(" \n\r\t.,;")
        
        encoded_name = quote(clean_name)
        url = (
            f"{self.BASE_URL}/compound/name/{encoded_name}"
            "/property/CanonicalSMILES,XLogP/JSON"
        )
        
        logger.info(f"Consultando PubChem para el compuesto: '{clean_name}'")
        logger.debug(f"URL de petición: {url}")

        try:
            response = requests.get(url, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo en la conexión con PubChem para '{clean_name}': {e}")
            return None

        if response.status_code == 404:
            logger.warning(f"PubChem devolvió 404: No existe el compuesto '{clean_name}'. Verifica la extracción del PDF.")
            return None
            
        if response.status_code != 200:
            logger.error(f"Error {response.status_code} en PubChem para '{clean_name}'. Respuesta: {response.text}")
            return None

        data = response.json()
        properties = data.get("PropertyTable", {}).get("Properties", [])
        
        if not properties:
            logger.warning(f"PubChem no devolvió propiedades (SMILES/LogP) para '{clean_name}'.")
            return None

        first = properties[0]
        smiles = first.get("CanonicalSMILES")
        logp = first.get("XLogP")
        
        logger.success(f"Datos obtenidos de PubChem para '{clean_name}': SMILES={smiles} | LogP={logp}")

        return Agrotoxico(
            nombre_comun=clean_name,
            familia_quimica=familia_quimica,
            smiles=smiles,
            logP=logp,
            fuente_dato="PubChem PUG REST",
        )


def fetch_compound(nombre_comun: str, familia_quimica: str | None = None) -> Agrotoxico | None:
    return PubChemService().fetch_compound(nombre_comun, familia_quimica)