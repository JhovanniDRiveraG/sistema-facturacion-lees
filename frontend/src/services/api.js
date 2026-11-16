const API_BASE_URL = 'http://localhost:8000';

// Obtener lista de clientes del período (id + nombre + servidor)
export const getClientes = async (start, end) => {
  const response = await fetch(
    `${API_BASE_URL}/clientes?start=${start}&end=${end}`
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al obtener clientes');
  }
  return response.json();
};

// Obtener vista previa (JSON)
// ANTES: enviaba client_id
// AHORA: envía cliente (nombre)
export const getPreview = async (start, end, filtro = 'todos', cliente = '') => {
  const params = new URLSearchParams({ start, end, filtro });

  if (cliente) params.append('cliente', cliente);

  const response = await fetch(`${API_BASE_URL}/preview?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al obtener vista previa');
  }
  return response.json();
};

// Exportar Excel
// ANTES: enviaba client_id
// AHORA: envía cliente (nombre)
export const exportarExcel = async (start, end, filtro, cliente = '') => {
  const params = new URLSearchParams({ start, end, filtro });

  if (cliente) params.append('cliente', cliente);

  const response = await fetch(`${API_BASE_URL}/exportar?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al exportar');
  }
  return response.blob();
};

// Calcular facturación de un cliente
// ANTES: enviaba client_id
// AHORA: envía cliente (nombre)
export const getFacturacion = async (start, end, cliente) => {
  const params = new URLSearchParams({
    start,
    end,
    cliente
  });
  const response = await fetch(`${API_BASE_URL}/facturar?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al calcular facturación');
  }
  return response.json();
};

// Obtener clientes con tarifas configuradas
export const getClientesConTarifas = async () => {
  const response = await fetch(`${API_BASE_URL}/clientes-con-tarifas`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al obtener clientes con tarifas');
  }
  return response.json();
};



export const exportarTarifario = async (start, end, cliente) => {
  const params = new URLSearchParams({ start, end, cliente });
  const response = await fetch(`${API_BASE_URL}/exportar-tarifario?${params}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error al exportar tarifario');
  }
  return response.blob();
};