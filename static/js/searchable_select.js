(function ($) {
    'use strict';

    function buildFilter($select) {
        var $filter = $('<input type="text" class="admin-input searchable-select-filter" placeholder="Buscar cliente..." autocomplete="off" />');
        var $clear = $('<button type="button" class="searchable-select-clear" title="Limpiar b\xFAsqueda" aria-label="Limpiar b\xFAsqueda">\xD7</button>');

        var $wrap = $select.wrap('<div class="searchable-select"></div>').parent();
        $filter.insertBefore($select);
        $clear.insertBefore($select);

        function applyFilter() {
            var term = $.trim($filter.val().toLowerCase());
            $select.find('option').each(function () {
                var show = !term || $(this).text().toLowerCase().indexOf(term) !== -1;
                $(this).prop('hidden', !show);
            });
            $clear.toggle(!!term);
        }

        $filter.on('input', applyFilter);
        $filter.on('keydown', function (e) {
            if (e.key === 'Escape') {
                $filter.val('');
                applyFilter();
                $select.focus();
            }
        });

        $clear.on('click', function () {
            $filter.val('');
            applyFilter();
            $filter.focus();
        });

        $filter.on('blur', function () {
            var $selOpt = $select.find('option:selected');
            if ($selOpt.length && $selOpt.val()) {
                $filter.val($selOpt.text());
            }
        });
    }

    function enhance() {
        $('select[data-searchable]').each(function () {
            var $sel = $(this);
            if ($sel.closest('.searchable-select').length) return;
            buildFilter($sel);
        });
    }

    $(function () {
        enhance();
    });

    if (window.MutationObserver) {
        new MutationObserver(enhance).observe(document.body, { subtree: true, childList: true });
    }

})(window.jQuery);