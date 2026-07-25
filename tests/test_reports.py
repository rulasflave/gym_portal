import pytest
from services.report_service import generate_clientes_pdf, generate_clientes_excel

def test_generate_pdf_with_empty_list():
    buffer = generate_clientes_pdf([])
    assert buffer is not None

def test_generate_excel_with_empty_list():
    buffer = generate_clientes_excel([])
    assert buffer is not None