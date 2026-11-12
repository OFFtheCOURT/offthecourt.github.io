# Offcourt · páginas por partido para compartir y para buscadores (las llama build2.py)
# p/<liga>/<id>.html : título, descripción, datos del partido y vista previa propia (og:image)
# p/<liga>/<id>.jpg  : imagen 1200x630 con escudos, marcador y MVP (WhatsApp, X, Telegram, Facebook...)
# sitemap.xml y robots.txt
import os, json, html, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SITE = 'https://offthecourt.github.io'
LGN = {'nba': 'NBA', 'el': 'EuroLiga', 'acb': 'Liga ACB'}
LOGODIR = {'nba': 't', 'el': 'el', 'acb': 'acb'}
VER = 4   # súbelo para regenerar todas las imágenes

def _font(S, name, size):
    try: return ImageFont.truetype(os.path.join(S, 'redes', 'fuentes', name), size)
    except Exception: return ImageFont.load_default()

def _hex(h):
    h = (h or '333333').lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _lum(c): return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255

def _team_col(t):
    c = _hex(t.get('color')); return (42, 47, 58) if _lum(c) < 0.04 else c

def _mvp(g):
    tops = [p for t in g['teams'] for p in t.get('top', [])]
    return max(tops, key=lambda p: p.get('gs', p.get('val', 0)) or 0) if tops else None

def image(S, B, lk, L, g, out):
    W, H = 1200, 630; A, Hm = g['teams']; ta, th = L['teams'][A['abbr']], L['teams'][Hm['abbr']]
    im = Image.new('RGB', (W, H), (7, 11, 19)); d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (W * .6, 0), (W * .4, H), (0, H)], fill=_team_col(ta))
    d.polygon([(W * .6, 0), (W, 0), (W, H), (W * .4, H)], fill=_team_col(th))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(-H, W, 30): od.line([(k, H), (k + H * .45, 0)], fill=(255, 255, 255, 18), width=4)
    im = Image.alpha_composite(im.convert('RGBA'), ov)
    # viñeta
    vg = Image.new('L', (W, H), 0); vd = ImageDraw.Draw(vg); vd.ellipse((-200, -260, W + 200, H + 260), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(120)); dark = Image.new('RGBA', (W, H), (5, 8, 14, 215)); dark.putalpha(Image.eval(vg, lambda v: 215 - int(v * .75)))
    im = Image.alpha_composite(im, dark); d = ImageDraw.Draw(im)
    FD = lambda s: _font(S, 'bigs900.ttf', s); FL = lambda s: _font(S, 'barlowc700.ttf', s)
    # cabecera
    d.text((48, 40), 'OFF', font=FD(52), fill='white'); w0 = d.textlength('OFF', font=FD(52)); d.text((48 + w0, 40), 'COURT', font=FD(52), fill=(255, 122, 26))
    when = g.get('_when', '')
    d.text((W - 48, 46), f"{LGN[lk].upper()}{(' · ' + when) if when else ''}", font=FL(30), fill=(255, 255, 255, 220), anchor='ra')
    ot = len(A.get('ls', [])) > 4; diff = abs(A['score'] - Hm['score'])
    tag = 'FINAL · PRÓRROGA' if ot else (f'FINAL · PALIZA +{diff}' if diff >= 20 else ('FINAL · AL LÍMITE' if diff <= 3 else 'FINAL'))
    tw = d.textlength(tag, font=FL(28)) + 44; d.rounded_rectangle((W / 2 - tw / 2, 108, W / 2 + tw / 2, 154), 23, fill=(255, 122, 26)); d.text((W / 2, 131), tag, font=FL(28), fill=(26, 11, 2), anchor='mm')
    for s, t, cx in ((A, ta, W * .25), (Hm, th, W * .75)):
        f = os.path.join(B, 'img', LOGODIR[lk], s['abbr'] + '.webp')
        if os.path.exists(f):
            lg = Image.open(f).convert('RGBA'); lg.thumbnail((170, 170)); sh = Image.new('RGBA', lg.size, (0, 0, 0, 0)); sh.putalpha(lg.split()[3].point(lambda v: v * .5))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (int(cx - lg.width / 2) + 4, 178 + 8)); im.alpha_composite(lg, (int(cx - lg.width / 2), 178))
        win = s['score'] > (Hm['score'] if s is A else A['score']); col = (255, 255, 255) if win else (205, 210, 220)
        nm = t['short'].upper(); fs = 46 if len(nm) <= 10 else (38 if len(nm) <= 14 else 32)
        d.text((cx, 382), nm, font=FD(fs), fill=col, anchor='mm')
        d.text((cx, 480), str(s['score']), font=FD(150), fill=col if win else (190, 196, 208), anchor='mm')
        if win: d.rounded_rectangle((cx - 50, 548, cx + 50, 556), 4, fill=(255, 122, 26))
    d.text((W / 2, 470), '–', font=FD(100), fill=(255, 255, 255, 140), anchor='mm')
    p = _mvp(g)
    if p:
        line = f"MVP: {p['n']} · {p['pts']} PTS · {p['reb']} REB · {p['ast']} AST"
        d.text((W / 2, 596), line.upper(), font=FL(28), fill=(255, 210, 120), anchor='mm')
    im.convert('RGB').save(out, 'JPEG', quality=80, optimize=True, progressive=True)

