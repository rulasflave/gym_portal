import re


def _hrefs(html):
    return re.findall(r'href=["\']([^"\']+)["\']', html)


def _srcs(html):
    return re.findall(r'src=["\']([^"\']+)["\']', html)


def _urls_of(html):
    return [u for u in _hrefs(html) + _srcs(html) if not u.startswith(('http', '#', 'mailto:', 'tel:', 'data:'))]


def test_vitelas_landing_raiz(client):
    resp = client.get('/vitelas/')
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'Vitelas Club' in body
    assert 'Reglamentos del Club' in body
    assert '/vitelas/reglamentos' in body


def test_vitelas_landing_sin_slash_raiz(client):
    resp = client.get('/vitelas')
    assert resp.status_code in (200, 308)
    if resp.status_code == 308:
        assert resp.headers['Location'].rstrip('/').endswith('/vitelas')


def test_vitelas_reglamentos(client):
    resp = client.get('/vitelas/reglamentos')
    assert resp.status_code == 200
    body = resp.data.decode()
    assert 'Reglamentos' in body
    assert '/vitelas/' in body


def test_vitelas_static_css_resuelve(client):
    assert client.get('/static/vitelas/css/index.css').status_code == 200
    assert client.get('/static/vitelas/css/reglamentos.css').status_code == 200


def test_vitelas_static_assets_resuelven(client):
    for path in ('/vitelas/', '/vitelas/reglamentos'):
        html = client.get(path).data.decode()
        for ref in _urls_of(html):
            if ref.startswith('/static/'):
                assert client.get(ref).status_code == 200, f'{ref} en {path}'


def test_vitelas_css_urls_resuelven(client):
    import os
    for css_rel in ('css/index.css', 'css/reglamentos.css'):
        css = client.get(f'/static/vitelas/{css_rel}').data.decode()
        base = os.path.dirname(css_rel)
        for m in re.finditer(r"url\(['\"]?(.*?)['\"]?\)", css):
            ref = m.group(1)
            if ref.startswith(('data:', 'http')):
                continue
            resolved = os.path.normpath(os.path.join(base, ref)).replace('\\', '/')
            assert client.get(f'/static/vitelas/{resolved}').status_code == 200, \
                f'{ref} en {css_rel} -> {resolved}'


def test_vitelas_landing_no_enlaces_internos_rotos(client):
    for path in ('/vitelas/', '/vitelas/reglamentos'):
        html = client.get(path).data.decode()
        for ref in _hrefs(html):
            if ref.startswith('/vitelas') or ref.startswith('/static'):
                assert client.get(ref).status_code == 200, f'{ref} en {path}'