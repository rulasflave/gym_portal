$(function () {
    var $search = $('#adminSearch');
    if (!$search.length) return;
    var $thead = $('#adminTableHead');
    var $tbody = $('#adminTableBody');
    var $count = $('#adminResultCount');
    var $pagination = $('#adminPagination');
    var timer = null;
    var state = { q: '', sort: '', dir: '' };

    function getParam(qs, key) {
        var m = new RegExp('[?&]' + key + '=([^&]*)').exec('?' + qs);
        return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : '';
    }

    function load(page) {
        var data = { page: page, q: state.q };
        if (state.sort) {
            data.sort = state.sort;
            data.dir = state.dir;
        }
        $.ajax({
            url: window.location.pathname,
            data: data,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            success: function (res) {
                $tbody.html(res.html);
                $thead.html(res.thead_html);
                $count.text(res.total + ' registros');
                if ($pagination.length) {
                    var prev = res.page > 1
                        ? '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page - 1) + '">← Anterior</button>'
                        : '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page - 1) + '" disabled>← Anterior</button>';
                    var next = res.page < res.total_pages
                        ? '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page + 1) + '">Siguiente →</button>'
                        : '<button class="admin-btn admin-btn-secondary" data-page="' + (res.page + 1) + '" disabled>Siguiente →</button>';
                    $pagination.html(prev + '<span style="color: var(--text-secondary);">Página ' + res.page + ' de ' + res.total_pages + '</span>' + next);
                }
                $tbody.attr('data-total', res.total)
                    .attr('data-total-pages', res.total_pages)
                    .attr('data-page', res.page);
            }
        });
    }

    $search.on('input', function () {
        clearTimeout(timer);
        state.q = $.trim(this.value);
        timer = setTimeout(function () { load(1); }, 250);
    });

    $(document).on('click', 'th[data-sortable]', function (e) {
        e.preventDefault();
        var href = $(this).attr('data-href');
        if (!href) return;
        var qs = href.split('?')[1] || '';
        state.sort = getParam(qs, 'sort');
        state.dir = getParam(qs, 'dir');
        load(1);
    });

    $(document).on('click', '.admin-pagination button[data-page]:not(:disabled)', function () {
        load($(this).data('page'));
    });
});