def page(lk, L, g, img_rel):
    A, Hm = g['teams']; ta, th = L['teams'][A['abbr']], L['teams'][Hm['abbr']]
    p = _mvp(g); ot = len(A.get('ls', [])) > 4
    title = f"{ta['short']} {A['score']}-{Hm['score']} {th['short']}{' (prórroga)' if ot else ''} · {LGN[lk]} · Offcourt"
    desc = f"{ta['name']} {A['score']} - {Hm['score']} {th['name']}, {LGN[lk]}{(', ' + g['_when']) if g.get('_when') else ''}."
    if p: desc += f" MVP: {p['n']} ({p['pts']} puntos, {p['reb']} rebotes, {p['ast']} asistencias). Estadísticas completas, jugadores y resumen en Offcourt."
    url = f"{SITE}/p/{lk}/{g['id']}.html"; app = f"{SITE}/#partido/{lk}/{g['id']}"; img = f"{SITE}/{img_rel}"
    E = html.escape
    tops = ''.join(f"<li>{E(x['n'])} ({E(t['abbr'])}): {x['pts']} pts, {x['reb']} reb, {x['ast']} ast</li>" for t in g['teams'] for x in t.get('top', [])[:3])
    ld = {"@context": "https://schema.org", "@type": "SportsEvent", "name": f"{ta['name']} vs {th['name']}", "sport": "Basketball",
          "startDate": g.get('utc') or g.get('_day', ''), "eventStatus": "https://schema.org/EventScheduled",
          "homeTeam": {"@type": "SportsTeam", "name": (th if lk == 'nba' else ta)['name']}, "awayTeam": {"@type": "SportsTeam", "name": (ta if lk == 'nba' else th)['name']},
          "location": {"@type": "Place", "name": g.get('venue') or ''}, "url": url, "image": img, "description": desc}
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Offcourt"><meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#070b13"><link rel="icon" href="/icons/icon-192.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script>location.replace({json.dumps(app)})</script>
<style>body{{font-family:system-ui,sans-serif;background:#070b13;color:#f4f7fc;max-width:640px;margin:40px auto;padding:0 16px}}a{{color:#ff9a4a}}img{{max-width:100%;border-radius:12px}}</style></head>
<body><h1>{E(ta['short'])} {A['score']} - {Hm['score']} {E(th['short'])}</h1><p>{E(desc)}</p><img src="{img}" alt="{E(title)}"><ul>{tops}</ul>
<p><a href="{app}">Ver el partido en Offcourt</a></p></body></html>"""

def build(S, B, LEAGUES):
    os.makedirs(os.path.join(S, 'p'), exist_ok=True); urls = [(SITE + '/', None)]; n_img = 0; n = 0
    for lk, L in LEAGUES.items():
        d = os.path.join(S, 'p', lk); os.makedirs(d, exist_ok=True)
        for per in L.get('periods', []):
            for g in per['games']:
                g = dict(g); day = per.get('key') if lk == 'nba' else None
                if lk != 'nba': g['teams'] = g['teams'][::-1]   # en Europa, el local primero (izquierda)
                try:
                    if g.get('utc'): dt = datetime.datetime.fromisoformat(g['utc'].replace('Z', '+00:00')).astimezone(datetime.timezone(datetime.timedelta(hours=1)))
                    else: dt = datetime.datetime.fromisoformat(day)
                    MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']
                    g['_when'] = f"{dt.day} {MES[dt.month - 1]} {dt.year}"; g['_day'] = (day or dt.date().isoformat())
                except Exception: g['_when'] = ''
                img_rel = f"p/{lk}/{g['id']}.jpg"; img = os.path.join(S, img_rel); stamp = img + '.v'
                if not os.path.exists(img) or not os.path.exists(stamp) or open(stamp).read() != str(VER):
                    try: image(S, B, lk, L, g, img); open(stamp, 'w').write(str(VER)); n_img += 1
                    except Exception as e: print('og: sin imagen', g['id'], e)
                open(os.path.join(d, g['id'] + '.html'), 'w', encoding='utf-8').write(page(lk, L, g, img_rel)); n += 1
                urls.append((f"{SITE}/p/{lk}/{g['id']}.html", g.get('_day')))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = datetime.date.today().isoformat()
    for u, day in urls: sm.append(f'<url><loc>{u}</loc><lastmod>{day or today}</lastmod>{"<changefreq>hourly</changefreq><priority>1.0</priority>" if day is None else ""}</url>')
    sm.append('</urlset>'); open(os.path.join(S, 'sitemap.xml'), 'w').write('\n'.join(sm))
    open(os.path.join(S, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    print('páginas de partido', n, '· imágenes nuevas', n_img)
