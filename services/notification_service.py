import os
import requests


def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    if not token or not chat_id:
        print("Telegram not configured, skipping message")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram: {e}")
        return False


def notify_membresia_venciendo(cliente, dias_restantes):
    message = (
        f"¡Hola {cliente.nickname}! 💪 Tu membresía vence en {dias_restantes} días "
        f"({cliente.fecha_fin_membresia.strftime('%d/%m/%Y')}). "
        f"¡Renueva pronto para seguir entrenando!"
    )
    send_telegram(message)


def notify_cumpleanos(cliente):
    message = f"🎂 ¡Feliz cumpleaños {cliente.nickname}! Te deseamos un excelente día. ¡Te esperamos en el gym!"
    send_telegram(message)
