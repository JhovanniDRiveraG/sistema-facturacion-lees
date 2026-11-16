import httpx
from app.config import SERVIDORES, SERVIDOR_DEFAULT

 

async def get_requests(start_date: str, end_date: str, servidor: str = SERVIDOR_DEFAULT, limit: int = 1000):
    """
    Obtiene TODAS las solicitudes del período de un servidor específico.
    Con paginación automática si hay más de `limit`.
    """
    
    # Obtener config del servidor
    config = SERVIDORES.get(servidor)
    if not config:
        raise Exception(f"Servidor desconocido: {servidor}")
    
    url = config["url"]
    token = config["token"]
    
    if not url or not token:
        raise Exception(f"Servidor '{servidor}' sin URL o token configurado")
    
    all_requests = []
    offset = 1
    total_count = None
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            params = {
                "OrderByDirection": "asc",
                "OrderByField": "slaDeliveredTime",
                "ServiceWorkflowId": "",
                "accessionNumber": "",
                "clientserviceId": "",
                "endDate": end_date,
                "iaid": "",
                "limit": limit,
                "lockedby": "",
                "offset": offset,
                "patientname": "",
                "priority": 0,
                "startDate": start_date,
                "status": ""
            }
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.get(
                f"{url}/request/search/",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"[{servidor}] Error {response.status_code}: {response.text}")
            
            data = response.json()
            results = data.get("results", [])
            pagination = data.get("pagination", {})
            
            if total_count is None:
                total_count = pagination.get("totalCount", 0)
                print(f" [{servidor}] Total en el período: {total_count}")
            
            if not results:
                break
            
            all_requests.extend(results)
            print(f"   [{servidor}] Página {offset}: {len(results)} (acumulado: {len(all_requests)})")
            
            if len(all_requests) >= total_count:
                break
            
            offset += 1
    
    print(f" [{servidor}] Total traído: {len(all_requests)}")
    return all_requests

# para los valores
async def get_client_services(client_id: str, servidor: str = SERVIDOR_DEFAULT):
    """
    Obtiene el catálogo de servicios y precios de un cliente específico.
    """
    config = SERVIDORES.get(servidor)
    if not config:
        raise Exception(f"Servidor desconocido: {servidor}")
    
    url = config["url"]
    token = config["token"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Llamamos a la API que nos indicaste
        response = await client.get(
            f"{url}/client/{client_id}/Service/All",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Error obteniendo servicios: {response.status_code}")
            
        return response.json()