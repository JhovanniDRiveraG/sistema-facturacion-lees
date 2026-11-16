from app.config.tarifas.loader import cargar_tarifas_por_nombre
from app.utils.helpers import get_client_name


def calcular_facturacion(solicitudes, nombre_cliente):
    """
    Calcula el TOTAL a facturar automáticamente.
    Ahora recibe el NOMBRE del cliente (no el clientId).
    """
    # ANTES: tarifas = cargar_tarifas_por_id(client_id)
    tarifas = cargar_tarifas_por_nombre(nombre_cliente)

    if not tarifas:
        return {
            "error": f"No hay tarifas configuradas para el cliente '{nombre_cliente}'",
            "cliente": nombre_cliente,
            "total": 0
        }

    tipo_cobro = tarifas.get("tipo_cobro", "por_rango")
    cuenta_cancelados = tarifas.get("cuenta_cancelados", True)

    # NUEVO: Contar cuántos cancelados hay en total (antes de filtrar)
    cancelados = sum(
        1 for req in solicitudes 
        if get_client_name(req) == nombre_cliente 
        and req.get("requestStatus", {}).get("name") == "STATUS.CANCELED"
    )

    # Filtrar solicitudes del cliente por NOMBRE
    # NUEVO: Obtener los estados que no se deben contar (si los hay)
    solicitudes_cliente = [
        req for req in solicitudes
        if get_client_name(req) == nombre_cliente
        and (cuenta_cancelados or req.get("requestStatus", {}).get("name") != "STATUS.CANCELED")
    ]

    # Ordenar por fecha de creación
    solicitudes_cliente.sort(key=lambda x: x.get("createdAt", ""))

    # Calcular según tipo
    if tipo_cobro == "por_umbral":
        detalle = calcular_umbral(solicitudes_cliente, tarifas)
    elif tipo_cobro == "por_productividad":
        detalle = calcular_productividad(solicitudes_cliente, tarifas)
    elif tipo_cobro == "por_rango_unitario":
        detalle = calcular_rango_unitario(solicitudes_cliente, tarifas)
    elif tipo_cobro == "personalizado":  # <-- NUEVO condicion espcial
        detalle = calcular_personalizado(solicitudes_cliente, tarifas)

    else:
        detalle = calcular_rango(solicitudes_cliente, tarifas)

    total = sum(item["subtotal"] for item in detalle.values())

    return {
        "cliente": tarifas.get("cliente", nombre_cliente),
        "tipo_cobro": tipo_cobro,
        "total_solicitudes": len(solicitudes_cliente),
        "detalle": detalle,
        "total": round(total, 2),
        "total_cancelados": cancelados,
        "moneda": "PEN"
    }


def calcular_umbral(solicitudes_cliente, tarifas):
    """Cálculo para clientes por_umbral"""
    detalle = {}

    for nombre, config in tarifas["grupos"].items():
        modalidades = [m.upper() for m in config["modalidades"]]

        solicitudes_grupo = [
            req for req in solicitudes_cliente
            if req.get("modalityName", "").upper() in modalidades
        ]

        cantidad = len(solicitudes_grupo)

        if cantidad == 0:
            subtotal = 0
            modo = "sin_cobro"
        elif cantidad <= config["limite"]:
            subtotal = config["valor_mensual"]
            modo = "umbral"
        else:
            subtotal = cantidad * config["precio_unitario"]
            modo = "unidad"

        detalle[nombre] = {
            "descripcion": config["descripcion"],
            "modalidades": config["modalidades"],
            "cantidad": cantidad,
            "limite": config["limite"],
            "valor_mensual": config["valor_mensual"],
            "precio_unitario": config["precio_unitario"],
            "modo": modo,
            "subtotal": round(subtotal, 2),
            "solicitudes": solicitudes_grupo,
            "tipo": "umbral"
        }

    return detalle


def calcular_productividad(solicitudes_cliente, tarifas):
    """
    Cálculo para clientes por_productividad.
    Siempre: cantidad × precio_unitario (sin mínimo, sin límite).
    """
    detalle = {}

    for nombre, config in tarifas["grupos"].items():
        modalidades = [m.upper() for m in config["modalidades"]]

        solicitudes_grupo = [
            req for req in solicitudes_cliente
            if req.get("modalityName", "").upper() in modalidades
        ]

        cantidad = len(solicitudes_grupo)
        precio_unitario = config["precio_unitario"]
        subtotal = cantidad * precio_unitario

        detalle[nombre] = {
            "descripcion": config["descripcion"],
            "modalidades": config["modalidades"],
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": round(subtotal, 2),
            "solicitudes": solicitudes_grupo,
            "tipo": "productividad"
        }

    return detalle


