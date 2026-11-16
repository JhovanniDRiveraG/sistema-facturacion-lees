import pandas as pd
from io import BytesIO
from app.utils.helpers import format_date, get_sla_status, get_client_name
#importaciomes para el exel de valores
import json
import os
import glob

def generate_excel(requests):
    """Genera archivo Excel con las columnas solicitadas"""

    data = []
    for req in requests:
        # Médico firmante
        signer_name = ""
        if req.get("validated"):
            signer_name = req["validated"].get("name", "")

        # Cliente
        client_name = get_client_name(req)

        # Columnas nuevas
        sla_status = get_sla_status(req)
        pendiente = "No" if req.get("validated") else "Sí"

        # NUEVO: Extraer el nombre del Servicio
        servicio_desc = ""
        if req.get("clientService") and req["clientService"].get("service"):
            servicio_desc = req["clientService"]["service"].get("description", "")

        data.append({
            "Paciente": req.get("patientName", ""),
            "Procedimiento": req.get("procedureName", ""),
            "Servicio": servicio_desc,
            "Modalidad": req.get("modalityName", ""),
            "Estado": req.get("requestStatus", {}).get("name", ""),
            "Firmado": "Sí" if req.get("validated") else "No",
            "Pendiente": pendiente,
            "SLA": sla_status,
            "Fecha Enviado": format_date(req.get("createdAt")),
            "Fecha Firmado": format_date(req.get("validatedAt")),
            "Médico Firmante": signer_name,
            "Cliente": client_name
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Facturación', index=False)

        # Resumen
        total = len(data)
        firmados = sum(1 for d in data if d["Firmado"] == "Sí")
        no_firmados = total - firmados
        pendientes = sum(1 for d in data if d["Pendiente"] == "Sí")
        a_tiempo = sum(1 for d in data if d["SLA"] == "A TIEMPO")
        atrasados = sum(1 for d in data if d["SLA"] == "ATRASADO")

        resumen = pd.DataFrame({
            "Métrica": [
                "Total Solicitudes",
                "Firmadas",
                "No Firmadas",
                "Pendientes (no firmadas)",
                "A Tiempo (SLA)",
                "Atrasadas (SLA)"
            ],
            "Cantidad": [
                total,
                firmados,
                no_firmados,
                pendientes,
                a_tiempo,
                atrasados
            ]
        })
        resumen.to_excel(writer, sheet_name='Resumen', index=False)

        # Ajustar ancho de columnas
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_length = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_length

    output.seek(0)
    return output

# exle con valores
def generate_excel_tarifario(requests, cliente):
    """
    Genera el Excel de valores.
    Busca en la carpeta de tarifarios el archivo que corresponda al cliente.
    """
    import glob
    import os
    import re
    from openpyxl.styles import PatternFill, Font, Alignment
    
    # 1. Ruta de la carpeta de tarifarios
    ruta_carpeta = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'tarifario')
    archivos = glob.glob(os.path.join(ruta_carpeta, '*.json'))
    
    tarifario = None
    for archivo in archivos:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("cliente", "").strip().upper() == cliente.strip().upper():
                    tarifario = data
                    break
        except Exception:
            continue
            
    if not tarifario:
        raise Exception(f"No se encontró un archivo tarifario para el cliente: {cliente}")

    data = []
    for req in requests:
        # 2. EXTRAER EL NOMBRE
        servicio = ""
        if req.get("clientService") and req["clientService"].get("service"):
            servicio = req["clientService"]["service"].get("description", "")
        if not servicio:
            servicio = req.get("procedureName", "")
        
        # LIMPIEZA INTELIGENTE
        servicio_clean = " ".join(servicio.upper().split())
        servicio_clean = servicio_clean.replace(" - GENERAL", "").strip()
        servicio_clean = re.sub(r'\s*\(.*?\)', '', servicio_clean).strip()

        modalidad = req.get("modalityName", "").upper()

        # 3. BUSCAR EL PRECIO
        precio_base = 0.0
        if modalidad in ["CT"]:
            diccionario = tarifario.get("TEM", {})
            precio_base = diccionario.get(servicio_clean, 0.0)
        elif modalidad in ["RX", "CR", "DX"]:
            diccionario = tarifario.get("RX", {})
            precio_base = diccionario.get(servicio_clean, 0.0)

        if precio_base == 0.0 and 'diccionario' in locals():
            for nombre_json, precio in diccionario.items():
                if nombre_json in servicio_clean or servicio_clean in nombre_json:
                    precio_base = precio
                    break

        # 4. URGENCIA
        is_urgent = req.get("isUrgent", False)
        precio_con_igv = (precio_base * 1.20) if (is_urgent and precio_base > 0) else precio_base

        # 5. CÁLCULOS
        if precio_con_igv > 0:
            valor_sin_igv = round(precio_con_igv / 1.18, 2)
            valor_rhe = round(valor_sin_igv * 1.08, 2)
        else:
            valor_sin_igv = 0.0
            valor_rhe = 0.0

        data.append({
            "Enviado": format_date(req.get("createdAt")),
            "Firmado": format_date(req.get("validatedAt")),
            "Modalidad": modalidad,
            "Servicio": servicio,
            "Paciente": req.get("patientName", ""),
            "Valor": round(precio_con_igv, 2),
            "Valor sin IGV": valor_sin_igv,
            "Valor por RHE": valor_rhe
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Valores', index=False)
        
        worksheet = writer.sheets['Valores']
        
        # Colores para el encabezado y totales (Celeste claro)
        fill_celeste = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        font_bold = Font(bold=True)

        # --- ESTILO DEL ENCABEZADO ---
        for cell in worksheet[1]:
            cell.fill = fill_celeste
            cell.font = font_bold
            cell.alignment = Alignment(horizontal="center")

        # --- FORMATO DE MONEDA (S/.) ---
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=6, max_col=8):
            for cell in row:
                cell.number_format = '"S/." #,##0.00'

        # --- FILA DE TOTALES Y CANTIDAD ---
        last_row = worksheet.max_row
        total_row = last_row + 1
        
        # Aplicar el color celeste a la fila de totales
        for cell in worksheet[total_row]:
            cell.fill = fill_celeste
            cell.font = font_bold
            
        # Poner la palabra "TOTAL" en la columna del Servicio (índice 4)
        #worksheet.cell(row=total_row, column=4, value="TOTALES")
        
        # Poner la cantidad de exámenes debajo de "Enviado" (índice 1)
        worksheet.cell(row=total_row, column=1, value=f"Total exámenes: {len(data)}")
        
        # Poner las sumas en las columnas de moneda
        worksheet.cell(row=total_row, column=6, value=df["Valor"].sum())
        worksheet.cell(row=total_row, column=7, value=df["Valor sin IGV"].sum())
        worksheet.cell(row=total_row, column=8, value=df["Valor por RHE"].sum())

        # Formatear las sumas como moneda
        for col_idx in [6, 7, 8]:
            cell = worksheet.cell(row=total_row, column=col_idx)
            cell.number_format = '"S/." #,##0.00'

        # --- AJUSTAR ANCHO DE COLUMNAS ---
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_length = min(max_length + 2, 50)

            if column_letter in ['F', 'G', 'H']:
                adjusted_length = 18  # <-- Hacemos que estas columnas sean bien anchas

            worksheet.column_dimensions[column_letter].width = adjusted_length
            
    output.seek(0)
    return output