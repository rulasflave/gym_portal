from html.parser import HTMLParser

ALLOWED = {'b', 'strong', 'i', 'em', 'u', 's', 'ol', 'ul', 'li', 'a',
           'img', 'p', 'br', 'blockquote', 'h1', 'h2', 'h3', 'span', 'div'}
ATTR_ALLOW = {
    'a': ['href', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
    'span': ['style'],
    'p': ['style'],
    'div': ['style'],
}
SAFE_CSS = ('color', 'background-color', 'background', 'font-weight',
            'font-style', 'text-decoration', 'text-align')
VOID = {'br', 'img'}


def _safe_css(style):
    if not style:
        return ''
    out = []
    for part in style.split(';'):
        part = part.strip()
        if not part or ':' not in part:
            continue
        prop, _, val = part.partition(':')
        prop = prop.strip().lower()
        val = val.strip()
        if prop not in SAFE_CSS:
            continue
        if 'url(' in val.lower():
            continue
        out.append(f'{prop}:{val}')
    return ';'.join(out)


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in ALLOWED:
            return
        attrs_dict = dict(attrs)
        keep = {}
        for key in ATTR_ALLOW.get(tag, []):
            val = attrs_dict.get(key)
            if val is None:
                continue
            val = val.strip()
            if key in ('href', 'src'):
                low = val.lower()
                if not (low.startswith('data:image/') or low.startswith('http://')
                        or low.startswith('https://') or low.startswith('/') or low.startswith('#')):
                    continue
                keep[key] = val
            elif key == 'style':
                css = _safe_css(val)
                if css:
                    keep[key] = css
            else:
                keep[key] = val
        attrs_str = ''.join(f' {k}="{v}"' for k, v in keep.items())
        self.out.append(f'<{tag}{attrs_str}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ALLOWED and tag not in VOID:
            self.out.append(f'</{tag}>')

    def handle_data(self, data):
        self.out.append(data)


def sanitize_html(html):
    if not html:
        return ''
    p = _Sanitizer()
    p.feed(html)
    p.close()
    return ''.join(p.out)