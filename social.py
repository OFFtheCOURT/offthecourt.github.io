# Offcourt · paquete diario para redes (NBA): carrusel 1080x1350, vídeo vertical 1080x1920 y texto
# Uso: python3 social.py  -> crea la carpeta contenido/ con las imágenes, el vídeo y el texto
import os, re, json, base64, datetime, subprocess, shutil, html as H
S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, 'contenido'); os.makedirs(OUT, exist_ok=True)
SITE = os.environ.get('OFFCOURT_URL', 'martisosa.github.io/OFFCOURT')
HANDLE = os.environ.get('OFFCOURT_HANDLE', '@offcourt')

src = open(os.path.join(S, 'index.html'), encoding='utf-8').read()
i = src.find('const LG = '); j = src.find(';\nconst UPDATED', i)
LG = json.loads(src[i + 11:j])
i = src.find('const IMG = '); j = src.find(';\n', i)
IMG = json.loads(src[i + 12:j])
m = re.search(r'<div class="logo-slot" id="logoSlot">(<svg.*?</svg>)', src, flags=re.S)
OFFLOGO = m.group(1) if m else ''

L = LG['nba']; T = L['teams']; night = L['periods'][0]; games = night['games']
logo = lambda ab: IMG['t']['nba'].get(ab, '')
photo = lambda pid: IMG['p'].get(pid, '')
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
d = datetime.date.fromisoformat(night['key'])
FECHA = f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]}"
FECHA_C = f"{d.day} {MESES[d.month - 1][:3].upper()}"

def lum(h): n = int(h, 16); return (0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255)) / 255
def tc(t): return '#2a2f3a' if lum(t['color']) < 0.04 else '#' + t['color']
def ink(t):
    if lum(t['color']) > 0.28: return '#' + t['color']
    if lum(t['alt']) > 0.28 and t['alt'].lower() != 'ffffff': return '#' + t['alt']
    return '#' + t['color'] if lum(t['color']) > 0.12 else '#c4ced4'
def ini(n): return ''.join(w[0] for w in n.split()[:2])
e = H.escape

# ---- datos de la noche ----
P = []
for g in games:
    for s in g['teams']:
        opp = next(x for x in g['teams'] if x is not s)
        for p in s['top']: P.append({**p, 'abbr': s['abbr'], 'opp': opp['abbr'], 'win': s['win']})
P.sort(key=lambda p: -p['gs'])
mvp = P[0]
diff = lambda g: abs(g['teams'][0]['score'] - g['teams'][1]['score'])
tot = sum(g['teams'][0]['score'] + g['teams'][1]['score'] for g in games)
sc = lambda g: -diff(g) + (8 if len(g['teams'][0]['ls']) > 4 else 0) + (g['teams'][0]['score'] + g['teams'][1]['score']) / 60
potn = sorted(games, key=sc, reverse=True)[0]
blow = max(games, key=diff); close = min(games, key=diff)
by = lambda k: max(P, key=lambda p: p[k])
tonight = (L.get('upcoming') or [{}])[0].get('games', [])

def madrid(utc):
    t = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
    try:
        from zoneinfo import ZoneInfo; t = t.astimezone(ZoneInfo('Europe/Madrid'))
    except Exception: t = t + datetime.timedelta(hours=1)
    return t.strftime('%H:%M')

