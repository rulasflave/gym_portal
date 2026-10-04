import re


def _hrefs(html):
    return re.findall(r'href=["\']([^"\']+)["\']', html)


def _srcs(html):
    return re.findall(r'src=["\']([^"\']+)["\']', html)


def _urls_of(html):
    return [u for u in _hrefs(html) + _srcs(html) if not u.startswith(('http', '#', 'mailto:', 'tel:', 'data:'))]


def test_ax_landing_raiz(client):
    resp = client.get('/ax/')
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'AXIS HYBRID' in body
    assert '#MOVEONAXIS' in body
    assert '#precios' in body


def test_ax_landing_sin_slash_raiz(client):
    resp = client.get('/ax')
    assert resp.status_code in (200, 308)
    if resp.status_code == 308:
        assert resp.headers['Location'].rstrip('/').endswith('/ax')


def test_ax_static_css_resuelve(client):
    assert client.get('/static/ax/css/index.css').status_code == 200


def test_ax_static_assets_resuelven(client):
    for path in ('/ax/',):
        html = client.get(path).data.decode()
        for ref in _urls_of(html):
            if ref.startswith('/static/'):
                assert client.get(ref).status_code == 200, f'{ref} en {path}'


def test_ax_landing_no_enlaces_internos_rotos(client):
    for path in ('/ax/',):
        html = client.get(path).data.decode()
        for ref in _hrefs(html):
            if ref.startswith('/ax') or ref.startswith('/static'):
                assert client.get(ref).status_code == 200, f'{ref} en {path}'