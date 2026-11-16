import React, { useState } from 'react';

import './App.css';

import { getPreview, exportarExcel, getClientes, getFacturacion, exportarTarifario } from './services/api';

function App() {
  // Obtener el primer y último día del mes anterior
  const hoy = new Date();
  const primerDiaMesPasado = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
  const ultimoDiaMesPasado = new Date(hoy.getFullYear(), hoy.getMonth(), 0);
  // Formatear a YYYY-MM-DD para los inputs
  const formatInputDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  const [startDate, setStartDate] = useState(formatInputDate(primerDiaMesPasado));
  const [endDate, setEndDate] = useState(formatInputDate(ultimoDiaMesPasado));


  const [filtro, setFiltro] = useState('todos');
  // ANTES: clienteSeleccionado guardaba el clientId
  // AHORA: guarda el NOMBRE del cliente
  const [clienteSeleccionado, setClienteSeleccionado] = useState('');
  const [clientes, setClientes] = useState([]);
  const [clienteMostrado, setClienteMostrado] = useState('');
  const [preview, setPreview] = useState(null);
  const [facturacion, setFacturacion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  // Ver vista previa + calcular facturación automáticamente
  const handlePreview = async () => {
    setCargando(true);
    setError(null);
    setFacturacion(null);

    try {
      if (clientes.length === 0) {
        const dataClientes = await getClientes(startDate, endDate);
        setClientes(dataClientes.clientes);
      }

      const data = await getPreview(startDate, endDate, filtro, clienteSeleccionado);
      setPreview(data);

      if (clienteSeleccionado) {
        setClienteMostrado(clienteSeleccionado);

        try {
          const fact = await getFacturacion(startDate, endDate, clienteSeleccionado);
          setFacturacion(fact);
        } catch (err) {
          console.warn('Sin facturación:', err.message);
        }
      } else {
        setClienteMostrado('');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  // Exportar Excel
  const handleExportar = async () => {
    setCargando(true);
    setError(null);
    try {
      const blob = await exportarExcel(startDate, endDate, filtro, clienteSeleccionado);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const clienteLimpio = clienteSeleccionado ? clienteSeleccionado.replace(/ /g, "_").replace(/\./g, "") : "Todos";
      link.download = `facturacion_${clienteLimpio}_${startDate}_${endDate}_${filtro}.xlsx`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  // Generar documento PDF
  const handleGenerarDocumento = () => {
    if (!clienteSeleccionado) {
      setError('Selecciona un cliente para generar el documento');
      return;
    }
    const url = `http://localhost:8000/documento?start=${startDate}&end=${endDate}&cliente=${encodeURIComponent(clienteSeleccionado)}`;
    window.open(url, '_blank');
  };

  // Generar el enlace de correo con la fecha calculada
  const handleEnviarCorreo = () => {
    if (!clienteSeleccionado || !endDate) {
      setError('Selecciona un cliente y un rango de fechas válido');
      return;
    }

    // 1. Calcular la fecha límite (+2 días a la fecha fin)
    const fechaFin = new Date(endDate + 'T00:00:00'); // Evitar problemas de zona horaria
    fechaFin.setDate(fechaFin.getDate() + 2);

    const dia = String(fechaFin.getDate()).padStart(2, '0');
    const mes = String(fechaFin.getMonth() + 1).padStart(2, '0');
    const anio = fechaFin.getFullYear();
    const fechaLimite = `${dia}/${mes}/${anio}`;

    // 2. Armar el asunto y el cuerpo del correo
    const asunto = encodeURIComponent(`Documentación de Facturación - ${clienteSeleccionado}`);
    
    const cuerpo = encodeURIComponent(
      `Buenos días equipo ${clienteSeleccionado}\n\n` +
      `Por solicitud se remite el PDF de documentación por Licencia de Software Telerradiologia.co. ` +
      `El documento PDF no es la factura emitida, necesitamos la confirmación para poder emitir la factura. ` +
      `No olvidar enviar su respuesta del documento PDF hasta la fecha ${fechaLimite}, caso contrario el área de Contabilidad tomará como aceptado y se le enviará la factura emitida por este medio. ` +
      `Cualquier duda estamos atentos.\n\n` +
      `Saludos,\nEquipo Telerradiología.co`
    );

    // 3. Abrir el cliente de correo
    // (Dejamos el destinatario vacío para que lo llenen manualmente)
    window.location.href = `mailto:?subject=${asunto}&body=${cuerpo}`;
  };


  const handleExportarTarifario = () => {
    if (!clienteSeleccionado) {
      setError('Selecciona un cliente para exportar su tarifario');
      return;
    }
    // Usamos la misma lógica del PDF
    const url = `http://localhost:8000/exportar-tarifario?start=${startDate}&end=${endDate}&cliente=${encodeURIComponent(clienteSeleccionado)}`;
    window.open(url, '_blank');
  };  

  

  return (
    <div className="app">
      <header className="header">
        <h1> Sistema de Facturación de Firmas</h1>
      </header>

      <main className="main">
        {/* Filtros */}
        <div className="filtros">
          <div className="filtro-grupo">
            <label>Fecha Inicio:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setFacturacion(null);
              }}
            />
          </div>

          <div className="filtro-grupo">
            <label>Fecha Fin:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setFacturacion(null);
              }}
            />
          </div>

          <div className="filtro-grupo">
            <label>Cliente:</label>
            <select
              value={clienteSeleccionado}
              onChange={(e) => {
                setClienteSeleccionado(e.target.value);
                setFacturacion(null);
              }}
            >
              <option value="">Todos los clientes</option>
              {clientes.map((c) => (
                <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
              ))}
            </select>
          </div>

          <div className="filtro-botones">
            <button onClick={handlePreview} disabled={cargando}>
              {cargando ? 'Cargando...' : ' Ver Datos'}
            </button>
            <button onClick={handleExportar} disabled={cargando} className="btn-exportar">
              {cargando ? 'Cargando...' : '⬇ Exportar Excel'}
            </button>
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        {/* Resumen */}
        {preview && preview.resumen && (
          <div className="resumen">
            <h2> Resumen</h2>
            <div className="tarjetas">
              <div className="tarjeta">
                <span className="numero">{preview.resumen.total}</span>
                <span className="label">Total</span>
              </div>
              <div className="tarjeta firmado">
                <span className="numero">{preview.resumen.firmados}</span>
                <span className="label"> Firmadas</span>
              </div>
              <div className="tarjeta no-firmado">
                <span className="numero">{preview.resumen.no_firmados}</span>
                <span className="label"> No Firmadas</span>
              </div>
              <div className="tarjeta mismo-mes">
                <span className="numero">{preview.resumen.a_tiempo}</span>
                <span className="label"> A Tiempo</span>
              </div>
              <div className="tarjeta otro-mes">
                <span className="numero">{preview.resumen.atrasados}</span>
                <span className="label"> Atrasadas</span>
              </div>
            </div>
          </div>
        )}

        {/* Tabla */}
        {preview && preview.datos && preview.datos.length > 0 && (
          <div className="tabla-container">
            <h2>
               Solicitudes ({preview.mostrando} de {preview.total})
              {clienteMostrado && (
                <span className="cliente-seleccionado"> - {clienteMostrado}</span>
              )}
            </h2>
            <div className="tabla-scroll">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Paciente</th>
                    <th>Procedimiento</th>
                    <th>Servicio</th>
                    <th>Modalidad</th>
                    <th>Estado</th>
                    <th>Firmado</th>
                    <th>Pendiente</th>
                    <th>SLA</th>
                    <th>Enviado</th>
                    <th>Firmado</th>
                    <th>Médico Firmante</th>
                    <th>Cliente</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.datos.map((item, index) => (
                    <tr key={index}>
                      <td>{item.paciente}</td>
                      <td>{item.procedimiento}</td>
                      <td>{item.servicio}</td>
                      <td>{item.modalidad}</td>
                      <td><span className="badge-estado">{item.estado}</span></td>
                      <td>
                        <span className={item.firmado === 'Sí' ? 'badge-si' : 'badge-no'}>
                          {item.firmado}
                        </span>
                      </td>
                      <td>
                        <span className={item.pendiente === 'Sí' ? 'badge-no' : 'badge-si'}>
                          {item.pendiente}
                        </span>
                      </td>
                      <td>
                        <span className={item.sla === 'A TIEMPO' ? 'badge-si' : 'badge-no'}>
                          {item.sla}
                        </span>
                      </td>
                      <td>{item.fecha_solicitud}</td>
                      <td>{item.fecha_firmado || '-'}</td>
                      <td>{item.medico_firmante || '-'}</td>
                      <td>{item.cliente}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {preview && preview.datos && preview.datos.length === 0 && (
          <div className="sin-datos">
             No hay solicitudes en el período seleccionado
          </div>
        )}

        {/* Total + Botón Generar Documento */}
        {facturacion && (
          <div className="total-cliente">
            <div className="total-info">
              <h2> Total a pagar: {facturacion.cliente}</h2>
              <p className="periodo-total"> Período: {facturacion.periodo}</p>
              <div className="total-monto">
                S/ {facturacion.total.toFixed(2)}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button onClick={handleGenerarDocumento} className="btn-documento">
                 Generar Documento
              </button>
              <button onClick={handleEnviarCorreo} className="btn-documento btn-correo">
                 Enviar Correo
              </button>
              {/* BOTÓN CONDICIONAL */}
              {clienteSeleccionado && clienteSeleccionado.toUpperCase().includes('CHOTA') && (
              <button onClick={handleExportarTarifario} className="btn-documento btn-chota">
                Exportar Tarifario
              </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
  
}

export default App;