# ---- plantilla HTML de las diapositivas ----
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#05080f;font-family:'Barlow',sans-serif;color:#f4f7fc}
.s{width:1080px;height:1350px;position:relative;overflow:hidden;display:flex;flex-direction:column;padding:70px 70px 60px;
  background:radial-gradient(900px 600px at 0% 0%,rgba(255,110,26,.28),transparent 60%),radial-gradient(900px 700px at 100% 100%,rgba(56,110,255,.22),transparent 60%),#070b13}
.s::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(112deg,rgba(255,255,255,.025) 0 2px,transparent 2px 18px);pointer-events:none}
.court{position:absolute;inset:0;opacity:.06;pointer-events:none}
.top{display:flex;align-items:center;justify-content:space-between;position:relative;z-index:2}
.brand{display:flex;align-items:center;gap:16px}
.brand .lg{width:74px;height:74px}.brand .lg svg{width:100%;height:100%}
.brand b{font:900 46px/1 'Big Shoulders Display';letter-spacing:.01em;text-transform:uppercase}.brand b span{color:#ff7a1a}
.tag{font:800 24px 'Barlow Condensed';letter-spacing:.2em;text-transform:uppercase;color:#1a0b02;background:linear-gradient(100deg,#ff5a1f,#ff8a1a 45%,#ffc04d);padding:8px 22px;transform:skewX(-12deg);border-radius:4px}
.tag i{display:inline-block;font-style:normal;transform:skewX(12deg)}
h1{font:900 150px/.86 'Big Shoulders Display';text-transform:uppercase;margin-top:40px;position:relative;z-index:2}
h1 em,h2 em{font-style:italic;background:linear-gradient(100deg,#ff5a1f,#ff8a1a 45%,#ffc04d);-webkit-background-clip:text;background-clip:text;color:transparent;padding-right:.05em}
h2{font:900 104px/.9 'Big Shoulders Display';text-transform:uppercase;margin:34px 0 28px;position:relative;z-index:2}
.sub{font:600 34px 'Barlow Condensed';letter-spacing:.06em;color:#a3afc4;margin-top:16px;position:relative;z-index:2}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font:700 26px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;color:#a3afc4;position:relative;z-index:2}
.foot b{color:#ffb15c}
.hero{margin-top:46px;border-radius:36px;overflow:hidden;position:relative;z-index:2;padding:40px 30px 34px;border:2px solid rgba(255,255,255,.12)}
.hero .bg{position:absolute;inset:0}
.hero .row{position:relative;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;text-align:center}
.hero img{width:210px;height:210px;object-fit:contain;filter:drop-shadow(0 14px 24px rgba(0,0,0,.5))}
.hero .tn{font:900 46px/1 'Big Shoulders Display';text-transform:uppercase;margin-top:10px}
.hero .sc{font:900 150px/.85 'Big Shoulders Display';white-space:nowrap}
.hero .sc .lo{color:rgba(255,255,255,.45)}
.hero .lbl{position:relative;text-align:center;margin-bottom:18px}
.chips{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:26px;position:relative;z-index:2}
.chip{border-radius:24px;padding:20px 22px;background:linear-gradient(180deg,#19233a,#121a2a);border:2px solid #26324d}
.chip .l{font:800 20px 'Barlow Condensed';letter-spacing:.18em;text-transform:uppercase;color:#a3afc4}
.chip .v{font:900 64px/1 'Big Shoulders Display';margin-top:6px;background:linear-gradient(100deg,#ff5a1f,#ff8a1a 45%,#ffc04d);-webkit-background-clip:text;background-clip:text;color:transparent}
.chip .n{font:700 24px 'Barlow Condensed';color:#d6deea;margin-top:4px;display:flex;align-items:center;gap:8px;white-space:nowrap;overflow:hidden}
.chip .n img{width:34px;height:34px;object-fit:contain}
.res{display:grid;gap:12px;position:relative;z-index:2}
.rg{display:grid;grid-template-columns:1fr 1fr;border-radius:22px;overflow:hidden;border:2px solid #26324d;background:#121a2a}
.rt{display:flex;align-items:center;gap:14px;padding:22px 20px 10px;position:relative}
.rt.h{flex-direction:row-reverse;text-align:right}
.rt img{width:60px;height:60px;object-fit:contain}
.rt .n{font:900 34px/1 'Big Shoulders Display';text-transform:uppercase;flex:1;min-width:0}
.rt .p{font:900 60px/1 'Big Shoulders Display';color:#6b7893}
.rt.w .p{color:#fff}.rt.w .n{color:#fff}.rt:not(.w) .n{color:#a3afc4}
.rt.w{background:linear-gradient(90deg,var(--c),transparent 85%)}.rt.h.w{background:linear-gradient(270deg,var(--c),transparent 85%)}
.bd{position:absolute;top:4px;z-index:3;font:800 16px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;padding:2px 10px;border-radius:99px}
.mvp{flex:1;margin-top:10px;border-radius:40px;position:relative;z-index:2;overflow:hidden;border:2px solid rgba(255,255,255,.14)}
.mvp .bg{position:absolute;inset:0}
.mvp .ph{position:absolute;right:-30px;bottom:0;width:640px;height:466px;object-fit:cover;-webkit-mask-image:linear-gradient(to right,transparent,#000 40%)}
.mvp .ini{position:absolute;right:60px;top:120px;width:380px;height:380px;border-radius:50%;display:grid;place-items:center;font:900 190px 'Big Shoulders Display';background:rgba(255,255,255,.12);border:6px solid rgba(255,255,255,.25)}
.mvp .num{position:absolute;right:40px;bottom:-60px;font:900 460px/1 'Big Shoulders Display';color:rgba(255,255,255,.08)}
.mvp .in{position:relative;padding:50px 54px;display:flex;flex-direction:column;height:100%}
.mvp .tl{width:130px;height:130px;object-fit:contain}
.mvp .nm{font:900 112px/.88 'Big Shoulders Display';text-transform:uppercase;margin-top:auto;max-width:640px}
.mvp .vs{font:700 32px 'Barlow Condensed';letter-spacing:.08em;color:rgba(255,255,255,.85);margin-top:14px;text-transform:uppercase}
.stats{display:flex;gap:40px;margin-top:34px}
.stats div{display:flex;flex-direction:column}
.stats b{font:900 150px/.85 'Big Shoulders Display'}
.stats div:first-child b{color:#ffc04d}
.stats small{font:800 28px 'Barlow Condensed';letter-spacing:.2em;color:rgba(255,255,255,.75)}
.top5{display:grid;gap:16px;position:relative;z-index:2}
.t5{display:grid;grid-template-columns:70px 120px 1fr auto;align-items:center;gap:22px;border-radius:24px;padding:14px 26px 14px 18px;background:linear-gradient(90deg,var(--c) 0%,#121a2a 60%);border:2px solid #26324d}
.t5 .r{font:900 70px/1 'Big Shoulders Display';color:rgba(255,255,255,.55);text-align:center}
.t5 .av{width:120px;height:120px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:rgba(255,255,255,.12);font:900 50px 'Big Shoulders Display'}
.t5 .av img{width:164px;height:120px;object-fit:cover}
.t5 .n{font:900 46px/.95 'Big Shoulders Display';text-transform:uppercase}
.t5 .t{font:700 24px 'Barlow Condensed';letter-spacing:.12em;color:#a3afc4;margin-top:6px;display:flex;align-items:center;gap:8px}
.t5 .t img{width:34px;height:34px}
.t5 .v{display:flex;gap:22px;text-align:center}
.t5 .v b{display:block;font:900 64px/1 'Big Shoulders Display'}
.t5 .v b.hot{color:#ffc04d}
.t5 .v small{font:800 18px 'Barlow Condensed';letter-spacing:.16em;color:#a3afc4}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:20px;position:relative;z-index:2}
.f{border-radius:28px;padding:30px 30px 26px;background:linear-gradient(180deg,#19233a,#121a2a);border:2px solid #26324d;display:flex;flex-direction:column;gap:10px}
.f .l{font:800 24px 'Barlow Condensed';letter-spacing:.18em;text-transform:uppercase;color:#a3afc4}
.f .v{font:900 120px/.9 'Big Shoulders Display'}
.f .v.hot{background:linear-gradient(100deg,#ff5a1f,#ff8a1a 45%,#ffc04d);-webkit-background-clip:text;background-clip:text;color:transparent}
.f .w{display:flex;align-items:center;gap:12px;font:700 30px 'Barlow Condensed';letter-spacing:.04em;color:#d6deea}
.f .w img{width:48px;height:48px;object-fit:contain}
.up{display:grid;gap:14px;position:relative;z-index:2}
.u{display:grid;grid-template-columns:150px 1fr auto 1fr;align-items:center;gap:16px;border-radius:22px;padding:14px 22px;background:#121a2a;border:2px solid #26324d}
.u .h{font:900 60px/1 'Big Shoulders Display';color:#ffc04d}
.u .tm{display:flex;align-items:center;gap:14px;font:900 36px 'Big Shoulders Display';text-transform:uppercase}
.u .tm.r{flex-direction:row-reverse;text-align:right}
.u .tm img{width:66px;height:66px;object-fit:contain}
.u .at{font:900 36px 'Big Shoulders Display';color:#6b7893}
.cta{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;gap:30px;position:relative;z-index:2}
.cta .lg{width:300px;height:300px}.cta .lg svg{width:100%;height:100%}
.cta b{font:900 120px/.9 'Big Shoulders Display';text-transform:uppercase}
.cta b span{color:#ff7a1a}
.cta p{font:700 44px 'Barlow Condensed';letter-spacing:.06em;color:#d6deea}
.cta .url{font:800 40px 'Barlow Condensed';letter-spacing:.06em;color:#1a0b02;background:linear-gradient(100deg,#ff5a1f,#ff8a1a 45%,#ffc04d);padding:14px 34px;border-radius:999px}
"""
COURT = """<svg class="court" viewBox="0 0 1080 1350" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="#fff" stroke-width="5"><circle cx="540" cy="675" r="170"/><path d="M0 675H1080"/><path d="M200 0v200a340 340 0 0 0 680 0V0"/><path d="M200 1350v-200a340 340 0 0 1 680 0v200"/></g></svg>"""
def top(tag): return f'<div class="top"><div class="brand"><span class="lg">{OFFLOGO}</span><b>Off<span>court</span></b></div><span class="tag"><i>{tag}</i></span></div>'
def foot(n, total): return f'<div class="foot"><span>{e(HANDLE)} · <b>{e(SITE)}</b></span><span>{n}/{total}</span></div>'

slides = []
# 1 portada
A, Hm = potn['teams']; ta, th = T[A['abbr']], T[Hm['abbr']]
slides.append(lambda n, N: f"""<div class="s">{COURT}{top('NBA · ' + FECHA_C)}
<h1>Noche<br><em>NBA</em></h1><div class="sub">{e(FECHA)} · {len(games)} partidos · {tot} puntos</div>
<div class="hero"><div class="bg" style="background:linear-gradient(112deg,{tc(ta)} 0 49.6%,{tc(th)} 50.4% 100%)"></div>
<div class="lbl"><span class="tag"><i>Partido de la noche</i></span></div>
<div class="row"><div><img src="{logo(A['abbr'])}"><div class="tn">{e(ta['short'])}</div></div>
<div class="sc"><span class="{'' if A['win'] else 'lo'}">{A['score']}</span>–<span class="{'' if Hm['win'] else 'lo'}">{Hm['score']}</span></div>
<div><img src="{logo(Hm['abbr'])}"><div class="tn">{e(th['short'])}</div></div></div></div>
<div class="chips"><div class="chip"><div class="l">MVP</div><div class="v">{mvp['pts']} pts</div><div class="n"><img src="{logo(mvp['abbr'])}">{e(mvp['n'].split()[-1])}</div></div>
<div class="chip"><div class="l">Máx. anotador</div><div class="v">{by('pts')['pts']} pts</div><div class="n"><img src="{logo(by('pts')['abbr'])}">{e(by('pts')['n'].split()[-1])}</div></div>
<div class="chip"><div class="l">Mayor paliza</div><div class="v">+{diff(blow)}</div><div class="n"><img src="{logo(next(x for x in blow['teams'] if x['win'])['abbr'])}">{e(T[next(x for x in blow['teams'] if x['win'])['abbr']]['short'])}</div></div></div>
{foot(n, N)}</div>""")
# 2 resultados
def badge(g):
    dd = diff(g)
    if len(g['teams'][0]['ls']) > 4: return '<span class="bd" style="left:50%;transform:translateX(-50%);background:rgba(120,150,255,.25);color:#b9c9ff">Prórroga</span>'
    if dd >= 20: return f'<span class="bd" style="left:50%;transform:translateX(-50%);background:rgba(255,93,108,.2);color:#ff9aa3">Paliza +{dd}</span>'
    if dd <= 5: return f'<span class="bd" style="left:50%;transform:translateX(-50%);background:rgba(61,220,151,.2);color:#7ff0bd">Igualado</span>'
    return ''
def rrow(g):
    a, h = g['teams']
    def side(s, cls):
        t = T[s['abbr']]
        return f'<div class="rt {cls} {"w" if s["win"] else ""}" style="--c:{tc(t)}"><img src="{logo(s["abbr"])}"><span class="n">{e(t["short"])}</span><span class="p">{s["score"]}</span></div>'
    return f'<div class="rg" style="position:relative">{side(a, "a")}{side(h, "h")}{badge(g)}</div>'
slides.append(lambda n, N: f"""<div class="s">{COURT}{top('Resultados')}<h2>Los <em>resultados</em></h2>
<div class="res">{''.join(rrow(g) for g in games[:8])}</div>{foot(n, N)}</div>""")
# 3 MVP
tm = T[mvp['abbr']]; ph = photo(mvp['pid'])
slides.append(lambda n, N: f"""<div class="s">{COURT}{top('MVP de la noche')}
<div class="mvp"><div class="bg" style="background:linear-gradient(150deg,{tc(tm)},#070b13 85%)"></div><span class="num">{e(mvp['num'])}</span>
{f'<img class="ph" src="{ph}">' if ph else f'<span class="ini">{ini(mvp["n"])}</span>'}
<div class="in"><img class="tl" src="{logo(mvp['abbr'])}"><div class="nm">{e(mvp['n'])}</div>
<div class="vs">{e(tm['short'])} {'gana a' if mvp['win'] else 'cae ante'} {e(T[mvp['opp']]['short'])} · {mvp['min']} min</div>
<div class="stats"><div><b>{mvp['pts']}</b><small>PUNTOS</small></div><div><b>{mvp['reb']}</b><small>REBOTES</small></div><div><b>{mvp['ast']}</b><small>ASIST.</small></div></div></div></div>
{foot(n, N)}</div>""")
# 4 top 5
def t5(i, p):
    t = T[p['abbr']]; ph = photo(p['pid'])
    return f"""<div class="t5" style="--c:{tc(t)}"><span class="r">{i}</span><span class="av">{f'<img src="{ph}">' if ph else ini(p['n'])}</span>
<div><div class="n">{e(p['n'])}</div><div class="t"><img src="{logo(p['abbr'])}">{e(t['short'])} · {p['fg']} TC</div></div>
<div class="v"><div><b class="hot">{p['pts']}</b><small>PTS</small></div><div><b>{p['reb']}</b><small>REB</small></div><div><b>{p['ast']}</b><small>AST</small></div></div></div>"""
slides.append(lambda n, N: f"""<div class="s">{COURT}{top('Top 5')}<h2>Los <em>mejores</em></h2>
<div class="top5">{''.join(t5(i + 1, p) for i, p in enumerate(P[:5]))}</div>{foot(n, N)}</div>""")
# 5 cifras
def gf(lbl, g, v):
    w = next(x for x in g['teams'] if x['win']); l = next(x for x in g['teams'] if not x['win'])
    return f'<div class="f"><span class="l">{lbl}</span><span class="v">{v}</span><span class="w"><img src="{logo(w["abbr"])}">{w["score"]}-{l["score"]}<img src="{logo(l["abbr"])}"></span></div>'
def pf(lbl, p, k, u):
    return f'<div class="f"><span class="l">{lbl}</span><span class="v hot">{p[k]}<span style="font-size:40px;color:#a3afc4;-webkit-text-fill-color:#a3afc4"> {u}</span></span><span class="w"><img src="{logo(p["abbr"])}">{e(p["n"])}</span></div>'
slides.append(lambda n, N: f"""<div class="s">{COURT}{top('Cifras')}<h2>La noche en <em>cifras</em></h2>
<div class="facts">{pf('Máximo anotador', by('pts'), 'pts', 'PTS')}{pf('Más rebotes', by('reb'), 'reb', 'REB')}{pf('Más asistencias', by('ast'), 'ast', 'AST')}
<div class="f"><span class="l">Puntos totales</span><span class="v">{tot}</span><span class="w">{len(games)} partidos · {tot / len(games) / 2:.0f} por equipo</span></div>
{gf('Mayor paliza', blow, '+' + str(diff(blow)))}{gf('Más igualado', close, str(diff(close)) + ' pts')}</div>{foot(n, N)}</div>""")
# 6 esta noche
if tonight:
    def urow(g):
        a, h = g['teams']
        return f"""<div class="u"><span class="h">{madrid(g['utc'])}</span><span class="tm"><img src="{logo(a['abbr'])}">{e(T[a['abbr']]['short'])}</span><span class="at">@</span>
<span class="tm r"><img src="{logo(h['abbr'])}">{e(T[h['abbr']]['short'])}</span></div>"""
    slides.append(lambda n, N: f"""<div class="s">{COURT}{top('Esta noche')}<h2>Esta noche <em>se juega</em></h2>
<div class="sub" style="margin:-10px 0 24px">Hora de España</div><div class="up">{''.join(urow(g) for g in tonight[:9])}</div>{foot(n, N)}</div>""")
# 7 cierre (solo vídeo)
cta = f"""<div class="s">{COURT}<div class="cta"><span class="lg">{OFFLOGO}</span><b>Off<span>court</span></b>
<p>Resultados, estadísticas y directo<br>de NBA, EuroLiga y ACB</p><span class="url">{e(SITE)}</span><p style="font-size:34px;color:#a3afc4">Síguenos {e(HANDLE)}</p></div></div>"""

N = len(slides)
body = ''.join(f'<div class="wrap" id="s{k + 1}">{f(k + 1, N)}</div>' for k, f in enumerate(slides)) + f'<div class="wrap" id="s{N + 1}">{cta}</div>'
page = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Barlow:wght@500;600;700&family=Barlow+Condensed:wght@600;700;800&display=block" rel="stylesheet">
<style>{CSS}.wrap{{width:1080px;height:1350px}}</style></head><body>{body}</body></html>"""
open(os.path.join(OUT, 'slides.html'), 'w', encoding='utf-8').write(page)

# ---- capturas con Playwright ----
JS = '''const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1350}});
await p.goto('file://'+process.argv[1]+'/slides.html');await p.waitForTimeout(2500);await p.evaluate(()=>document.fonts.ready);
for(let k=1;k<=+process.argv[2];k++){await p.locator('#s'+k).screenshot({path:process.argv[1]+'/slide'+k+'.png'});}await b.close()})();'''
subprocess.run(['node', '-e', JS, OUT, str(N + 1)], check=True)

# ---- vídeo vertical 1080x1920 (≈3 s por diapositiva, fundidos) ----
from PIL import Image, ImageDraw
frames = []
for k in range(N + 1):
    bg = Image.new('RGB', (1080, 1920), (7, 11, 19))
    g = Image.open(os.path.join(OUT, f'slide{k + 1}.png')).convert('RGB')
    bg.paste(g, (0, (1920 - 1350) // 2))
    dr = ImageDraw.Draw(bg)
    dr.rectangle((0, 0, 1080, 285), fill=(7, 11, 19)); dr.rectangle((0, 1635, 1080, 1920), fill=(7, 11, 19))
    p = os.path.join(OUT, f'v{k + 1}.png'); bg.save(p); frames.append(p)
D, F = 3.2, 0.45
inputs = []
for p in frames: inputs += ['-loop', '1', '-t', str(D), '-i', p]
fl = []; last = '[0:v]'
for k in range(1, len(frames)):
    off = round(k * (D - F), 2)
    fl.append(f'{last}[{k}:v]xfade=transition=slideleft:duration={F}:offset={off}[x{k}]'); last = f'[x{k}]'
fl.append(f'{last}format=yuv420p,fps=30[out]')
cmd = ['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', ';'.join(fl), '-map', '[out]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', os.path.join(OUT, 'video_nba.mp4')]
subprocess.run(cmd, check=True)
for p in frames: os.remove(p)
os.rename(os.path.join(OUT, f'slide{N + 1}.png'), os.path.join(OUT, 'cierre.png'))

# ---- texto para publicar ----
lines = [f"🏀 NOCHE NBA · {FECHA}", ""]
for g in games:
    a, h = g['teams']; w = a if a['win'] else h; l = h if w is a else a
    lines.append(f"{T[w['abbr']]['short']} {w['score']}-{l['score']} {T[l['abbr']]['short']}")
lines += ["", f"⭐ MVP: {mvp['n']} ({T[mvp['abbr']]['short']}) · {mvp['pts']} pts, {mvp['reb']} reb, {mvp['ast']} ast",
          f"🔥 Mayor paliza: +{diff(blow)} · ⚖️ Más igualado: {diff(close)} pts", "",
          f"📊 Todas las estadísticas en {SITE}", "", "#NBA #NBAenEspañol #Baloncesto #Basket #Offcourt"]
open(os.path.join(OUT, 'texto.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('ok', N, 'diapositivas')
