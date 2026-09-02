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
