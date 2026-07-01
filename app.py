import requests

""" Datos a Extraer del(de los) artículo(s)
La herramienta debe identificar y extraer la siguiente información de cada artículo y
enriquecerla con bases de datos externas:
● DOI
Introducción a la Bioinformática Prof. Ana Julia Velez Rueda
● Título
● Autores
● Año de Publicación
● Revista
● B. Proteína del Organismo Modelo:
● Nombre de la proteína (ej. "Proteína quimiosensorial de Apis mellifera").
● Organismo (nombre científico, ej. Apis mellifera o Danio rerio).
● ID de UniProt (obtenido automáticamente por consulta a la API de UniProt usando el
nombre de la proteína y el organismo).
● Código PDB (si se menciona una estructura 3D en el artículo o si existe en PDB).
● Función biológica (extraída de UniProt mediante la API).
● C. Agrotóxico(s) Investigado(s):
● Nombre común (ej. Imidacloprid, Atrazina).
● Familia Química (ej. Neonicotinoide, Triazina).
● SMILES (obtenido automáticamente de PubChem mediante la API PUG REST).
● LogP (coeficiente de partición, obtenido de PubChem).
● Tipo de Afinidad: (Kd, Ki, IC50, etc., si están reportados en el texto).
● Valor y Unidad: (ej. 2.5 µM).
● Método experimental (ej. "ITC", "Fluorescencia", "Docking").
● Fuente del Dato: Texto del artículo, API de BindingDB o ChEMBL.
"""

doi = "10.1042/bj3180001"
url = f"https://api.crossref.org/works/{doi}"

class Articulo:
    def __init__(self, doi):
        self.doi = doi
        self.titulo = None
        self.autores = []
        self.año = None
        self.revista = None

    def toJson(self):
        return {
            "DOI": self.doi,
            "Título": self.titulo,
            "Autores": self.autores,
            "Año de Publicacion": self.año,
            "Revista": self.revista
        }

class ProteinaOrganizmoModelo:
    def __init__(self, nombre_proteina, organismo, uniprot_id=None, pdb_code=None, funcion_biologica=None):
        self.nombre_proteina = nombre_proteina
        self.organismo = organismo
        self.uniprot_id = uniprot_id
        self.pdb_code = pdb_code
        self.funcion_biologica = funcion_biologica

class Agrotóxico:
    def __init__(self, nombre_comun, familia_quimica, smiles=None, logP=None, tipo_afinidad=None, valor_unidad=None, metodo_experimental=None, fuente_dato=None):
        self.nombre_comun = nombre_comun
        self.familia_quimica = familia_quimica
        self.smiles = smiles
        self.logP = logP
        self.tipo_afinidad = tipo_afinidad
        self.valor_unidad = valor_unidad
        self.metodo_experimental = metodo_experimental
        self.fuente_dato = fuente_dato

def fetch_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        articulo = Articulo(doi)
        
        # Navegando el JSON para sacar los datos que te pide el TP:
        articulo.titulo = data['message']['title'][0]
        articulo.revista = data['message']['container-title'][0]
        
        # El año de publicación puede estar en 'published-print' o 'published-online'
        if 'published-print' in data['message']:
            articulo.año = data['message']['published-print']['date-parts'][0][0]
        elif 'published-online' in data['message']:
            articulo.año = data['message']['published-online']['date-parts'][0][0]

        for autor in data['message']['author']:
            nombre = autor.get('given', '')
            apellido = autor.get('family', '')
            articulo.autores.append(f"{nombre} {apellido}")
        
        return articulo
    else:
        print(f"Error al obtener datos para DOI {doi}: {response.status_code}")
        return None

if __name__ == "__main__":
    articulo = fetch_doi(doi)
    if articulo:
        print(articulo.toJson())