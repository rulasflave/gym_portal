(function ($) {
    'use strict';

    function normalize(text) {
        return (text || '')
            .toLowerCase()
            .replace(/[áéíóúÁÉÍÓÚ]/g, function (ch) {
                return { 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                          'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u' }[ch];
            });
    }

    function buildFilter($select) {
        var $native = $select.hide();
        var $wrap = $select.wrap('<div class="searchable-select"></div>').parent();

        $wrap.append(
            '<div class="ss-control" role="combobox" aria-expanded="false" aria-haspopup="listbox">' +
            '  <input type="text" class="ss-input" placeholder="Buscar cliente..." autocomplete="off" role="textbox" />' +
            '  <span class="ss-caret" aria-hidden="true"></span>' +
            '</div>' +
            '<ul class="ss-list" role="listbox" hidden></ul>'
        );

        var $input = $wrap.find('.ss-input');
        var $list = $wrap.find('.ss-list');
        var $control = $wrap.find('.ss-control');
        var options = [];

        $select.find('option').each(function () {
            var $o = $(this);
            if (!$o.val()) return;
            options.push({ value: $o.val(), text: $.trim($o.text()) });
        });

        function selectedIndex() {
            var v = $select.val();
            for (var i = 0; i < options.length; i++) {
                if (options[i].value === v) return i;
            }
            return -1;
        }

        function selectedText() {
            var idx = selectedIndex();
            return idx >= 0 ? options[idx].text : '';
        }

        function highlight() {
            var idx = selectedIndex();
            $list.children().removeClass('ss-active');
            if (idx >= 0) {
                var $item = $list.children().eq(idx);
                $item.addClass('ss-active');
                var el = $item.get(0);
                if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
            }
        }

        function render(term) {
            var t = normalize(term);
            $list.empty();
            var matched = 0;
            options.forEach(function (opt, i) {
                if (t && normalize(opt.text).indexOf(t) === -1) return;
                var $item = $('<li class="ss-item" role="option" data-index="' + i + '"></li>').text(opt.text);
                $list.append($item);
                matched++;
            });
            if (!matched) {
                $list.append('<li class="ss-empty">Sin resultados</li>');
            }
            highlight();
            return matched;
        }

        function open() {
            $list.removeAttr('hidden');
            $control.attr('aria-expanded', 'true');
        }

        function close() {
            $list.attr('hidden', '');
            $control.attr('aria-expanded', 'false');
        }

        function setValue(i) {
            if (i < 0 || i >= options.length) return;
            $select.val(options[i].value).trigger('change');
            $input.val(options[i].text);
            close();
        }

        function resetFilter() {
            $input.val(selectedText());
            render('');
        }

        $select.on('change', function () {
            resetFilter();
        });

        $input.on('focus', function () {
            render('');
            open();
            highlight();
        });

        $input.on('input', function () {
            render($input.val());
            open();
        });

        function visibleItems() {
            return $list.children().not('.ss-empty');
        }

        function singleVisible() {
            var $items = visibleItems();
            if ($items.length !== 1) return -1;
            return parseInt($items.eq(0).data('index'), 10);
        }

        $input.on('keydown', function (e) {
            var $items = visibleItems();
            var cur = $items.index($items.filter('.ss-active'));
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (!$list.is(':visible')) { render(''); open(); }
                    cur = Math.min(cur + 1, $items.length - 1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    cur = Math.max(cur - 1, 0);
                    break;
                case 'Enter': {
                    var single = singleVisible();
                    e.preventDefault();
                    if (cur >= 0) {
                        setValue(parseInt($items.eq(cur).data('index'), 10));
                    } else if (single >= 0) {
                        setValue(single);
                    }
                    break;
                }
                case 'Escape':
                    e.preventDefault();
                    close();
                    $control.blur();
                    break;
                case 'Tab':
                    if ($list.is(':visible')) {
                        var one = singleVisible();
                        if (one >= 0 && cur < 0) setValue(one);
                        close();
                    }
                    break;
                default:
                    return;
            }
            if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && cur >= 0 && cur < $items.length) {
                $items.removeClass('ss-active').eq(cur).addClass('ss-active');
            }
        });

        $list.on('mousedown', function (e) {
            var $item = $(e.target).closest('.ss-item');
            if ($item.length) {
                e.preventDefault();
                setValue(parseInt($item.data('index'), 10));
            }
        });

        $(document).on('mousedown', function (e) {
            if (!$wrap.get(0).contains(e.target)) close();
        });

        var $form = $select.closest('form');
        if ($form.length) {
            $form.on('submit', function () {
                if (!$select.val()) {
                    $input.val('');
                    $control.focus();
                    open();
                    render('');
                    $input.trigger('focus');
                    return false;
                }
            });
        }

        resetFilter();
    }

    function enhance() {
        $('select[data-searchable]').each(function () {
            var $sel = $(this);
            if ($sel.data('ss-ready')) return;
            $sel.data('ss-ready', true);
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