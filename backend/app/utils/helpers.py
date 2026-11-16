from datetime import datetime


def get_invoice_status(request):
    """Determina estado de facturación (solo para filtros)"""
    is_signed = request.get("validated") is not None

    if not is_signed:
        return "no_firmado"

    signature_date = request.get("validatedAt")
    created_date = request.get("createdAt")

    if not signature_date or not created_date:
        return "firmado_sin_fecha"

    try:
        sig_date = datetime.fromisoformat(signature_date.replace("Z", "+00:00"))
        cre_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
    except:
        return "firmado_otro_mes"

    if sig_date.month == cre_date.month:
        return "firmado_mismo_mes"
    else:
        return "firmado_otro_mes"


def get_sla_status(request):
    """
    Determina el estado del SLA
    - A TIEMPO: si slaDifferenceTime es positivo o cero
    - ATRASADO: si slaDifferenceTime es negativo
    - SIN SLA: si no hay datos
    """
    diff = request.get("slaDifferenceTime", "")

    if not diff:
        return "SIN SLA"

    if diff.startswith("-"):
        return "ATRASADO"
    else:
        return "A TIEMPO"


def format_date(date_str):
    """Formatea una fecha para mostrarla"""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str


def filter_requests(requests, filter_type):
    """Filtra solicitudes por tipo de facturación"""
    if filter_type == "todos":
        return requests

    filtered = []
    for req in requests:
        status = get_invoice_status(req)

        if filter_type == "firmado_mismo_mes" and status == "firmado_mismo_mes":
            filtered.append(req)
        elif filter_type == "firmado_otro_mes" and status == "firmado_otro_mes":
            filtered.append(req)
        elif filter_type == "no_firmado" and status == "no_firmado":
            filtered.append(req)

    return filtered


def filter_by_client_id(requests, client_id):
    """Filtra solicitudes por clientId (si está vacío, devuelve todo)"""
    if not client_id:
        return requests

    filtered = []
    for req in requests:
        if req.get("clientId") == client_id:
            filtered.append(req)

    return filtered


def get_client_name(req):
    """Obtiene el nombre del cliente de una solicitud"""
    if req.get("client"):
        return req["client"].get("fantasyName", "") or req["client"].get("companyName", "")
    return ""


def extract_clientes(requests):
    """Extrae la lista única de clientes (id + nombre) de una lista de solicitudes"""
    clientes_dict = {}
    for req in requests:
        client_id = req.get("clientId")
        client_info = req.get("client", {})
        nombre = client_info.get("fantasyName", "") or client_info.get("companyName", "")

        if client_id and nombre:
            clientes_dict[client_id] = nombre

    clientes = [
        {"id": cid, "nombre": nombre}
        for cid, nombre in sorted(clientes_dict.items(), key=lambda x: x[1])
    ]

    return clientes