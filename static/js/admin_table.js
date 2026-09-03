$(function () {
    var $search = $('#adminSearch');
    if (!$search.length) return;
    var $tbody = $('#adminTableBody');
    var $count = $('#adminResultCount');
    var $pagination = $('#adminPagination');
    var timer = null;

    function load(page, q) {
        $.ajax({
            url: window.location.pathname,
            data: { page: page, q: q },
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function (res) {
                $tbody.html(res.html);
                $count.text(res.total + ' registros');
                if ($pagination.length) {
                    var prev = res.page > 1 ? '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page - 1) + '">← Anterior</button>' : '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page - 1) + '" disabled>← Anterior</button>';
                    var next = res.page < res.total_pages ? '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page + 1) + '">Siguiente →</button>' : '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page + 1) + '" disabled>Siguiente →</button>';
                    $pagination.html(prev + '<span style="color: var(--text-secondary);">Página ' + res.page + ' de ' + res.total_pages + '</span>' + next);
                }
                $tbody.attr('data-total', res.total).attr('data-total-pages', res.total_pages).attr('data-page', res.page);
            }
        });
    }

    $search.on('input', function () {
        clearTimeout(timer);
        var val = $.trim(this.value);
        timer = setTimeout(function () { load(1, val); }, 250);
    });

    $(document).on('click', '.admin-pagination button[data-page]:not(:disabled)', function () {
        load($(this).data('page'), $.trim($search.val()));
    });
});
