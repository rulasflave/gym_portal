PORTAIS = {
    'axis': {
        'key': 'axis',
        'nombre': 'AXIS HYBRID',
        'logo': 'ax/assets/images/axis-hybrid-logo.svg',
        'accent': '#8200de',
        'accent_dark': '#b047ff',
        'css': 'ax/css/dashboard_axis.css',
        'home': 'axis.dashboard',
        'cambiar_password': 'axis.cambiar_password',
    },
    'vitelas': {
        'key': 'vitelas',
        'nombre': 'Vitellas Boxing',
        'logo': 'assets/images/HULK AGILA_vitelas.svg',
        'accent': '#FFC400',
        'accent_dark': '#A98200',
        'css': None,
        'home': 'cliente.dashboard',
        'cambiar_password': 'cliente.cambiar_password',
    },
}


def is_axis(empresa):
    return (empresa or '').strip().lower() == 'axis'


def get_brand(empresa):
    return PORTAIS['axis'] if is_axis(empresa) else PORTAIS['vitelas']
