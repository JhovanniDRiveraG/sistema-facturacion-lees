import json
import os
from app.config import SERVIDOR_DEFAULT


TARIFAS_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================
# MAPA: Nombre del cliente → archivo de tarifas
# ============================================
# NOTA: Antes se usaba clientId, pero como hay clientes
# con el mismo clientId en diferentes servidores
# (ej: Salud Primavera Chimbote y Trujillo),
# se cambió a usar el NOMBRE del cliente que es único.
#
# CÓDIGO ANTERIOR (por clientId):
# --------------------------------------------
# CLIENTES_TARIFAS = {
#     "08dc8176-3253-4a75-828a-9962c1ab6cef": "cristo_redentor.json",
#     "08da47c3-72de-41ac-8ca1-fea6a8253573": "clinica_trujillo_chota.json",
#     "08de0a6d-cb23-4f8e-8554-5be914a91f37": "climper.json",
#     "08d9a3d2-4ece-fad6-d56a-f651c8651e24": "salud_primavera_chimbote.json",
# }
# --------------------------------------------

CLIENTES_TARIFAS = {
    # LEES
    "CLINICA CRISTO REDENTOR TRUJILLO": "cristo_redentor.json",
    "C. TRUJILLO CHOTA": "clinica_trujillo_chota.json",
    "CLIMPER EIRL": "climper.json",
    "Telerradiomed": "telerradiomed.json", 
    "Policlinico Miraflores RX": "policlinico_miraflores.json",
    "INKAMAY RONTGEN": "inkamay.json",
    
    # Primavera-Chimbote
    "Salud Primavera Chimbote": "salud_primavera_chimbote.json",
    
    # Primavera-Trujillo
    "SALUD PRIMAVERA TRUJILLO": "salud_primavera_trujillo.json",
    "SOLUCIONES INTEGRALES DE SALUD S.A.C.": "soinsa.json",
}


# ============================================
# MAPA: Nombre del cliente → servidor
# ============================================
# CÓDIGO ANTERIOR (por clientId):
# --------------------------------------------
# CLIENTES_SERVIDORES = {
#     "08dc8176-3253-4a75-828a-9962c1ab6cef": "lees",
#     "08da47c3-72de-41ac-8ca1-fea6a8253573": "lees",
#     "08de0a6d-cb23-4f8e-8554-5be914a91f37": "lees",
#     "08d9a3d2-4ece-fad6-d56a-f651c8651e24": "primavera_chimbote",
#     "08da081c-41af-4bba-8bdf-635d84378454": "primavera_trujillo",
# }
# --------------------------------------------

CLIENTES_SERVIDORES = {
    # LEES
    "CLINICA CRISTO REDENTOR TRUJILLO": "lees",
    "C. TRUJILLO CHOTA": "lees",
    "CLIMPER EIRL": "lees",
    "Telerradiomed": "lees",
    "Policlinico Miraflores RX": "lees",
    "INKAMAY RONTGEN": "lees",
    
    # Primavera-Chimbote
    "Salud Primavera Chimbote": "primavera_chimbote",
    
    # Primavera-Trujillo
    "SALUD PRIMAVERA TRUJILLO": "primavera_trujillo",
    "SOLUCIONES INTEGRALES DE SALUD S.A.C.": "primavera_trujillo",
}


def cargar_tarifas_por_nombre(nombre_cliente):
    """Carga el archivo de tarifas de un cliente por su NOMBRE"""
    if not nombre_cliente:
        return None
    if nombre_cliente not in CLIENTES_TARIFAS:
        return None
    archivo = CLIENTES_TARIFAS[nombre_cliente]
    ruta = os.path.join(TARIFAS_DIR, archivo)
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================
# FUNCIÓN ANTERIOR (por clientId) - COMENTADA
# ============================================
# def cargar_tarifas_por_id(client_id):
#     if not client_id:
#         return None
#     if client_id not in CLIENTES_TARIFAS:
#         return None
#     archivo = CLIENTES_TARIFAS[client_id]
#     ruta = os.path.join(TARIFAS_DIR, archivo)
#     if not os.path.exists(ruta):
#         return None
#     with open(ruta, 'r', encoding='utf-8') as f:
#         return json.load(f)


def get_servidor_de_cliente(nombre_cliente):
    """Devuelve el servidor al que pertenece un cliente por su NOMBRE"""
    if not nombre_cliente:
        return SERVIDOR_DEFAULT
    return CLIENTES_SERVIDORES.get(nombre_cliente, SERVIDOR_DEFAULT)


def listar_clientes_con_tarifas():
    """Devuelve la lista de nombres de clientes que tienen tarifas configuradas"""
    return list(CLIENTES_TARIFAS.keys())