def calcular_rango(solicitudes_cliente, tarifas):
    """Cálculo para clientes por_rango (Cristo Redentor)"""
    detalle = {}

    for nombre, config in tarifas["tablas"].items():
        modalidades = [m.upper() for m in config["modalidades"]]

        solicitudes_tabla = [
            req for req in solicitudes_cliente
            if req.get("modalityName", "").upper() in modalidades
        ]

        cantidad = len(solicitudes_tabla)

        if cantidad == 0:
            detalle[nombre] = {
                "descripcion": config["descripcion"],
                "modalidades": config["modalidades"],
                "cantidad": 0,
                "rango": "-",
                "valor_unitario": 0,
                "subtotal": 0,
                "solicitudes": [],
                "tipo": "rango"
            }
            continue

        rango_aplicado = None
        for rango in config["rangos"]:
            if rango["min"] <= cantidad <= rango["max"]:
                rango_aplicado = rango
                break

        if rango_aplicado:
            subtotal = rango_aplicado["valor"]
            rango_nombre = rango_aplicado["nombre"]
            unitario = rango_aplicado["unitario"]
        else:
            ultimo = config["rangos"][-1]
            subtotal = cantidad * ultimo["unitario"]
            rango_nombre = f"{ultimo['nombre']}+"
            unitario = ultimo["unitario"]

        detalle[nombre] = {
            "descripcion": config["descripcion"],
            "modalidades": config["modalidades"],
            "cantidad": cantidad,
            "rango": rango_nombre,
            "valor_unitario": unitario,
            "subtotal": round(subtotal, 2),
            "solicitudes": solicitudes_tabla,
            "tipo": "rango"
        }

    return detalle

def calcular_rango_unitario(solicitudes_cliente, tarifas):
    """
    Cálculo para clientes con rangos de precio unitario.
    Siempre se cobra: cantidad * unitario del rango en el que cae.
    """
    detalle = {}

    for nombre, config in tarifas["grupos"].items():
        modalidades = [m.upper() for m in config["modalidades"]]

        solicitudes_grupo = [
            req for req in solicitudes_cliente
            if req.get("modalityName", "").upper() in modalidades
        ]

        cantidad = len(solicitudes_grupo)

        if cantidad == 0:
            detalle[nombre] = {
                "descripcion": config["descripcion"],
                "modalidades": config["modalidades"],
                "cantidad": 0,
                "rango": "-",
                "precio_unitario": 0,
                "subtotal": 0,
                "solicitudes": [],
                "tipo": "rango_unitario"
            }
            continue

        # Buscar rango aplicable
        rango_aplicado = config["rangos"][0] # Por defecto el primero
        for rango in config["rangos"]:
            if rango["min"] <= cantidad <= rango["max"]:
                rango_aplicado = rango
                break

        precio_unitario = rango_aplicado["unitario"]
        subtotal = cantidad * precio_unitario

        detalle[nombre] = {
            "descripcion": config["descripcion"],
            "modalidades": config["modalidades"],
            "cantidad": cantidad,
            "rango": rango_aplicado["nombre"],
            "precio_unitario": precio_unitario,
            "subtotal": round(subtotal, 2),
            "solicitudes": solicitudes_grupo,
            "tipo": "rango_unitario"
        }

    return detalle


def calcular_personalizado(solicitudes_cliente, tarifas):
    """
    Lógica especial:
    - Si la cantidad es menor o igual al límite especial, se cobra el monto especial (Mínimo).
    - Si pasa el límite, se aplica la tabla de rangos. Si está entre el límite y el mínimo del rango, 
      se cobra el mínimo del rango (ej. 16 a 30 se cobra como 30).
    """
    detalle = {}

    for nombre, config in tarifas["grupos"].items():
        modalidades = [m.upper() for m in config["modalidades"]]
        
        solicitudes_grupo = [
            req for req in solicitudes_cliente
            if req.get("modalityName", "").upper() in modalidades
        ]
        
        cantidad = len(solicitudes_grupo)
        limite_especial = config["limite_especial"]
        
        # 1. Si no hay exámenes, se cobra 0
        if cantidad == 0:
            subtotal = 0
            modo = "sin_cobro"
            rango_nombre = "-"
            unitario = 0
            
        # 2. Si está dentro del límite de la condición especial (Mínimo)
        elif cantidad <= limite_especial:
            subtotal = config["monto_especial"]
            modo = "especial"
            rango_nombre = f"Cond. Especial (Mínimo {limite_especial})"
            unitario = 0
            
        # 3. Si supera el límite, se aplican los rangos (con la regla del salto)
        else:
            rango_aplicado = config["rangos"][-1]
            for rango in config["rangos"]:
                if rango["min"] <= cantidad <= rango["max"]:
                    rango_aplicado = rango
                    break
            
            unitario = rango_aplicado["unitario"]
            rango_nombre = rango_aplicado["nombre"]
            
            # --- REGLA DEL SALTO (Para el primer rango) ---
            # Si el rango es el primero (ej. Rango 1) y la cantidad es menor al tope de ese bloque,
            # forzamos a que se cobre el tope del bloque completo.
            if rango_nombre == "Rango 1":
                if "Mamografía" in config["descripcion"]:
                    cantidad_a_cobrar = max(cantidad, 30) # Bloque completo de 30
                else:
                    cantidad_a_cobrar = max(cantidad, 300) # Bloque completo de 300
            else:
                cantidad_a_cobrar = cantidad
                
            subtotal = cantidad_a_cobrar * unitario
            modo = "rango"

        detalle[nombre] = {
            "descripcion": config["descripcion"],
            "modalidades": config["modalidades"],
            "cantidad": cantidad,
            "rango": rango_nombre,
            "valor_unitario": unitario,
            "modo": modo,
            "subtotal": round(subtotal, 2),
            "solicitudes": solicitudes_grupo,
            "tipo": "personalizado"
        }

    return detalle