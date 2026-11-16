from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.config import TOKEN, SERVIDORES
from app.services.telerradiologia_client import get_requests, get_client_services
from app.services.excel_service import generate_excel, generate_excel_tarifario 
from app.services.facturacion_service import calcular_facturacion
from app.services.documento_service import generar_pdf
from app.config.tarifas.loader import (
    listar_clientes_con_tarifas,
    get_servidor_de_cliente
)
from app.utils.helpers import (
    filter_requests,
    get_invoice_status,
    get_sla_status,
    format_date,
    get_client_name,
    extract_clientes
)

from app.services.excel_service import generate_excel

router = APIRouter()


# ============================================
# HELPERS
# ============================================
async def obtener_requests_de_cliente(start, end, cliente=""):
    """
    Obtiene solicitudes del servidor correcto.
    Si el cliente está vacío, consulta TODOS los servidores y une los resultados.
    """
    if not cliente:
        # Si es "Todos", consultar los 3 servidores
        todos_los_requests = []
        for servidor_nombre in SERVIDORES.keys():
            try:
                requests = await get_requests(start, end, servidor=servidor_nombre)
                todos_los_requests.extend(requests)
            except Exception as e:
                print(f"Error consultando {servidor_nombre} (Todos): {str(e)}")
                continue
        return todos_los_requests
    else:
        # Si es un cliente específico, consultar solo su servidor
        servidor = get_servidor_de_cliente(cliente)
        return await get_requests(start, end, servidor=servidor)


def filtrar_por_cliente(requests, cliente):
    """Filtra solicitudes por NOMBRE de cliente"""
    if not cliente:
        return requests
    return [r for r in requests if get_client_name(r) == cliente]


# ============================================
# ENDPOINTS
# ============================================
@router.get("/")
async def root():
    return {
        "mensaje": "Sistema de Facturación de Firmas",
        "version": "1.0",
        "servidores": list(SERVIDORES.keys()),
        "endpoints": {
            "estadisticas": "/estadisticas?start=YYYY-MM-DD&end=YYYY-MM-DD",
            "exportar": "/exportar?start=YYYY-MM-DD&end=YYYY-MM-DD&filtro=todos&cliente=",
            "preview": "/preview?start=YYYY-MM-DD&end=YYYY-MM-DD&filtro=todos&cliente=",
            "clientes": "/clientes?start=YYYY-MM-DD&end=YYYY-MM-DD",
            "facturar": "/facturar?start=YYYY-MM-DD&end=YYYY-MM-DD&cliente=",
            "documento": "/documento?start=YYYY-MM-DD&end=YYYY-MM-DD&cliente=",
            "clientes_con_tarifas": "/clientes-con-tarifas"
        }
    }


@router.get("/servidores")
async def listar_servidores():
    return {
        "servidores": [
            {"id": key, "nombre": val["nombre"]}
            for key, val in SERVIDORES.items()
        ]
    }


@router.get("/estadisticas")
async def estadisticas(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    cliente: str = Query("", description="Filtro por nombre de cliente")
):
    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        return {"mensaje": "No hay solicitudes en el período"}

    total = len(requests)
    firmados = sum(1 for r in requests if r.get("validated") is not None)
    no_firmados = total - firmados
    mismo_mes = sum(1 for r in requests if get_invoice_status(r) == "firmado_mismo_mes")
    otro_mes = sum(1 for r in requests if get_invoice_status(r) == "firmado_otro_mes")

    return {
        "periodo": f"{start} → {end}",
        "total": total,
        "firmados": firmados,
        "no_firmados": no_firmados,
        "firmados_mismo_mes": mismo_mes,
        "firmados_otro_mes": otro_mes,
        "porcentaje_firmados": f"{(firmados/total*100):.1f}%" if total > 0 else "0%"
    }


@router.get("/clientes")
async def get_clientes(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD")
):
    """
    Devuelve la lista única de clientes del período.
    CONSULTA TODOS LOS SERVIDORES y une los resultados.
    """
    todos_clientes = {}

    for servidor_nombre in SERVIDORES.keys():
        try:
            requests = await get_requests(start, end, servidor=servidor_nombre)

            for req in requests:
                client_id = req.get("clientId")
                client_info = req.get("client", {})
                nombre = client_info.get("fantasyName", "") or client_info.get("companyName", "")

                if client_id and nombre:
                    # Usar el nombre como clave para evitar duplicados por clientId
                    todos_clientes[nombre] = {
                        "id": client_id,
                        "nombre": nombre,
                        "servidor": servidor_nombre
                    }
        except Exception as e:
            print(f"⚠️ Error consultando {servidor_nombre}: {str(e)}")
            continue

    clientes = sorted(todos_clientes.values(), key=lambda x: x["nombre"])

    return {
        "clientes": clientes,
        "total": len(clientes)
    }


@router.get("/clientes-con-tarifas")
async def clientes_con_tarifas():
    return {"clientes": listar_clientes_con_tarifas()}


@router.get("/exportar")
async def exportar(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    filtro: str = Query("todos", description="todos | firmado_mismo_mes | firmado_otro_mes | no_firmado"),
    cliente: str = Query("", description="Filtrar por nombre de cliente (vacío = todos)")
):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM-DD")

    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        raise HTTPException(404, "No se encontraron solicitudes")

    filtered = filter_requests(requests, filtro)
    filtered = filtrar_por_cliente(filtered, cliente)

    # NUEVO: Excluir estados específicos (como STATUS.UNCATEGORIZED) para este cliente
    #from app.config.tarifas.loader import cargar_tarifas_por_nombre
    #tarifas = cargar_tarifas_por_nombre(cliente)
    #if tarifas and "estados_excluidos" in tarifas:
    #    estados_excluidos = tarifas["estados_excluidos"]
    #    filtered = [
    #        req for req in filtered 
    #        if req.get("requestStatus", {}).get("name") not in estados_excluidos
    #    ]

    if not filtered:
        raise HTTPException(404, "No hay solicitudes con los filtros aplicados")

    filtered.sort(key=lambda x: x.get("createdAt", ""))

    excel = generate_excel(filtered)
    # Limpiamos el nombre del cliente para que no tenga espacios ni caracteres raros
    cliente_limpio = cliente.replace(" ", "_").replace(".", "").replace(",", "") if cliente else "Todos"
    filename = f"facturacion_{cliente_limpio}_{start}_{end}_{filtro}.xlsx"

    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/preview")
