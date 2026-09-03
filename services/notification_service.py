import os
import requests


def _resolve_chat_ids():
    try:
        from models.configuracion_recordatorio import ConfiguracionRecordatorio
        config = ConfiguracionRecordatorio.get_config()
        if config.chat_ids:
            return [c.strip() for c in config.chat_ids.split(',') if c.strip()]
    except Exception:
        pass
    return [c.strip() for c in os.environ.get('TELEGRAM_CHAT_ID', '').split(',') if c.strip()]


def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_ids = _resolve_chat_ids()

    if not token or not chat_ids:
        print("Telegram not configured, skipping message")
        return False

    ok = False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        for chat_id in chat_ids:
            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(url, json=payload, timeout=10)
            ok = ok or response.status_code == 200
        return ok
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
