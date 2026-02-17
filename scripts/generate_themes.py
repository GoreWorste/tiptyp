# -*- coding: utf-8 -*-
"""Генерация CSS для тем dark6-50 и light6-50."""
import os

def hsl(h, s, l):
    return 'hsl({}, {}%, {}%)'.format(round(h), round(s), round(l))

def rgba_from_hsl(h, s, l, a):
    # Упрощённая конвертация HSL -> RGB для rgba
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0
    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return 'rgba({}, {}, {}, {})'.format(round(r*255), round(g*255), round(b*255), a)

out = []
# Тёмные темы 6-50: оттенок акцента по кругу, тёмный фон
for i in range(6, 51):
    hue = (i * 137) % 360  # золотой угол для разнообразия
    sat_accent = 55 + (i % 3) * 10
    light_accent = 45 + (i % 5) * 6
    bg_light = 10 + (i % 7)
    out.append('''[data-theme="dark{}"] {{
    --bg: hsl({}, 12%, {}%);
    --bg-sub: hsl({}, 10%, {}%);
    --surface: hsl({}, 11%, {}%);
    --text: hsl(0, 0%, 88%);
    --text-muted: hsl(0, 0%, 58%);
    --accent: hsl({}, {}%, {}%);
    --accent-dim: hsl({}, {}%, {}%);
    --success: #2ecc71;
    --error: #e74c3c;
    --on-accent: {};
    --success-bg: rgba(46, 204, 113, 0.2);
    --error-bg: rgba(231, 76, 60, 0.2);
    --success-bg-dim: rgba(46, 204, 113, 0.12);
    --accent-bg-dim: hsl({}, {}%, {}%);
    --overlay: rgba(0, 0, 0, 0.75);
    --shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}}'''.format(
        i, hue, bg_light, hue, bg_light + 4, hue, bg_light + 8,
        hue, sat_accent, light_accent, hue, sat_accent, max(30, light_accent - 12),
        '#1a1a1a' if light_accent > 50 else '#fff',
        hue, sat_accent, 20
    ))

# Светлые темы 6-50
for i in range(6, 51):
    hue = (i * 137 + 180) % 360
    sat_accent = 50 + (i % 4) * 12
    light_accent = 38 + (i % 4) * 5
    bg_light = 96 - (i % 5)
    out.append('''[data-theme="light{}"] {{
    --bg: hsl(0, 0%, {}%);
    --bg-sub: #ffffff;
    --surface: hsl(0, 0%, {}%);
    --text: hsl(0, 0%, 18%);
    --text-muted: hsl(0, 0%, 45%);
    --accent: hsl({}, {}%, {}%);
    --accent-dim: hsl({}, {}%, {}%);
    --success: #27ae60;
    --error: #c0392b;
    --on-accent: #fff;
    --success-bg: rgba(39, 174, 96, 0.15);
    --error-bg: rgba(192, 57, 43, 0.15);
    --success-bg-dim: rgba(39, 174, 96, 0.1);
    --accent-bg-dim: hsl({}, {}%, {}%);
    --overlay: rgba(0, 0, 0, 0.45);
    --shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}}'''.format(
        i, bg_light, bg_light - 8,
        hue, sat_accent, light_accent, hue, sat_accent, max(28, light_accent - 10),
        hue, 70, 92
    ))

css = '/* TipTyp — темы 6–50 (сгенерировано generate_themes.py) */\n\n' + '\n\n'.join(out)
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base, 'static', 'themes-extra.css')
with open(path, 'w', encoding='utf-8') as f:
    f.write(css)
print('Written', path)
