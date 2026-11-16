import os
from datetime import datetime
from fpdf import FPDF

# ============================================
# RUTAS DE LAS IMÁGENES
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

HEADER_IMG = os.path.join(STATIC_DIR, 'header.png')
FOOTER_IMG = os.path.join(STATIC_DIR, 'footer.png')
CARATULA_IMG = os.path.join(STATIC_DIR, 'caratula.png')

# Meses en español (mayúsculas)
MESES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]


def obtener_mes(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        return MESES[fecha.month - 1]
    except:
        return ""


def formatear_fecha(fecha_str):
    if not fecha_str:
        return ""
    try:
        dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return fecha_str


def obtener_servicio(req):
    try:
        return req.get("clientService", {}).get("service", {}).get("description", "")
    except:
        return ""


# ============================================
# CLASE PDF PERSONALIZADA
# ============================================
class ReportePDF(FPDF):
    def header(self):
        # Si es la página 1 (carátula), no dibujar el header normal
        if self.page_no() == 1:
            return

        # Imagen del encabezado (Franja LEES)
        if os.path.exists(HEADER_IMG):
            # Ancho de A4 es 210mm. La imagen ocupará todo el ancho.
            self.image(HEADER_IMG, x=0, y=0, w=210)
        
        # Mover el cursor hacia abajo para no chocar con la imagen
        self.set_y(25)
        
        # Título principal
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(44, 62, 80)
        self.cell(0, 10, self.titulo, 0, 1, "C")
        self.ln(5)
    
    def footer(self):
        # Si es la página 1, no dibujar el footer normal
        if self.page_no() == 1:
            return

        # Imagen del pie de página (contacto, redes)
        if os.path.exists(FOOTER_IMG):
            # Posicionar al fondo de la hoja A4 (297mm alto)
            self.image(FOOTER_IMG, x=0, y=280, w=210)


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def generar_pdf(facturacion, start_date, end_date):
    """Genera el PDF del reporte con FPDF2"""
    
    mes = obtener_mes(start_date)
    titulo = f"REPORTE MES {mes} - {facturacion['cliente']}"
    
    # Crear PDF (A4, milímetros)
    pdf = ReportePDF(orientation="P", unit="mm", format="A4")
    pdf.titulo = titulo
    pdf.set_auto_page_break(auto=True, margin=25) # Margen inferior para el footer
    
    # ========================================
    # PÁGINA 1: CARÁTULA
    # ========================================
    pdf.add_page()
    if os.path.exists(CARATULA_IMG):
        # Insertar la imagen de la carátula ocupando toda la hoja A4
        pdf.image(CARATULA_IMG, x=0, y=0, w=210, h=297)
    else:
        # Si no hay imagen, poner un texto de respaldo
        pdf.set_y(100)
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 20, "RESUMEN DE EXÁMENES", 0, 1, "C")

    # ========================================
    # PÁGINA 2: RESUMEN
    # ========================================
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Resumen", 0, 1, "L")
    pdf.ln(2)
    
    # Anchos de la tabla
    w_tipo = 60
    w_cant = 70
    w_total = 50
    
    # Encabezado de la tabla
    pdf.set_fill_color(240, 240, 240) # Gris claro
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w_tipo, 8, "Tipo de examen", 1, 0, "C", True)
    pdf.cell(w_cant, 8, "Cantidad de exámenes", 1, 0, "C", True)
    pdf.cell(w_total, 8, "TOTAL", 1, 1, "C", True)
    
    # Filas de la tabla
    pdf.set_font("Helvetica", "", 9)
    for key, item in facturacion["detalle"].items():
        if item["cantidad"] == 0:
            continue
            
        tipo = item.get("tipo", "rango")
        
        # Formatear la cantidad según el tipo
        if tipo in ["rango", "personalizado"]:
            cant_texto = f"{item['cantidad']} exámenes ({item['rango']})"
        elif tipo == "umbral":
            cant_texto = f"{item['cantidad']} exámenes"
        else:
            cant_texto = f"{item['cantidad']} exámenes"
            
        # Imprimir fila
        pdf.set_text_color(0, 0, 0)
        pdf.cell(w_tipo, 8, item["descripcion"], 1, 0, "L")
        pdf.cell(w_cant, 8, cant_texto, 1, 0, "C")
        pdf.cell(w_total, 8, f"S/ {item['subtotal']:.2f}", 1, 1, "R")
        
    # Fila de Total General (Fondo amarillo claro)
    pdf.set_fill_color(255, 235, 156) # Amarillo claro
    pdf.set_font("Helvetica", "B", 10)
    
    # Si hay más de un grupo, armamos el texto "RANGO A + B"
    rangos_texto = " + ".join([str(item.get("rango", "")) for key, item in facturacion["detalle"].items() if item["cantidad"] > 0])
    if not rangos_texto:
        rangos_texto = "TOTAL"
        
    pdf.cell(w_tipo, 10, "Total", 1, 0, "L", True)
    pdf.cell(w_cant, 10, rangos_texto, 1, 0, "C", True)
    pdf.cell(w_total, 10, f"S/ {facturacion['total']:.2f}", 1, 1, "C", True)
    pdf.ln(8)
    
    # Cuadro de Cancelados (Rojo)
    if facturacion.get("total_cancelados", 0) > 0:
        w_cancel = 80
        # Encabezado rojo
        pdf.set_fill_color(220, 80, 80) # Rojo
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w_cancel, 7, "Cantidad de exámenes cancelados", 1, 1, "C", True)
        # Fila blanca
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(w_cancel, 8, f"{facturacion['total_cancelados']} exámenes", 1, 1, "C")
        pdf.ln(8)
    
    # ========================================
    # PÁGINA 3+: DETALLE DE EXÁMENES
    # ========================================
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Detalle de Exámenes", 0, 1, "L")
    
    pdf.set_draw_color(127, 178, 255)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    w_enviado = 30
    w_modalidad = 18
    w_servicio = 55
    w_paciente = 50
    w_cliente = 37
    
    for key, item in facturacion["detalle"].items():
        if item["cantidad"] == 0:
            continue
        
        # Nombre del grupo
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 6, item["descripcion"], 0, 1, "L")
        
        # Encabezado de la tabla
        pdf.set_fill_color(127, 178, 255)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(w_enviado, 6, "Enviado", 1, 0, "C", True)
        pdf.cell(w_modalidad, 6, "Modalidad", 1, 0, "C", True)
        pdf.cell(w_servicio, 6, "Servicio", 1, 0, "C", True)
        pdf.cell(w_paciente, 6, "Paciente", 1, 0, "C", True)
        pdf.cell(w_cliente, 6, "Cliente", 1, 1, "C", True)
        
        # Filas
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        
        for sol in item["solicitudes"]:
            enviado = formatear_fecha(sol.get("createdAt"))
            modalidad = sol.get("modalityName", "")
            servicio = obtener_servicio(sol)
            paciente = sol.get("patientName", "")
            cliente = sol.get("client", {}).get("fantasyName", "") or sol.get("client", {}).get("companyName", "")
            
            # Recortar textos largos
            servicio = (servicio[:35] + "...") if len(servicio) > 38 else servicio
            paciente = (paciente[:30] + "...") if len(paciente) > 33 else paciente
            cliente = (cliente[:22] + "...") if len(cliente) > 25 else cliente
            
            pdf.cell(w_enviado, 5, enviado, 1, 0, "L")
            pdf.cell(w_modalidad, 5, modalidad, 1, 0, "C")
            pdf.cell(w_servicio, 5, servicio, 1, 0, "L")
            pdf.cell(w_paciente, 5, paciente, 1, 0, "L")
            pdf.cell(w_cliente, 5, cliente, 1, 1, "L")
        
        # Total del grupo
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 6, f"Total: {item['cantidad']}", 0, 1, "R")
        pdf.ln(5)
    
    # Retornar PDF como bytes
    return bytes(pdf.output())