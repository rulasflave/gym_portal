import os
import requests


def send_telegram(message):
    all_keys = sorted(os.environ.keys())
    print(f"DEBUG2: Total env vars = {len(all_keys)}")
    telegram_keys = [k for k in all_keys if 'TELEGRAM' in k.upper()]
    print(f"DEBUG2: TELEGRAM keys found = {telegram_keys}")
    for k in telegram_keys:
        v = os.environ.get(k, '')
        print(f"DEBUG2: {k} = {v[:15]}..." if len(v) > 15 else f"DEBUG2: {k} = {v}")
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    print(f"DEBUG: token={token[:10] if token else 'NONE'}...", file=sys.stderr)
    print(f"DEBUG: chat_id={chat_id}", file=sys.stderr)
    
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
        print(f"DEBUG: Telegram response status = {response.status_code}")
        print(f"DEBUG: Telegram response = {response.text[:200]}")
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
