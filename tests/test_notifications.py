import pytest
from services.notification_service import send_telegram


def test_send_telegram_without_config():
    result = send_telegram('Test message')
    assert result is False


def test_send_telegram_multiple_chat_ids(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200

    def fake_post(url, json=None, timeout=None):
        calls.append(json['chat_id'])
        return FakeResponse()

    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'bot123')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '111,222')
    monkeypatch.setattr('requests.post', fake_post)

    result = send_telegram('Hola')
    assert result is True
    assert calls == ['111', '222']


def test_send_telegram_single_chat_id_with_spaces(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200

    def fake_post(url, json=None, timeout=None):
        calls.append(json['chat_id'])
        return FakeResponse()

    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'bot123')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '  665029832 ,  ')
    monkeypatch.setattr('requests.post', fake_post)

    result = send_telegram('Hola')
    assert result is True
    assert calls == ['665029832']


def test_send_telegram_uses_db_chat_ids(app, monkeypatch):
    with app.app_context():
        from extensions import db
        from models.configuracion_recordatorio import ConfiguracionRecordatorio
        ConfiguracionRecordatorio.get_config().chat_ids = '555,666'
        db.session.commit()
    calls = []
    def fake_post(url, json=None, timeout=None):
        calls.append(json['chat_id'])
        class R: status_code = 200
        return R()
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'bot1')
    monkeypatch.setattr('services.notification_service.requests.post', fake_post)
    from services.notification_service import send_telegram
    with app.app_context():
        ok = send_telegram('mensaje')
    assert ok is True
    assert calls == ['555', '666']


def test_send_telegram_db_empty_falls_back_to_env(app, monkeypatch):
    with app.app_context():
        from extensions import db
        from models.configuracion_recordatorio import ConfiguracionRecordatorio
        ConfiguracionRecordatorio.get_config().chat_ids = ''
        db.session.commit()
    calls = []
    def fake_post(url, json=None, timeout=None):
        calls.append(json['chat_id'])
        class R: status_code = 200
        return R()
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'bot1')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '999')
    monkeypatch.setattr('services.notification_service.requests.post', fake_post)
    from services.notification_service import send_telegram
    with app.app_context():
        ok = send_telegram('mensaje')
    assert ok is True
    assert calls == ['999']
