import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to_email, subject, body):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        print("SMTP not configured, skipping email")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_whatsapp(phone_number, message):
    api_key = os.getenv('WHATSAPP_API_KEY')
    api_secret = os.getenv('WHATSAPP_API_SECRET')
    
    if not api_key or not api_secret:
        print("WhatsApp API not configured, skipping message")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(api_key, api_secret)
        client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',
            to=f'whatsapp:+52{phone_number}'
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return False

def notify_membresia_venciendo(cliente, dias_restantes):
    subject = f"Tu membresía vence en {dias_restantes} días"
    body = f"""
    <h2>Hola {cliente.nickname or cliente.nombre_completo},</h2>
    <p>Tu membresía vence en <strong>{dias_restantes} días</strong>.</p>
    <p>Fecha de vencimiento: {cliente.fecha_fin_membresia.strftime('%d/%m/%Y')}</p>
    <p>Renueva para seguir disfrutando del gym.</p>
    <p>Saludos,<br>Gym Portal</p>
    """
    
    if cliente.email:
        send_email(cliente.email, subject, body)
    
    if cliente.telefono:
        message = f"Hola {cliente.nickname}, tu membresía vence en {dias_restantes} días. Renueva pronto."
        send_whatsapp(cliente.telefono, message)

def notify_cumpleanos(cliente):
    subject = "¡Feliz cumpleaños! 🎂"
    body = f"""
    <h2>¡Feliz cumpleaños {cliente.nickname or cliente.nombre_completo}!</h2>
    <p>Te deseamos un excelente día.</p>
    <p>Saludos,<br>Gym Portal</p>
    """
    
    if cliente.email:
        send_email(cliente.email, subject, body)
    
    if cliente.telefono:
        message = f"¡Feliz cumpleaños {cliente.nickname}! Te deseamos un excelente día. 🎂"
        send_whatsapp(cliente.telefono, message)