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


def test_home_renderiza_y_enlaza_ax(client):
    resp = client.get('/')
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'href="/ax/"' in body, 'la home debe enlazar a /ax/'


def test_home_sin_build_error_de_endpoint(client):
    resp = client.get('/')
    assert b'BuildError' not in resp.data


def test_ax_css_urls_resuelven(client):
    import os
    css = client.get('/static/ax/css/index.css').data.decode()
    base = 'css'
    found = False
    for m in re.finditer(r"url\(['\"]?(.*?)['\"]?\)", css):
        ref = m.group(1)
        if ref.startswith(('data:', 'http')):
            continue
        found = True
        resolved = os.path.normpath(os.path.join(base, ref)).replace('\\', '/')
        assert client.get(f'/static/ax/{resolved}').status_code == 200, \
            f'{ref} -> {resolved}'
    assert found, 'el CSS deberia tener al menos un url() local'


def test_ax_tiene_secciones_runnfit_y_merch(client):
    body = client.get('/ax/').data.decode()
    assert 'runnfit-section' in body
    assert 'merch-section' in body
    assert 'RUNNFIT' in body
    assert body.count('data-gallery>') == 7, 'deben ser 7 galerias de merch'


def test_ax_galerias_merch_tienen_imagenes(client):
    body = client.get('/ax/').data.decode()
    for path in _srcs(body):
        if path.startswith('/static/ax/assets/images/merch/'):
            assert client.get(path).status_code == 200, f'{path} no resuelve'