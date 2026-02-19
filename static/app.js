(function () {
    var typingWords = document.getElementById('typingWords');
    var typingInput = document.getElementById('typingInput');
    var timerEl = document.getElementById('timer');
    var wpmEl = document.getElementById('wpm');
    var accuracyEl = document.getElementById('accuracy');
    var btnRestart = document.getElementById('btnRestart');
    var resultInline = document.getElementById('resultInline');
    var resultStats = document.getElementById('resultStats');
    var resultReport = document.getElementById('resultReport');
    var resultSave = document.getElementById('resultSave');
    var btnCloseResult = document.getElementById('btnCloseResult');
    var visualKeyboard = document.getElementById('visualKeyboard');

    var words = [];

    var KEYBOARD_ROWS = [
        ['Backquote', 'Digit1', 'Digit2', 'Digit3', 'Digit4', 'Digit5', 'Digit6', 'Digit7', 'Digit8', 'Digit9', 'Digit0', 'Minus', 'Equal'],
        ['KeyQ', 'KeyW', 'KeyE', 'KeyR', 'KeyT', 'KeyY', 'KeyU', 'KeyI', 'KeyO', 'KeyP', 'BracketLeft', 'BracketRight'],
        ['KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 'KeyH', 'KeyJ', 'KeyK', 'KeyL', 'Semicolon', 'Quote'],
        ['KeyZ', 'KeyX', 'KeyC', 'KeyV', 'KeyB', 'KeyN', 'KeyM', 'Comma', 'Period', 'Slash'],
        ['Space']
    ];
    var LAYOUT_EN = {
        Backquote: '`', Digit1: '1', Digit2: '2', Digit3: '3', Digit4: '4', Digit5: '5', Digit6: '6', Digit7: '7', Digit8: '8', Digit9: '9', Digit0: '0', Minus: '-', Equal: '=',
        KeyQ: 'q', KeyW: 'w', KeyE: 'e', KeyR: 'r', KeyT: 't', KeyY: 'y', KeyU: 'u', KeyI: 'i', KeyO: 'o', KeyP: 'p', BracketLeft: '[', BracketRight: ']',
        KeyA: 'a', KeyS: 's', KeyD: 'd', KeyF: 'f', KeyG: 'g', KeyH: 'h', KeyJ: 'j', KeyK: 'k', KeyL: 'l', Semicolon: ';', Quote: "'",
        KeyZ: 'z', KeyX: 'x', KeyC: 'c', KeyV: 'v', KeyB: 'b', KeyN: 'n', KeyM: 'm', Comma: ',', Period: '.', Slash: '/',
        Space: ' '
    };
    var LAYOUT_RU = {
        Backquote: 'ё', Digit1: '1', Digit2: '2', Digit3: '3', Digit4: '4', Digit5: '5', Digit6: '6', Digit7: '7', Digit8: '8', Digit9: '9', Digit0: '0', Minus: '-', Equal: '=',
        KeyQ: 'й', KeyW: 'ц', KeyE: 'у', KeyR: 'к', KeyT: 'е', KeyY: 'н', KeyU: 'г', KeyI: 'ш', KeyO: 'щ', KeyP: 'з', BracketLeft: 'х', BracketRight: 'ъ',
        KeyA: 'ф', KeyS: 'ы', KeyD: 'в', KeyF: 'а', KeyG: 'п', KeyH: 'р', KeyJ: 'о', KeyK: 'л', KeyL: 'д', Semicolon: 'ж', Quote: 'э',
        KeyZ: 'я', KeyX: 'ч', KeyC: 'с', KeyV: 'м', KeyB: 'и', KeyN: 'т', KeyM: 'ь', Comma: 'б', Period: 'ю', Slash: '.',
        Space: ' '
    };

    function buildVisualKeyboard() {
        if (!visualKeyboard) return;
        var lang = getLang();
        var layout = lang === 'en' ? LAYOUT_EN : LAYOUT_RU;
        visualKeyboard.innerHTML = '';
        KEYBOARD_ROWS.forEach(function (rowCodes) {
            var row = document.createElement('div');
            row.className = 'keyboard-row';
            rowCodes.forEach(function (code) {
                var key = document.createElement('span');
                key.className = 'key' + (code === 'Space' ? ' key-space' : '');
                key.setAttribute('data-code', code);
                key.textContent = code === 'Space' ? (lang === 'en' ? 'Space' : 'Пробел') : (layout[code] || code);
                row.appendChild(key);
            });
            visualKeyboard.appendChild(row);
        });
    }

    function highlightKey(code, pressed) {
        if (!visualKeyboard) return;
        var key = visualKeyboard.querySelector('.key[data-code="' + code + '"]');
        if (key) {
            if (pressed) key.classList.add('key-pressed');
            else key.classList.remove('key-pressed');
        }
    }
    var startTime = null;
    var timerInterval = null;
    var totalChars = 0;
    var correctChars = 0;
    var lastWordCount = 0;
    var totalTypedChars = 0;
    var totalCorrectChars = 0;
    var prevInputValue = '';

    function getGenerator() {
        var sel = document.getElementById('wordGenerator');
        return sel ? sel.value : 'words';
    }

    function getWordCount() {
        var btn = document.querySelector('.word-count-btn.active');
        return btn ? parseInt(btn.getAttribute('data-count'), 10) : 25;
    }

    function getLang() {
        return (typeof window.TIPTOP_LANG !== 'undefined' ? window.TIPTOP_LANG : (document.body && document.body.getAttribute('data-lang'))) || 'ru';
    }

    function renderWords(done) {
        var lang = getLang();
        var loadingText = lang === 'en' ? 'Loading words…' : 'Загрузка слов…';
        var errorHint = lang === 'en' ? 'Try «Syllables» or refresh the page.' : 'Попробуйте «Слоги» или обновите страницу.';
        typingWords.innerHTML = '<span class="loading-words">' + loadingText + '</span>';
        typingInput.disabled = true;
        var count = getWordCount();
        var generator = getGenerator();
        fetch('/api/words?count=' + count + '&generator=' + encodeURIComponent(generator) + '&lang=' + encodeURIComponent(lang))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.words && data.words.length > 0) {
                    words = data.words;
                } else {
                    words = [];
                }
                if (words.length === 0) {
                    var errMsg = data.error ? (data.error + '. ') : '';
                    typingWords.innerHTML = '<span class="loading-words">' + errMsg + errorHint + '</span>';
                    if (typeof done === 'function') done();
                    return;
                }
                typingWords.innerHTML = words.map(function (w, i) {
                    return '<span class="word" data-idx="' + i + '">' + escapeHtml(w) + '</span>';
                }).join(' ');
                var first = typingWords.querySelector('.word');
                if (first) first.classList.add('current');
                typingInput.disabled = false;
                typingInput.value = '';
                prevInputValue = '';
                totalTypedChars = 0;
                totalCorrectChars = 0;
                highlightWords();
                if (typeof done === 'function') done();
            })
            .catch(function (err) {
                typingWords.innerHTML = '<span class="loading-words">' + (getLang() === 'en' ? 'Load error. Try «Syllables» or refresh.' : 'Ошибка загрузки. Попробуйте «Слоги» или обновите страницу.') + '</span>';
                typingInput.disabled = false;
                if (typeof done === 'function') done();
            });
    }

    function escapeHtml(s) {
        var div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    function startTimer() {
        if (startTime) return;
        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 200);
    }

    function updateTimer() {
        if (!startTime) return;
        var sec = Math.floor((Date.now() - startTime) / 1000);
        var m = Math.floor(sec / 60);
        var s = sec % 60;
        timerEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        updateWPM();
    }

    function updateWPM() {
        if (!startTime) return;
        var elapsedMin = (Date.now() - startTime) / 60000;
        var wordCount = countCompletedWords();
        var wpm = elapsedMin > 0 ? Math.round(wordCount / elapsedMin) : 0;
        wpmEl.textContent = wpm;
    }

    function getCompletedCountFromText(text) {
        var parts = text.trim().split(/\s+/).filter(Boolean);
        if (parts.length === 0) return 0;
        var endsWithSpace = /\s$/.test(text);
        return endsWithSpace ? parts.length : Math.max(0, parts.length - 1);
    }

    function getCompletedCount() {
        return getCompletedCountFromText(typingInput.value);
    }

    function getExpectedTextFromValue(text) {
        var n = getCompletedCountFromText(text);
        if (n >= words.length) return words.join(' ');
        return words.slice(0, n + 1).join(' ');
    }

    function getExpectedText() {
        return getExpectedTextFromValue(typingInput.value);
    }

    function countCompletedWords() {
        var completed = getCompletedCount();
        if (completed >= words.length) return words.length;
        if (completed === words.length - 1 && getCurrentWordTyped() === words[words.length - 1]) return words.length;
        return completed;
    }

    function updateAccuracy() {
        var pct = totalTypedChars ? Math.round((totalCorrectChars / totalTypedChars) * 100) : 0;
        accuracyEl.textContent = pct + '%';
    }

    function getCurrentWordTyped() {
        var full = typingInput.value;
        var lastSpace = full.lastIndexOf(' ');
        return lastSpace === -1 ? full : full.slice(lastSpace + 1);
    }

    function highlightWords() {
        var text = typingInput.value;
        var parts = text.trim().split(/\s+/).filter(Boolean);
        var completedCount = getCompletedCount();
        var currentTyped = getCurrentWordTyped();
        var wordSpans = typingWords.querySelectorAll('.word');
        wordSpans.forEach(function (span, idx) {
            span.classList.remove('correct', 'wrong', 'current');
            span.innerHTML = '';
            var word = words[idx];
            if (!word) return;
            if (idx < completedCount) {
                var typed = parts[idx] || '';
                span.classList.add(typed === word ? 'correct' : 'wrong');
                span.textContent = word;
            } else if (idx === completedCount) {
                span.classList.add('current');
                var expected = word;
                var html = '';
                for (var i = 0; i < currentTyped.length; i++) {
                    var c = expected[i];
                    var cls = currentTyped[i] === c ? 'char-correct' : 'char-wrong';
                    html += '<span class="' + cls + '">' + escapeHtml(c) + '</span>';
                }
                html += '<span class="cursor"></span>';
                for (var i = currentTyped.length; i < expected.length; i++) {
                    html += '<span class="char-rest">' + escapeHtml(expected[i]) + '</span>';
                }
                if (currentTyped.length > expected.length) {
                    for (var j = expected.length; j < currentTyped.length; j++) {
                        html += '<span class="char-wrong">' + escapeHtml(currentTyped[j]) + '</span>';
                    }
                }
                span.innerHTML = html;
            } else {
                span.textContent = word;
            }
        });
    }

    function stopTest() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        typingInput.disabled = true;
        showResult();
    }

    function buildTypingReport() {
        var expected = words.join(' ');
        var actual = typingInput.value;
        var wrongByLetter = {};
        var i;
        for (i = 0; i < actual.length && i < expected.length; i++) {
            if (actual[i] !== expected[i]) {
                var ch = expected[i];
                wrongByLetter[ch] = (wrongByLetter[ch] || 0) + 1;
            }
        }
        var parts = typingInput.value.trim().split(/\s+/).filter(Boolean);
        var wordsCorrect = 0;
        var wordsWrongList = [];
        for (i = 0; i < parts.length && i < words.length; i++) {
            if (parts[i] === words[i]) {
                wordsCorrect++;
            } else {
                wordsWrongList.push({ expected: words[i], typed: parts[i] });
            }
        }
        var sortedLetters = Object.keys(wrongByLetter).sort(function (a, b) {
            return wrongByLetter[b] - wrongByLetter[a];
        });
        var topLetters = sortedLetters.slice(0, 8);
        var isEn = getLang() === 'en';
        var reportHtml = isEn
            ? ('<div class="report-section"><strong>By words:</strong> ' + wordsCorrect + ' of ' + parts.length + ' correct.</div>')
            : ('<div class="report-section"><strong>По словам:</strong> ' + wordsCorrect + ' из ' + parts.length + ' введены верно.</div>');
        if (topLetters.length > 0) {
            reportHtml += isEn
                ? ('<div class="report-section"><strong>Most errors on letters:</strong> ' + topLetters.map(function (c) { return '"' + escapeHtml(c) + '"'; }).join(', ') + '.</div>')
                : ('<div class="report-section"><strong>Чаще ошибались на буквы:</strong> ' + topLetters.map(function (c) { return '"' + escapeHtml(c) + '"'; }).join(', ') + '.</div>');
        }
        if (wordsWrongList.length > 0 && wordsWrongList.length <= 15) {
            reportHtml += '<div class="report-section report-words-wrong"><strong>' + (isEn ? 'Words with errors:' : 'Слова с ошибками:') + '</strong> ';
            reportHtml += wordsWrongList.map(function (w) { return escapeHtml(w.expected) + ' → ' + escapeHtml(w.typed); }).join('; ') + '.</div>';
        } else if (wordsWrongList.length > 15) {
            reportHtml += '<div class="report-section"><strong>' + (isEn ? 'Words with errors:' : 'Слова с ошибками:') + '</strong> ' + wordsWrongList.length + (isEn ? ' words.' : ' слов.') + '</div>';
        }
        return reportHtml;
    }

    function showResult() {
        var timeSec = Math.floor((Date.now() - startTime) / 1000);
        var wordCount = countCompletedWords();
        var elapsedMin = timeSec / 60;
        var wpm = elapsedMin > 0 ? Math.round(wordCount / elapsedMin) : 0;
        var acc = totalTypedChars ? Math.round((totalCorrectChars / totalTypedChars) * 100) : 0;

        var isEn = getLang() === 'en';
        resultStats.innerHTML = isEn
            ? ('<p><strong>Words per minute:</strong> ' + wpm + '</p><p><strong>Accuracy:</strong> ' + acc + '%</p><p><strong>Time:</strong> ' + timeSec + ' sec</p><p><strong>Words typed:</strong> ' + wordCount + '</p>')
            : ('<p><strong>Слов в минуту:</strong> ' + wpm + '</p><p><strong>Точность:</strong> ' + acc + '%</p><p><strong>Время:</strong> ' + timeSec + ' сек</p><p><strong>Слов набрано:</strong> ' + wordCount + '</p>');

        if (resultReport) resultReport.innerHTML = buildTypingReport();
        resultSave.textContent = '';
        fetch('/api/save_result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                wpm: wpm,
                accuracy: acc,
                time_seconds: timeSec,
                chars_typed: totalTypedChars,
                chars_correct: totalCorrectChars
            })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                resultSave.textContent = data.ok
                    ? (getLang() === 'en' ? 'Result saved. See progress in My stats.' : 'Результат сохранён. Смотрите прогресс в «Моя статистика».')
                    : (data.error || (getLang() === 'en' ? 'Could not save.' : 'Не удалось сохранить.'));
            })
            .catch(function () {
                resultSave.textContent = getLang() === 'en' ? 'Could not save result.' : 'Не удалось сохранить результат.';
            });

        resultInline.hidden = false;
        resultInline.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function resetTest() {
        if (resultInline) resultInline.hidden = true;
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        startTime = null;
        totalChars = 0;
        correctChars = 0;
        totalTypedChars = 0;
        totalCorrectChars = 0;
        prevInputValue = '';
        lastWordCount = 0;
        typingInput.value = '';
        timerEl.textContent = '0:00';
        wpmEl.textContent = '0';
        accuracyEl.textContent = '—';
        renderWords(function () {
            typingInput.focus();
        });
    }

    function onTypingInput() {
        var raw = typingInput.value;
        if (/\r|\n/.test(raw)) {
            typingInput.value = raw.replace(/\r\n?|\n/g, ' ');
            raw = typingInput.value;
        }
        var next = raw;
        if (next.length > prevInputValue.length && next.slice(0, prevInputValue.length) === prevInputValue) {
            var added = next.slice(prevInputValue.length);
            for (var i = 0; i < added.length; i++) {
                var valBefore = prevInputValue + added.slice(0, i);
                var exp = getExpectedTextFromValue(valBefore);
                var pos = prevInputValue.length + i;
                var expectedChar = exp[pos];
                if (added[i] === expectedChar) totalCorrectChars++;
                totalTypedChars++;
            }
        }
        prevInputValue = next;
        startTimer();
        updateAccuracy();
        highlightWords();
        var w = countCompletedWords();
        if (w >= words.length) {
            stopTest();
        }
    }

    typingInput.addEventListener('input', onTypingInput);

    typingInput.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            resetTest();
            return;
        }
        if (e.key === 'Enter') {
            e.preventDefault();
            return;
        }
        highlightKey(e.code, true);
    });

    typingInput.addEventListener('keyup', function (e) {
        highlightKey(e.code, false);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            resetTest();
            return;
        }
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            resetTest();
        }
    });

    document.addEventListener('keyup', function (e) {
        highlightKey(e.code, false);
    });

    document.querySelectorAll('.word-count-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.word-count-btn').forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            if (!startTime) {
                if (resultInline) resultInline.hidden = true;
                timerEl.textContent = '0:00';
                wpmEl.textContent = '0';
                accuracyEl.textContent = '—';
                renderWords(function () { typingInput.focus(); });
            }
        });
    });

    if (btnRestart) btnRestart.addEventListener('click', resetTest);

    if (btnCloseResult) btnCloseResult.addEventListener('click', resetTest);

    buildVisualKeyboard();
    renderWords(function () {
        typingInput.focus();
    });
})();
