import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# MAPA DE SERVIDORES
# ============================================
SERVIDORES = {
    "lees": {
        "nombre": "LEES",
        "url": os.getenv("LEES_API_URL"),
        "token": os.getenv("LEES_API_TOKEN"),
    },
    "primavera_chimbote": {
        "nombre": "Primavera - Chimbote",
        "url": os.getenv("PRIMAVERA_CHIMBOTE_API_URL"),
        "token": os.getenv("PRIMAVERA_CHIMBOTE_API_TOKEN"),
    },
    "primavera_trujillo": {
        "nombre": "Primavera - Trujillo",
        "url": os.getenv("PRIMAVERA_TRUJILLO_API_URL"),
        "token": os.getenv("PRIMAVERA_TRUJILLO_API_TOKEN"),
    },
}

# Servidor por defecto (si no se especifica otro)
SERVIDOR_DEFAULT = "lees"

# Compatibilidad con código existente
LEES_API_URL = SERVIDORES["lees"]["url"]
TOKEN = SERVIDORES["lees"]["token"]


def get_servidor(nombre):
    """Devuelve la config de un servidor por nombre"""
    return SERVIDORES.get(nombre)


def listar_servidores():
    """Devuelve la lista de nombres de servidores disponibles"""
    return list(SERVIDORES.keys())