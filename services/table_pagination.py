from flask import request

PER_PAGE = 20


def paginate(query, per_page=PER_PAGE, page=1):
    page = max(1, page)
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return total, total_pages, items


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
