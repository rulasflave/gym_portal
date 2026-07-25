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