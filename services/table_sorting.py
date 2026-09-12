def apply_sort(query, sort, sort_dir, columns):
    entry = columns.get(sort)
    if entry is None:
        return query
    if callable(entry):
        return query.order_by(entry(sort_dir))
    return query.order_by(entry.desc() if sort_dir == 'desc' else entry.asc())
