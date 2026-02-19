(function () {
    var STORAGE_KEY = 'tiptyp_theme';
    var FONT_KEY = 'tiptyp_font';

    function getLang() {
        return (typeof window.TIPTOP_LANG !== 'undefined' ? window.TIPTOP_LANG : (document.body && document.body.getAttribute('data-lang'))) || 'ru';
    }

    // ——— Tabs ———
    var tabs = document.querySelectorAll('.profile-tab');
    var panels = document.querySelectorAll('.profile-panel');
    tabs.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-tab');
            tabs.forEach(function (t) { t.classList.remove('active'); });
            panels.forEach(function (p) {
                var show = p.id === 'panel-' + id;
                p.classList.toggle('active', show);
                p.hidden = !show;
            });
            this.classList.add('active');
            if (id === 'stats') loadProfileStats();
        });
    });

    // ——— Theme ———
    function setTheme(id) {
        document.body.dataset.theme = id;
        try { localStorage.setItem(STORAGE_KEY, id); } catch (e) {}
        document.querySelectorAll('.theme-card.active').forEach(function (el) { el.classList.remove('active'); });
        var card = document.querySelector('.theme-card[data-theme="' + id + '"]');
        if (card) card.classList.add('active');
    }
    var storedTheme = '';
    try { storedTheme = localStorage.getItem(STORAGE_KEY) || 'dark1'; } catch (e) { storedTheme = 'dark1'; }
    if (document.body.dataset.theme) storedTheme = document.body.dataset.theme;
    setTheme(storedTheme);
    document.querySelectorAll('.profile-content .theme-card').forEach(function (btn) {
        btn.addEventListener('click', function () {
            setTheme(this.getAttribute('data-theme'));
        });
    });

    // ——— Font ———
    function getStoredFont() {
        try { return localStorage.getItem(FONT_KEY) || ''; } catch (e) { return ''; }
    }
    function setFont(fontName) {
        if (!fontName) {
            try { localStorage.removeItem(FONT_KEY); } catch (e) {}
            var cur = document.getElementById('profileFontCurrent');
            if (cur) cur.textContent = '—';
            return;
        }
        try { localStorage.setItem(FONT_KEY, fontName); } catch (e) {}
        var cur = document.getElementById('profileFontCurrent');
        if (cur) cur.textContent = fontName;
    }
    var fontList = [];
    var searchEl = document.getElementById('profileFontSearch');
    var dropEl = document.getElementById('profileFontDropdown');
    var currentEl = document.getElementById('profileFontCurrent');
    var resetBtn = document.getElementById('profileFontReset');
    if (resetBtn) resetBtn.addEventListener('click', function () { setFont(''); });
    var storedFont = getStoredFont();
    if (currentEl) currentEl.textContent = storedFont || '—';

    fetch('/static/fonts-list.json')
        .then(function (r) { return r.json(); })
        .then(function (arr) {
            fontList = arr;
            if (searchEl) {
                searchEl.addEventListener('focus', function () {
                    searchEl.dispatchEvent(new Event('input'));
                    dropEl.hidden = false;
                });
                searchEl.addEventListener('input', function () {
                    var q = (searchEl.value || '').trim().toLowerCase();
                    var list = q ? fontList.filter(function (f) { return f.toLowerCase().indexOf(q) >= 0; }) : fontList;
                    var show = list.slice(0, 80);
                    dropEl.innerHTML = '';
                    dropEl.hidden = show.length === 0 && !q;
                    show.forEach(function (name) {
                        var div = document.createElement('div');
                        div.className = 'font-option';
                        div.textContent = name;
                        div.addEventListener('click', function () {
                            setFont(name);
                            searchEl.value = '';
                            dropEl.hidden = true;
                            dropEl.innerHTML = '';
                        });
                        dropEl.appendChild(div);
                    });
                });
                searchEl.addEventListener('blur', function () {
                    setTimeout(function () { dropEl.hidden = true; }, 200);
                });
            }
        })
        .catch(function () {});

    // ——— Stats (load when tab opened) ———
    function formatDate(iso) {
        if (!iso) return '—';
        var d = new Date(iso);
        var locale = getLang() === 'en' ? 'en-US' : 'ru-RU';
        return d.toLocaleDateString(locale, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    function loadProfileStats() {
        var summaryEl = document.getElementById('profileStatsSummary');
        var bodyEl = document.getElementById('profileStatsBody');
        if (!summaryEl || !bodyEl) return;
        var isEn = getLang() === 'en';
        var loading = isEn ? 'Loading…' : 'Загрузка…';
        var noAttempts = isEn ? 'No attempts yet' : 'Пока нет попыток';
        var noAttemptsHint = isEn ? 'Take the test on the main page for statistics to appear here.' : 'Пройдите тест на главной странице, чтобы здесь появилась статистика.';
        var totalTests = isEn ? 'Total tests' : 'Всего тестов';
        var bestResult = isEn ? 'Best result' : 'Лучший результат';
        var avgResult = isEn ? 'Average' : 'Средний результат';
        var wpmUnit = isEn ? ' wpm' : ' слов/мин';
        var timeSec = isEn ? ' sec' : ' сек';
        var loadError = isEn ? 'Error loading statistics.' : 'Ошибка загрузки статистики.';

        summaryEl.innerHTML = '<p>' + loading + '</p>';

        fetch('/api/my_stats')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.total_tests === 0) {
                    summaryEl.innerHTML = '<p class="big">' + noAttempts + '</p><p>' + noAttemptsHint + '</p>';
                } else {
                    summaryEl.innerHTML =
                        '<p class="big">' + totalTests + ': ' + data.total_tests + '</p>' +
                        '<p>' + bestResult + ': <strong>' + (data.best_wpm != null ? data.best_wpm + wpmUnit : '—') + '</strong></p>' +
                        '<p>' + avgResult + ': <strong>' + (data.avg_wpm != null ? data.avg_wpm + wpmUnit : '—') + '</strong></p>';
                }
                bodyEl.innerHTML = '';
                data.results.forEach(function (r) {
                    var tr = document.createElement('tr');
                    tr.innerHTML =
                        '<td>' + formatDate(r.created_at) + '</td>' +
                        '<td>' + r.wpm + '</td>' +
                        '<td>' + r.accuracy + '%</td>' +
                        '<td>' + r.time_seconds + timeSec + '</td>';
                    bodyEl.appendChild(tr);
                });
            })
            .catch(function () {
                summaryEl.innerHTML = '<p>' + loadError + '</p>';
            });
    }
})();
