import pytest
from services.notification_service import send_email, send_whatsapp

def test_send_email_without_config():
    result = send_email('test@test.com', 'Test', 'Test body')
    assert result == False

def test_send_whatsapp_without_config():
    result = send_whatsapp('1234567890', 'Test message')
    assert result == False