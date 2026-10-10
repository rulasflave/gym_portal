from services.branding import is_axis, get_brand


def test_is_axis_variants_insensibles_a_mayusculas():
    assert is_axis('Axis')
    assert is_axis('axis')
    assert is_axis('aXiS')
    assert is_axis(' AXIS ')
    assert is_axis(' axis ')


def test_is_axis_falso_para_otros():
    assert not is_axis('Box')
    assert not is_axis('')
    assert not is_axis(None)


def test_get_brand_axis():
    b = get_brand('Axis')
    assert b['key'] == 'axis'
    assert b['nombre'] == 'AXIS HYBRID'
    assert b['accent'] == '#8200de'
    assert b['logo'] == 'ax/assets/images/axis-hybrid-logo.svg'
    assert b['home'] == 'axis.dashboard'


def test_get_brand_vitelas_por_defecto():
    for v in ('Box', None, ''):
        b = get_brand(v)
        assert b['key'] == 'vitelas'
        assert b['accent'] == '#FFC400'
        assert b['logo'] == 'assets/images/HULK AGILA_vitelas.svg'
        assert b['home'] == 'cliente.dashboard'