async def preview(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    filtro: str = Query("todos", description="todos | firmado_mismo_mes | firmado_otro_mes | no_firmado"),
    cliente: str = Query("", description="Filtrar por nombre de cliente (vacío = todos)")
):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM-DD")

    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        return {"total": 0, "mostrando": 0, "datos": [], "resumen": {}}

    # Filtrar por estado de facturación Y por cliente
    filtered = filter_requests(requests, filtro)
    filtered = filtrar_por_cliente(filtered, cliente)

    # NUEVO: Excluir estados específicos (como STATUS.UNCATEGORIZED) para este cliente
    #from app.config.tarifas.loader import cargar_tarifas_por_nombre
    #tarifas = cargar_tarifas_por_nombre(cliente)
    #if tarifas and "estados_excluidos" in tarifas:
    #    estados_excluidos = tarifas["estados_excluidos"]
    #    filtered = [
    #        req for req in filtered 
    #        if req.get("requestStatus", {}).get("name") not in estados_excluidos
    #    ]

    items = []
    for req in filtered:
        signer_name = ""
        if req.get("validated"):
            signer_name = req["validated"].get("name", "")

        client_name = get_client_name(req)

        # NUEVO: Extraer el nombre del servicio
        servicio_desc = ""
        if req.get("clientService") and req["clientService"].get("service"):
            servicio_desc = req["clientService"]["service"].get("description", "")

        items.append({
            "paciente": req.get("patientName", ""),
            "procedimiento": req.get("procedureName", ""),
            "servicio": servicio_desc,
            "modalidad": req.get("modalityName", ""),
            "estado": req.get("requestStatus", {}).get("name", ""),
            "firmado": "Sí" if req.get("validated") else "No",
            "pendiente": "No" if req.get("validated") else "Sí",
            "sla": get_sla_status(req),
            "fecha_solicitud": format_date(req.get("createdAt")),
            "fecha_firmado": format_date(req.get("validatedAt")),
            "medico_firmante": signer_name,
            "cliente": client_name
        })

    total_filtrado = len(filtered)
    firmados = sum(1 for r in filtered if r.get("validated") is not None)
    no_firmados = total_filtrado - firmados
    mismo_mes = sum(1 for r in filtered if get_invoice_status(r) == "firmado_mismo_mes")
    otro_mes = sum(1 for r in filtered if get_invoice_status(r) == "firmado_otro_mes")
    a_tiempo = sum(1 for r in filtered if get_sla_status(r) == "A TIEMPO")
    atrasados = sum(1 for r in filtered if get_sla_status(r) == "ATRASADO")

    return {
        "total": len(requests),
        "mostrando": len(items),
        "datos": items,
        "resumen": {
            "total": total_filtrado,
            "firmados": firmados,
            "no_firmados": no_firmados,
            "firmados_mismo_mes": mismo_mes,
            "firmados_otro_mes": otro_mes,
            "a_tiempo": a_tiempo,
            "atrasados": atrasados,
            "porcentaje_firmados": f"{(firmados/total_filtrado*100):.1f}%" if total_filtrado > 0 else "0%"
        }
    }


@router.get("/facturar")
async def facturar(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    cliente: str = Query(..., description="Nombre del cliente")
):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM-DD")

    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        raise HTTPException(404, "No se encontraron solicitudes")

    resultado = calcular_facturacion(requests, cliente)

    if "error" in resultado:
        raise HTTPException(400, resultado["error"])

    resultado["periodo"] = f"{start} → {end}"
    return resultado


@router.get("/documento")
async def documento(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    cliente: str = Query(..., description="Nombre del cliente")
):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM-DD")

    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        raise HTTPException(404, "No se encontraron solicitudes")

    facturacion = calcular_facturacion(requests, cliente)

    if "error" in facturacion:
        raise HTTPException(400, facturacion["error"])

    try:
        pdf_bytes = generar_pdf(facturacion, start, end)
    except Exception as e:
        raise HTTPException(500, f"Error al generar PDF: {str(e)}")

    nombre_cliente = facturacion["cliente"].replace(" ", "_")
    filename = f"reporte_{nombre_cliente}_{start}_{end}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/exportar-tarifario")
async def exportar_tarifario(
    start: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    cliente: str = Query(..., description="Nombre del cliente")
):
    """Exporta el Excel con los valores calculados según el tarifario del cliente"""
    
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except:
        raise HTTPException(400, "Formato inválido. Use YYYY-MM-DD")

    try:
        requests = await obtener_requests_de_cliente(start, end, cliente)
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

    if not requests:
        raise HTTPException(404, "No se encontraron solicitudes")

    filtered = filtrar_por_cliente(requests, cliente)

    if not filtered:
        raise HTTPException(404, "No hay solicitudes para este cliente")

    try:
        # Ahora le pasamos el nombre del cliente a la función
        excel = generate_excel_tarifario(filtered, cliente) 
    except Exception as e:
        raise HTTPException(500, f"Error al generar Excel: {str(e)}")

    filename = f"valores_{cliente.replace(' ', '_')}_{start}_{end}.xlsx"

    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )