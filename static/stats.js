(function () {
    var summaryEl = document.getElementById('statsSummary');
    var bodyEl = document.getElementById('statsBody');

    function getLang() {
        return (typeof window.TIPTOP_LANG !== 'undefined' ? window.TIPTOP_LANG : (document.body && document.body.getAttribute('data-lang'))) || 'ru';
    }

    function formatDate(iso) {
        if (!iso) return '—';
        var d = new Date(iso);
        var locale = getLang() === 'en' ? 'en-US' : 'ru-RU';
        return d.toLocaleDateString(locale, {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function loadStats() {
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

    loadStats();
})();
