import pytest
from services.notification_service import send_telegram

def test_send_telegram_without_config():
    result = send_telegram('Test message')
    assert result == False
