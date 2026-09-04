from services.sanitizer import sanitize_html


def test_sanitize_quita_scripts_y_eventos():
    html = '<p onclick="x()">hola</p><script>alert(1)</script><img src="data:image/png;base64,AAA" onerror="x()">'
    out = sanitize_html(html)
    assert 'script' not in out.lower()
    assert 'onclick' not in out.lower()
    assert 'onerror' not in out.lower()
    assert 'src=' in out.lower()


def test_sanitize_mantiene_formato_basico():
    html = '<p><b>negrita</b></p><ol><li>item</li></ol><a href="https://x.com">link</a>'
    out = sanitize_html(html)
    assert '<b>' in out
    assert '<ol>' in out
    assert '<li>' in out
    assert 'href="https://x.com"' in out


def test_sanitize_bloque_javascript_protocolo():
    html = '<a href="javascript:alert(1)">x</a><img src="javascript:foo">'
    out = sanitize_html(html)
    assert 'javascript:' not in out.lower()


def test_sanitize_permite_imagenes_multiple():
    html = '<p>a</p><img src="data:image/png;base64,AAA"><p>b</p><img src="data:image/jpeg;base64,BBB">'
    out = sanitize_html(html)
    assert out.count('data:image/') == 2