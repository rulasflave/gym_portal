from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

def generate_clientes_pdf(clientes):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Reporte de Clientes")
    c.drawString(72, 730, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.setFont("Helvetica", 10)
    y = 700
    
    c.drawString(72, y, "Registro")
    c.drawString(150, y, "Nombre")
    c.drawString(350, y, "Telefono")
    c.drawString(450, y, "Estado")
    y -= 20
    
    for cliente in clientes:
        if y < 50:
            c.showPage()
            y = 750
        
        c.drawString(72, y, cliente.numero_registro)
        c.drawString(150, y, cliente.nombre_completo[:30])
        c.drawString(350, y, cliente.telefono or '')
        c.drawString(450, y, cliente.estado_membresia)
        y -= 20
    
    c.save()
    buffer.seek(0)
    return buffer

def generate_clientes_excel(clientes):
    wb = Workbook()
    ws = wb.active
    ws.title = "Clientes"
    
    headers = ["Registro", "Nombre", "Telefono", "Email", "Membresia", "Estado", "Vence"]
    ws.append(headers)
    
    for cliente in clientes:
        ws.append([
            cliente.numero_registro,
            cliente.nombre_completo,
            cliente.telefono or '',
            cliente.email or '',
            cliente.tipo_membresia,
            cliente.estado_membresia,
            cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else ''
        ])
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generate_pagos_pdf(pagos):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Reporte de Pagos")
    c.drawString(72, 730, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.setFont("Helvetica", 10)
    y = 700
    
    c.drawString(72, y, "Cliente")
    c.drawString(200, y, "Monto")
    c.drawString(300, y, "Fecha")
    c.drawString(400, y, "Metodo")
    y -= 20
    
    for pago in pagos:
        if y < 50:
            c.showPage()
            y = 750
        
        cliente = pago.cliente
        c.drawString(72, y, cliente.numero_registro if cliente else 'N/A')
        c.drawString(200, y, f"${pago.monto:.2f}")
        c.drawString(300, y, pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '')
        c.drawString(400, y, pago.metodo_pago or '')
        y -= 20
    
    c.save()
    buffer.seek(0)
    return buffer

def generate_pagos_excel(pagos):
    wb = Workbook()
    ws = wb.active
    ws.title = "Pagos"
    
    headers = ["Cliente", "Registro", "Monto", "Fecha", "Metodo", "Concepto"]
    ws.append(headers)
    
    for pago in pagos:
        cliente = pago.cliente
        ws.append([
            cliente.nombre_completo if cliente else 'N/A',
            cliente.numero_registro if cliente else 'N/A',
            float(pago.monto),
            pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
            pago.metodo_pago or '',
            pago.concepto or ''
        ])
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer