import qrcode
from io import BytesIO
import base64

def generate_qr_code(numero_registro):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(numero_registro)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"
