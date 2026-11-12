# Offcourt · vídeo resumen de la noche NBA v3 (vertical 1080x1920): voz en off, música a 128 BPM,
# cortes y golpes sincronizados con el ritmo, subtítulos palabra a palabra.
# Necesita: piper-tts (+ voz con alineación, ver tts_es.py), node + playwright, ffmpeg, numpy.
import os, re, json, wave, subprocess, datetime, html as H, shutil, math, random
import numpy as np
if os.environ.get('OFFCOURT_TTS', 'kokoro') == 'kokoro':
    from tts_kokoro import synth; SPEED = float(os.environ.get('OFFCOURT_SPEED', '1.15'))
else:
    from tts_es import synth; SPEED = 0.78
S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, 'contenido'); os.makedirs(OUT, exist_ok=True)
WORK = os.path.join(OUT, '_video'); shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK + '/f')
HANDLE = os.environ.get('OFFCOURT_HANDLE', '@offcourt')
FPS, SR = 24, 44100
BPM = 128; BEAT = 60 / BPM; BAR = BEAT * 4

# ================= datos =================
src = open(os.path.join(S, 'index.html'), encoding='utf-8').read()
i = src.find('const LG = '); j = src.find(';\nconst UPDATED', i); LG = json.loads(src[i + 11:j])
i = src.find('const IMG = '); j = src.find(';\n', i); IMG = json.loads(src[i + 12:j])
m = re.search(r'<div class="logo-slot" id="logoSlot">(<svg.*?</svg>)', src, flags=re.S); OFFLOGO = m.group(1) if m else ''
L = LG['nba']; T = L['teams']; night = L['periods'][0]; games = night['games']
logo = lambda ab: IMG['t']['nba'].get(ab, '')
def photo(pid):
    v = IMG['p'].get(pid, '')
    if v.startswith('photos/'):   # la web enlaza las fotos como archivos: se incrustan para el vídeo
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), v.split('?')[0])
        return 'data:image/webp;base64,' + __import__('base64').b64encode(open(f, 'rb').read()).decode() if os.path.exists(f) else ''
    return v
e = H.escape
def lum(h): n = int(h, 16); return (0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255)) / 255
def tc(t): return '#2a2f3a' if lum(t['color']) < 0.04 else '#' + t['color']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
d = datetime.date.fromisoformat(night['key']); FECHA = f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"
NUMW = {1: 'un', 2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco', 6: 'seis', 7: 'siete', 8: 'ocho', 9: 'nueve', 10: 'diez', 11: 'once', 12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince'}
nw = lambda n: NUMW.get(n, str(n))
short = lambda ab: T[ab]['short']
diff = lambda g: abs(g['teams'][0]['score'] - g['teams'][1]['score'])
Wn = lambda g: next(x for x in g['teams'] if x['win']); Ls = lambda g: next(x for x in g['teams'] if not x['win'])
allp = [(p, s['abbr'], g) for g in games for s in g['teams'] for p in s['top']]
mvp_pid = max(allp, key=lambda x: x[0]['gs'])[0]['pid']
tonight = (L.get('upcoming') or [{}])[0].get('games', [])
sc = lambda g: -diff(g) + (8 if len(g['teams'][0]['ls']) > 4 else 0) + (g['teams'][0]['score'] + g['teams'][1]['score']) / 60
mvp_game = next(g for g in games if any(p['pid'] == mvp_pid for s in g['teams'] for p in s['top']))
best = max(games, key=sc)
order = [best] + ([mvp_game] if mvp_game is not best else []) + sorted([g for g in games if g is not best and g is not mvp_game], key=lambda g: -sc(g))

# ================= guion: frases cortas y con energía =================
EN = lambda s: '⟦' + s + '⟧'
def pname(n, full=False):
    parts = n.split(); ln = parts[-1] if parts[-1] not in ('Jr.', 'II', 'III', 'IV', 'Sr.') or len(parts) < 2 else parts[-2]
    x = n if full else ln
    if re.search(r'(ic|ić|vic)$', ln.lower()) or any(ord(c) > 127 for c in n): return x
    return EN(x)
TEAM = lambda ab: EN(short(ab))
def kind(g):
    if len(g['teams'][0]['ls']) > 4: return 'ot'
    if diff(g) >= 20: return 'blow'
    if diff(g) <= 5: return 'close'
    return 'win'
KIND_TXT = {'ot': '¡Prórroga!', 'blow': '¡Paliza!', 'close': '¡Al límite!'}
def game_line(g):
    w, l = Wn(g), Ls(g)
    a = (KIND_TXT.get(kind(g), '') + ' ' if kind(g) != 'win' else '') + f"{TEAM(w['abbr'])} {w['score']}, {TEAM(l['abbr'])} {l['score']}."
    ws = w['top'][0]; ls_ = l['top'][0]
    extra = f" y {ws['reb']} rebotes" if ws['reb'] >= 10 else (f" y {ws['ast']} asistencias" if ws['ast'] >= 8 else '')
    b = f"¡Exhibición de {pname(ws['n'], True)}! {ws['pts']} puntos{extra}." if ws['pid'] == mvp_pid else f"{pname(ws['n'])}: {ws['pts']} puntos{extra}."
    c = f" ¡Los {ls_['pts']} de {pname(ls_['n'])} no bastaron!" if ls_['pts'] >= 40 else ''
    return a + ' ' + b + c
lines = [('intro', f"¡Buenos días! Esto es Offcourt. ¡Vamos con la noche {EN('NBA')}!")]
for k, g in enumerate(order): lines.append((f'g{k}', game_line(g)))
lines.append(('outro', (f"Esta noche, {nw(len(tonight))} partidos más. " if tonight else '') + "¡Síguenos!"))

# ================= voz y línea de tiempo cuantizada al ritmo =================
q = lambda x, u=BEAT: math.ceil(x / u - 1e-6) * u
timeline = []; t = 0.0
for k, (key, text) in enumerate(lines):
    wf = f'{WORK}/l{k}.wav'; dur, words, vsr = synth(text, wf, speed=SPEED)
    if key == 'intro': lead = BAR + BEAT * 0.5              # 1 compás de logos a toda velocidad antes de la voz
    elif key == 'outro': lead = BEAT * 0.5
    else: lead = BEAT * 0.75
    sdur = q(max(dur + lead + BEAT * 0.6, (BEAT * 8 if key.startswith('g') else BEAT * 6)), BEAT * 2)
    timeline.append({'key': key, 'start': round(t, 4), 'dur': round(sdur, 4), 'voice': round(t + lead, 4), 'wav': wf,
                     'text': re.sub(r'[⟦⟧]', '', text), 'words': [{**w_, 's': round(w_['s'] + t + lead, 3), 'e': round(w_['e'] + t + lead, 3)} for w_ in words]})
    t += sdur
TOTAL = round(t + BEAT, 3)

# ================= audio: voz + música 128 BPM + efectos sincronizados =================
N = int(TOTAL * SR); voice = np.zeros(N, np.float32)
for x in timeline:
    with wave.open(x['wav']) as f: a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32767; vsr = f.getframerate()
    a = np.interp(np.arange(0, len(a), vsr / SR), np.arange(len(a)), a)
    s0 = int(x['voice'] * SR); voice[s0:s0 + len(a)] += a[:N - s0]
rng = np.random.default_rng(11); tt = np.arange(N) / SR
music = np.zeros(N, np.float32); fx = np.zeros(N, np.float32)
def put(buf, sig, at, g=1.0):
    s0 = int(at * SR)
    if s0 < 0 or s0 >= N: return
    n = min(len(sig), N - s0); buf[s0:s0 + n] += sig[:n] * g
def lp(sig, a):
    out = np.zeros_like(sig); y = 0.0
    for k_ in range(len(sig)): y += a * (sig[k_] - y); out[k_] = y
    return out
X = lambda l: np.arange(int(l * SR)) / SR
def kick(): x = X(.3); f = 48 + 110 * np.exp(-x * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 8) * 1.1
def clap(): x = X(.2); n = rng.normal(0, 1, len(x)); return (n - lp(n, .15)) * np.exp(-x * 24) * .6
def hat(o=False): x = X(.18 if o else .04); n = rng.normal(0, 1, len(x)); return (n - lp(n, .5)) * np.exp(-x * (14 if o else 70)) * .3
def saw(fq, l, cut=.06, dec=4):
    x = X(l); s = 2 * ((x * fq) % 1) - 1 + 2 * ((x * fq * 1.006) % 1) - 1
    return lp(s, cut) * np.exp(-x * dec) * .5
def crash(): x = X(1.4); n = rng.normal(0, 1, len(x)); return (n - lp(n, .35)) * np.exp(-x * 3.2) * .35
def riser(l):
    x = X(l); n = rng.normal(0, 1, len(x)); out = np.zeros_like(n); y = 0.0
    for k_ in range(len(n)): a = 0.01 + 0.5 * (k_ / len(n)) ** 2; y += a * (n[k_] - y); out[k_] = y
    return out * (x / l) ** 1.5 * 1.2
def boom(): x = X(.7); return (np.sin(2 * np.pi * (38 + 70 * np.exp(-x * 18)) * x) * np.exp(-x * 5) + rng.normal(0, 1, len(x)) * np.exp(-x * 40) * .3)
def horn():
    x = X(.55); s = sum(np.sign(np.sin(2 * np.pi * f * x)) for f in (233, 294, 349)) / 3
    return lp(s, .2) * np.minimum(1, x / .02) * np.exp(-np.maximum(0, x - .35) * 18) * .45
def whoosh(l=.5):
    x = X(l); n = rng.normal(0, 1, len(x)); out = np.zeros_like(n); y = 0.0
    for k_ in range(len(n)): a = .02 + .3 * math.sin(math.pi * k_ / len(n)); y += a * (n[k_] - y); out[k_] = y
    return out * np.sin(np.pi * x / l)
KK, CL, HC, HO, CR, BM, HN = kick(), clap(), hat(), hat(True), crash(), boom(), horn()
PROG = [(55.0, (220.0, 261.6, 329.6)), (43.65, (174.6, 220.0, 261.6)), (65.41, (196.0, 261.6, 329.6)), (49.0, (196.0, 246.9, 293.7))]
BASS = {fq: saw(fq, BEAT * .45, .05, 6) for fq, _ in PROG}
STAB = {i_: sum(saw(c * 2, BEAT * .9, .12, 7) for c in ch) / 3 for i_, (_, ch) in enumerate(PROG)}
nbar = int(TOTAL / BAR) + 1
intro_end = timeline[0]['start'] + BAR                       # el primer compás: solo subida
for b in range(nbar):
    t0 = b * BAR; fq, _ = PROG[b % 4]
    for s16 in range(16):
        at = t0 + s16 * BEAT / 4
        if at < intro_end: continue
        if s16 % 4 == 0: put(music, KK, at, .95)
        if s16 in (4, 12): put(music, CL, at, .6)
        if s16 % 4 == 2: put(music, HO, at, .5)
        elif s16 % 2 == 1: put(music, HC, at, .35)
        if s16 % 2 == 0 and s16 % 4 != 0: put(music, BASS[fq], at, .55)
        if s16 % 4 == 0 and s16 != 0: put(music, BASS[fq], at + BEAT / 4, .35)
    if t0 >= intro_end: put(music, STAB[b % 4], t0, .28); put(music, STAB[b % 4], t0 + BEAT * 2.5, .18)
put(music, riser(BAR), 0, .7)
for x in timeline:
    put(fx, CR, x['start'], .8)
    if x['start'] > 0: put(fx, whoosh(.45), x['start'] - .3, .6); put(fx, riser(BEAT * 2), x['start'] - BEAT * 2, .35)
    if x['key'].startswith('g'): put(fx, BM, x['start'] + BEAT * 4, .7); put(fx, HN, x['start'] + BEAT * 4, .55)
for k_ in range(8): put(fx, boom()[:int(.2 * SR)] * .5, timeline[0]['start'] + k_ * BEAT / 2, .5)   # golpes del montaje de logos
env = np.convolve(np.abs(voice), np.ones(int(.1 * SR)) / int(.1 * SR), mode='same')
duck = 1 - 0.5 * np.clip(env * 6, 0, 1)
fade = np.clip((TOTAL - tt) / 1.0, 0, 1)
mix = voice * 1.05 + (music * 0.32 * duck + fx * 0.32) * fade
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.97
with wave.open(f'{WORK}/audio.wav', 'wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((mix * 32767).astype(np.int16).tobytes())

# ================= escenas =================
def face(p, abbr, size):
    ph = photo(p['pid']); ini = ''.join(w[0] for w in p['n'].split()[:2])
    return f'<div class="face" style="--c:{tc(T[abbr])};width:{size}px;height:{size}px">' + (f'<img src="{ph}">' if ph else f'<span style="font-size:{size * .42:.0f}px">{ini}</span>') + '</div>'
B = lambda n: round(n * BEAT, 3)          # n pulsos
def band(s, side, d, slam):
    t_ = T[s['abbr']]; cls = 'win' if s['win'] else 'lose'
    return f"""<div class="band glass {side} {cls}" data-a="{'left' if side == 'a' else 'right'}" data-d="{d}" data-slam="{slam}" style="--c:{tc(t_)}">
<span class="sheen"></span><img class="bl" src="{logo(s['abbr'])}"><div class="bn"><small>{e(t_['name'].replace(' ' + t_['short'], ''))}</small><b>{e(t_['short'])}</b><i>{e(s['rec'])}</i></div>
<span class="bs cnt" data-to="{s['score']}" data-d="{d}" data-end="{slam}">{s['score']}</span>
{'<span class="wtag" data-a="stamp" data-d="' + str(slam) + '">W</span><span class="burst" data-burst="' + str(slam) + '">' + '<i></i>' * 18 + '</span>' if s['win'] else ''}</div>"""
qlab = lambda i: f'{i + 1}C' if i < 4 else 'PR'
scenes = []
night_teams = []
for g in order:
    for s in g['teams']: night_teams.append(s['abbr'])
flashes = ''.join(f'<div class="fl" data-fl="{k}" style="--c:{tc(T[ab])}"><img src="{logo(ab)}"></div>' for k, ab in enumerate(night_teams[:8]))
scenes.append(('intro', f"""{flashes}
<div class="intro-logo" data-a="slam" data-d="{B(4)}">{OFFLOGO}</div>
<div class="kick glass" data-a="pop" data-d="{B(5)}">Noche NBA</div>
<div class="big"><span data-a="up" data-d="{B(5.5)}">Resumen</span><span data-a="up" data-d="{B(6)}"><em>de la noche</em></span></div>
<div class="date glass" data-a="up" data-d="{B(6.5)}">{e(FECHA)} · {len(games)} partidos</div>""", ('#ff6a1a', '#2f6bff')))
for k, g in enumerate(order):
    a, h = g['teams']; w = Wn(g); ws = w['top'][0]; is_mvp = ws['pid'] == mvp_pid; kd = kind(g)
    big = {'blow': f'¡PALIZA!<small>+{diff(g)}</small>', 'close': f'¡AL LÍMITE!<small>{diff(g)} pts</small>', 'ot': '¡PRÓRROGA!<small>tiempo extra</small>'}.get(kd, f'PARTIDO<small>{k + 1}/{len(order)}</small>')
    stats = ''.join(f'<div class="st" data-a="pop" data-d="{B(5 + q_ * .5)}"><b>{v}</b><small>{lb}</small></div>' for q_, (v, lb) in enumerate([(ws['pts'], 'PTS'), (ws['reb'], 'REB'), (ws['ast'], 'AST')]))
    scenes.append((f'g{k}', f"""<img class="wm" src="{logo(w['abbr'])}"><div class="kw {kd}" data-kw="1">{big}</div>
<div class="row"><span class="kick sm glass" data-a="left" data-d="{B(1)}">Partido {k + 1}/{len(order)}</span><span class="badge {kd}" data-a="pop" data-d="{B(1.5)}">{ {'blow': 'Paliza +' + str(diff(g)), 'close': 'Igualado · ' + str(diff(g)), 'ot': 'Prórroga'}.get(kd, 'Final') }</span></div>
{band(a, 'a', B(1), B(4))}{band(h, 'h', B(1.5), B(4))}
<div class="qs glass" data-a="up" data-d="{B(4.5)}"><div class="ql"><span></span>{''.join(f'<span>{qlab(i_)}</span>' for i_ in range(len(a['ls'])))}</div>
<div class="qr"><img src="{logo(a['abbr'])}">{''.join(f'<span class="{"hi" if x > y else ""}">{x}</span>' for x, y in zip(a['ls'], h['ls']))}</div>
<div class="qr"><img src="{logo(h['abbr'])}">{''.join(f'<span class="{"hi" if y > x else ""}">{y}</span>' for x, y in zip(a['ls'], h['ls']))}</div></div>
<div class="star glass{' gold' if is_mvp else ''}" data-a="up" data-d="{B(4.75)}" style="--c:{tc(T[w['abbr']])}">{face(ws, w['abbr'], 250)}
<span class="sheen"></span><div class="sn"><small>{'MVP de la noche' if is_mvp else 'Mejor de ' + e(short(w['abbr']))}</small><b>{e(ws['n'])}</b><div class="sts">{stats}</div></div>
{'<span class="mvp" data-a="stamp" data-d="' + str(B(6.5)) + '">MVP</span><span class="burst gold" data-burst="' + str(B(6.5)) + '">' + '<i></i>' * 24 + '</span>' if is_mvp else ''}</div>""", (tc(T[a['abbr']]), tc(T[h['abbr']]))))
up_rows = ''.join(f"""<div class="ug glass" data-a="right" data-d="{B(1 + q_ * .5)}"><span class="uh">{datetime.datetime.fromisoformat(x['utc'].replace('Z', '+00:00')).astimezone(__import__('zoneinfo').ZoneInfo('Europe/Madrid')).strftime('%H:%M')}</span>
<img src="{logo(x['teams'][0]['abbr'])}"><span class="at">@</span><img src="{logo(x['teams'][1]['abbr'])}"></div>""" for q_, x in enumerate(tonight[:6]))
scenes.append(('outro', f"""<div class="kick glass" data-a="pop" data-d="0">Esta noche</div><div class="ugrid">{up_rows}</div>
<div class="out-logo" data-a="slam" data-d="{B(5)}">{OFFLOGO}</div><div class="url" data-a="pop" data-d="{B(6)}">Enlace en la bio</div><div class="follow" data-a="up" data-d="{B(6.5)}">Síguenos {e(HANDLE)}</div>""", ('#ff6a1a', '#2f6bff')))

CSS = """
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1080px;height:1920px;overflow:hidden;background:#04060c;font-family:'Inter Tight','Barlow',sans-serif;color:#fff}
#stage{position:absolute;inset:0;transform-origin:50% 45%}
#bg{position:absolute;inset:0;background:#05070e}
.blob{position:absolute;width:1700px;height:1700px;border-radius:50%;filter:blur(120px);opacity:.85}
#b1{left:-700px;top:-650px}#b2{right:-760px;bottom:-650px}
#bg::after{content:"";position:absolute;inset:0;background:radial-gradient(120% 70% at 50% 45%,transparent 30%,rgba(3,5,10,.75) 100%)}
#stripes{position:absolute;inset:-400px;background:repeating-linear-gradient(112deg,rgba(255,255,255,.035) 0 2px,transparent 2px 46px);mix-blend-mode:overlay}
.court{position:absolute;inset:0;opacity:.06}
.wm{position:absolute;right:-260px;top:520px;width:1100px;height:1100px;object-fit:contain;opacity:.10;filter:grayscale(1) brightness(3);transform:rotate(-12deg)}
.pt{position:absolute;width:6px;height:6px;border-radius:50%;background:#fff;box-shadow:0 0 14px #fff}
.brand{position:absolute;top:62px;left:64px;display:flex;align-items:center;gap:14px;z-index:20}.brand .l{width:62px;height:62px}.brand svg{width:100%;height:100%}
.brand b{font:900 40px 'Big Shoulders Display';text-transform:uppercase;letter-spacing:.02em}.brand b span{color:#ff8a1a}
.segs{position:absolute;left:64px;right:64px;top:148px;display:flex;gap:8px;z-index:20}.segs i{flex:1;height:6px;border-radius:9px;background:rgba(255,255,255,.22);overflow:hidden}.segs i b{display:block;height:100%;width:0;background:#fff}
.scene{position:absolute;inset:0;padding:212px 60px 0;display:flex;flex-direction:column;gap:30px;opacity:0}
#sc-intro,#sc-outro{align-items:center;justify-content:center;padding-bottom:330px;gap:30px}
.glass{background:linear-gradient(135deg,rgba(255,255,255,.16),rgba(255,255,255,.04));backdrop-filter:blur(28px) saturate(1.4);-webkit-backdrop-filter:blur(28px) saturate(1.4);
  border:1.5px solid rgba(255,255,255,.28);box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 30px 70px rgba(0,0,0,.45)}
.sheen{position:absolute;inset:0;border-radius:inherit;overflow:hidden;pointer-events:none}
.sheen::before{content:"";position:absolute;top:-50%;bottom:-50%;width:35%;left:var(--sx,-60%);background:linear-gradient(100deg,transparent,rgba(255,255,255,.28),transparent);transform:skewX(-18deg)}
.fl{position:absolute;inset:0;display:grid;place-items:center;background:radial-gradient(circle at 50% 45%,color-mix(in srgb,var(--c) 85%,#fff 15%),var(--c) 45%,#03050a 100%);opacity:0;z-index:15}
.fl img{width:640px;height:640px;object-fit:contain;filter:drop-shadow(0 30px 60px rgba(0,0,0,.6))}
.kick{font:800 36px 'Inter Tight';letter-spacing:.28em;text-transform:uppercase;color:#fff;padding:12px 30px;border-radius:999px;display:inline-block}
.kick.sm{font-size:28px;padding:10px 24px}
.intro-logo{width:300px;height:300px;filter:drop-shadow(0 30px 60px rgba(255,120,30,.45))}.out-logo{width:190px;height:190px}.intro-logo svg,.out-logo svg{width:100%;height:100%}
.big{display:flex;flex-direction:column;align-items:center;font:900 168px/.84 'Big Shoulders Display';text-transform:uppercase;letter-spacing:.005em}
.big em,.kw small{font-style:normal;background:linear-gradient(95deg,#ffd166,#ff8a1a 40%,#ff3d7f 75%,#8f5bff);-webkit-background-clip:text;color:transparent;padding-right:.04em}
.date{font:700 36px 'Inter Tight';letter-spacing:.2em;text-transform:uppercase;padding:14px 32px;border-radius:999px}
.kw{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;font:900 270px/.84 'Big Shoulders Display';text-transform:uppercase;z-index:14;opacity:0;text-align:center;
  color:#fff;text-shadow:0 0 60px var(--kc),0 20px 0 rgba(0,0,0,.35)}
.kw small{display:block;font-size:140px;text-shadow:none}
.kw.blow{--kc:#ff3d5a}.kw.close{--kc:#2ee6a6}.kw.ot{--kc:#7c8cff}.kw.win{--kc:#ffffff}
.row{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:66px}
.badge{font:800 28px 'Inter Tight';letter-spacing:.16em;text-transform:uppercase;padding:12px 24px;border-radius:999px;color:#fff}
.badge.blow{background:linear-gradient(95deg,#ff3d5a,#ff8a5c);box-shadow:0 10px 30px rgba(255,61,90,.45)}.badge.close{background:linear-gradient(95deg,#13c98c,#5ef0c0);box-shadow:0 10px 30px rgba(19,201,140,.45)}
.badge.ot{background:linear-gradient(95deg,#5b6cff,#a77bff);box-shadow:0 10px 30px rgba(91,108,255,.45)}.badge.win{background:rgba(255,255,255,.14);border:1.5px solid rgba(255,255,255,.3)}
.band{position:relative;display:flex;align-items:center;gap:26px;height:300px;padding:0 40px 0 34px;border-radius:44px;overflow:hidden}
.band::before{content:"";position:absolute;left:0;top:0;bottom:0;width:100%;background:linear-gradient(100deg,var(--c) 0%,color-mix(in srgb,var(--c) 55%,transparent) 45%,transparent 80%);opacity:.95}
.band>*{position:relative}
.band .bl{width:220px;height:220px;object-fit:contain;filter:drop-shadow(0 18px 26px rgba(0,0,0,.45));flex:none}
.bn{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}.bn small{font:700 26px 'Inter Tight';letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.82)}
.bn b{font:900 80px/.92 'Big Shoulders Display';text-transform:uppercase;white-space:nowrap}.bn i{font:600 26px 'Inter Tight';font-style:normal;color:rgba(255,255,255,.7);letter-spacing:.06em}
.bs{font:900 178px/.8 'Big Shoulders Display';display:inline-block;background:linear-gradient(180deg,#fff 30%,#dfe6f5);-webkit-background-clip:text;color:transparent;filter:drop-shadow(0 8px 20px rgba(0,0,0,.35))}
.lose .bs{background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.35));-webkit-background-clip:text}
.wtag{position:absolute;right:18px;top:16px;font:800 22px 'Inter Tight';letter-spacing:.18em;background:#fff;color:#05070e;padding:8px 14px;border-radius:999px}
.burst{position:absolute;right:120px;top:50%;width:0;height:0;z-index:5}.burst i{position:absolute;width:12px;height:12px;border-radius:50%;background:#fff;box-shadow:0 0 18px #ffd166;opacity:0}
.burst.gold{right:60px;top:20px}.burst.gold i{background:#ffe27a}
.qs{display:grid;gap:6px;padding:20px 28px;border-radius:34px}
.ql,.qr{display:flex;align-items:center;gap:10px}.ql span,.qr span{flex:1;text-align:center}.ql span:first-child,.qr img{flex:none;width:66px}
.ql span{font:700 22px 'Inter Tight';letter-spacing:.2em;color:rgba(255,255,255,.55)}.qr img{height:56px;object-fit:contain}
.qr span{font:900 66px/1.05 'Big Shoulders Display';color:rgba(255,255,255,.5)}.qr span.hi{color:#fff;text-shadow:0 0 24px rgba(255,255,255,.35)}
.star{position:relative;display:flex;align-items:center;gap:30px;padding:28px 30px;border-radius:44px}
.star.gold{border-color:rgba(255,209,102,.9);box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 0 60px rgba(255,190,60,.45),0 30px 70px rgba(0,0,0,.45)}
.face{position:relative;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:radial-gradient(circle at 30% 25%,color-mix(in srgb,var(--c) 65%,#fff),var(--c));flex:none;
  box-shadow:0 0 0 6px rgba(255,255,255,.9),0 0 0 14px color-mix(in srgb,var(--c) 85%,#fff 0%),0 20px 50px rgba(0,0,0,.5)}
.face img{width:100%;height:100%;object-fit:cover;transform:scale(1.25);transform-origin:50% 40%}.face span{font-family:'Big Shoulders Display';font-weight:900}
.sn{flex:1;min-width:0}.sn small{font:800 24px 'Inter Tight';letter-spacing:.2em;text-transform:uppercase;color:#ffd166}.sn>b{display:block;font:900 80px/.92 'Big Shoulders Display';text-transform:uppercase;margin:6px 0 16px}
.sts{display:flex;gap:14px}.st{border-radius:24px;padding:12px 18px;text-align:center;min-width:118px;background:rgba(255,255,255,.1);border:1.5px solid rgba(255,255,255,.2)}
.st b{display:block;font:900 86px/.9 'Big Shoulders Display'}.st:first-child{background:linear-gradient(160deg,#ffd166,#ff8a1a);border:0}.st:first-child b,.st:first-child small{color:#1a0b02}
.st small{font:800 18px 'Inter Tight';letter-spacing:.22em;color:rgba(255,255,255,.7)}
.mvp{position:absolute;right:-8px;top:-46px;font:900 72px/1 'Big Shoulders Display';color:#1a0b02;background:linear-gradient(100deg,#ffe8a3,#ffc23d 50%,#ff9d00);padding:8px 28px;border-radius:20px;box-shadow:0 14px 40px rgba(255,170,0,.5)}
.ugrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;width:100%}
.ug{display:flex;align-items:center;justify-content:center;gap:12px;padding:20px;border-radius:30px}
.ug img{width:90px;height:90px;object-fit:contain}.ug .at{font:800 30px 'Inter Tight';color:rgba(255,255,255,.5)}.uh{font:900 46px 'Big Shoulders Display';color:#ffd166;margin-right:6px}
.url{font:800 44px 'Inter Tight';letter-spacing:.04em;color:#1a0b02;background:linear-gradient(95deg,#ffd166,#ff8a1a 50%,#ff3d7f);padding:18px 46px;border-radius:999px;box-shadow:0 20px 50px rgba(255,120,60,.45)}
.follow{font:800 36px 'Inter Tight';letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.85)}
#wipe{position:absolute;top:-200px;bottom:-200px;width:900px;background:linear-gradient(100deg,#ffd166,#ff8a1a 35%,#ff3d7f 70%,#8f5bff);transform:skewX(-14deg);z-index:30;left:-1500px}
#wipe2{position:absolute;top:-200px;bottom:-200px;width:220px;background:#fff;transform:skewX(-14deg);z-index:31;left:-1500px;opacity:.95}
#cap{position:absolute;left:40px;right:40px;bottom:100px;height:230px;display:flex;align-items:center;justify-content:center;z-index:25}
#cap div{text-align:center;font:900 84px/1.25 'Big Shoulders Display';text-transform:uppercase;text-shadow:0 6px 24px rgba(0,0,0,.6)}
#cap .w{display:inline-block;margin:0 .06em;padding:0 .14em;border-radius:14px;color:#fff}#cap .w.on{color:#1a0b02;background:linear-gradient(95deg,#ffd166,#ff8a1a)}
#flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:40;pointer-events:none}
"""
COURT = """<svg class="court" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="#fff" stroke-width="6"><circle cx="540" cy="960" r="200"/><path d="M0 960H1080"/><path d="M180 0v260a360 360 0 0 0 720 0V0"/><path d="M180 1920v-260a360 360 0 0 1 720 0v260"/></g></svg>"""
TL = [{'key': x['key'], 'start': x['start'], 'dur': x['dur'], 'cols': next(c for k_, _, c in scenes if k_ == x['key'])} for x in timeline]
WORDS = [w_ for x in timeline for w_ in x['words']]
chunks = []; cur = []
for w_ in WORDS:
    cur.append(w_)
    if len(cur) >= 3 or re.search(r'[.,:;!?]$', w_['w']): chunks.append(cur); cur = []
if cur: chunks.append(cur)
CH = [{'s': c[0]['s'], 'e': c[-1]['e'], 'w': [{'t': x['w'], 's': x['s'], 'e': x['e']} for x in c]} for c in chunks]
random.seed(5); PTS = [{'x': random.uniform(0, 1080), 'y': random.uniform(0, 1920), 'v': random.uniform(60, 160), 's': random.uniform(.4, 1.3), 'o': random.uniform(.2, .6)} for _ in range(40)]
JS = """
const TL=__TL__, CH=__CH__, PTS=__PTS__, TOTAL=__TOTAL__, BEAT=__BEAT__;
const cl=x=>Math.min(1,Math.max(0,x)), ease=x=>1-Math.pow(1-cl(x),3), back=x=>{x=cl(x);const c=2.2;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const seg=document.querySelector('.segs');TL.forEach(()=>seg.insertAdjacentHTML('beforeend','<i><b></b></i>'));
const pl=document.getElementById('pts');PTS.forEach(()=>pl.insertAdjacentHTML('beforeend','<i class="pt"></i>'));
document.querySelectorAll('.burst').forEach(b=>b.querySelectorAll('i').forEach((n,i,a)=>{n.dataset.ang=(i/a.length)*Math.PI*2+Math.random()*.3;n.dataset.sp=180+Math.random()*260}));
function render(t){
  let shake=0, glitch=0;
  let cur=TL[0];TL.forEach(s=>{if(t>=s.start)cur=s});
  document.querySelectorAll('.segs b').forEach((b,i)=>{const s=TL[i];b.style.width=(cl((t-s.start)/s.dur)*100)+'%'});
  b1.style.background=cur.cols[0];b2.style.background=cur.cols[1];
  b1.style.transform=`translate(${Math.sin(t*.9)*110}px,${Math.cos(t*.7)*80}px) scale(${1+.08*Math.sin(t*1.3)})`;
  b2.style.transform=`translate(${Math.cos(t*.8)*110}px,${Math.sin(t*.6)*90}px)`;
  stripes.style.transform=`translateX(${-(t*90)%40}px)`;
  document.querySelectorAll('.pt').forEach((p,i)=>{const q=PTS[i];const y=((q.y-t*q.v)%1920+1920)%1920;p.style.transform=`translate(${q.x+Math.sin(t*q.s*2+i)*40}px,${y}px) scale(${q.s})`;p.style.opacity=q.o});
  TL.forEach(s=>{const el=document.getElementById('sc-'+s.key);const lt=t-s.start;const on=lt>=0&&lt<s.dur;
    el.style.opacity=on?1:0; if(!on)return;
    el.querySelectorAll('[data-a]').forEach(n=>{const d=parseFloat(n.dataset.d||0);const p=(lt-d)/0.32;const a=n.dataset.a;let o=ease(p),tr='';
      if(a==='up')tr=`translateY(${(1-ease(p))*120}px) scale(${0.9+0.1*ease(p)})`;
      if(a==='left')tr=`translateX(${-(1-ease(p))*1200}px) skewX(${(1-ease(p))*-18}deg)`;
      if(a==='right')tr=`translateX(${(1-ease(p))*1200}px) skewX(${(1-ease(p))*18}deg)`;
      if(a==='pop')tr=`scale(${p<=0?0:0.3+0.7*back(p)})`;
      if(a==='slam'){tr=`scale(${p<=0?3.5:1+2.5*(1-back(p*1.2))}) rotate(${(1-ease(p))*-25}deg)`;o=p>0?1:0;if(p>0.3&&p<1)shake=Math.max(shake,1-(p-.3)/.7)}
      if(a==='stamp'){const r=n.classList.contains('mvp')?8:-6;tr=`rotate(${r}deg) scale(${p<=0?3.2:1+2.2*(1-back(p*1.6))})`;o=p>0?1:0;if(p>0.25&&p<0.9)shake=Math.max(shake,1-(p-.25)/.65)}
      if(n.dataset.slam){const sp=lt-parseFloat(n.dataset.slam);if(sp>0&&sp<.3){tr+=` scale(${1+.06*Math.sin(sp/.3*Math.PI)})`}}
      n.style.opacity=o;n.style.transform=tr;
      const sl=parseFloat(n.dataset.slam||99);
      if(n.classList.contains('lose')){const k=cl((lt-sl)/.3);n.style.filter=`grayscale(${k*.75}) brightness(${1-k*.3})`}
      if(n.classList.contains('win')&&lt>sl){n.style.boxShadow=`0 0 ${50+30*Math.abs(Math.sin(lt*Math.PI/BEAT))}px rgba(255,200,80,.6),0 30px 60px rgba(0,0,0,.45)`}
    });
    el.querySelectorAll('.cnt').forEach(n=>{const to=+n.dataset.to,d=parseFloat(n.dataset.d||0),en=parseFloat(n.dataset.end||d+1.2);const p=cl((lt-d)/(en-d));n.textContent=Math.round(to*(1-Math.pow(1-p,2)));
      const sp=lt-en;n.style.transform=sp>0&&sp<.35?`scale(${1+.35*Math.sin(sp/.35*Math.PI)})`:'';});
    el.querySelectorAll('[data-burst]').forEach(b=>{const bt=lt-parseFloat(b.dataset.burst);b.querySelectorAll('i').forEach(n=>{
      if(bt<0||bt>.9){n.style.opacity=0;return}const a=+n.dataset.ang,sp=+n.dataset.sp;const r=sp*ease(bt/.9);n.style.opacity=1-bt/.9;n.style.transform=`translate(${Math.cos(a)*r}px,${Math.sin(a)*r+bt*bt*300}px) scale(${1.4-bt})`})});
    const kw=el.querySelector('[data-kw]');if(kw){const k=lt/(BEAT*1.0);kw.style.opacity=k<1?1:cl(1-(k-1)*3);kw.style.transform=`scale(${k<1?1.4-0.4*ease(k*2):1+(k-1)*.4}) rotate(-6deg)`;}
    el.querySelectorAll('.fl').forEach(f=>{const i=+f.dataset.fl;const fs=i*BEAT/2;const on2=lt>=fs&&lt<fs+BEAT/2&&lt<BEAT*4;f.style.opacity=on2?1:0;
      if(on2){const p=(lt-fs)/(BEAT/2);f.querySelector('img').style.transform=`scale(${1.35-0.35*ease(p*1.5)}) rotate(${(i%2?1:-1)*(1-ease(p))*12}deg)`}});
  });
  // cortinilla + glitch en cada cambio de escena
  let wx=-1500;TL.forEach((s,i)=>{if(i===0)return;const p=(t-(s.start-0.22))/0.44;if(p>0&&p<1)wx=-1100+p*3000;const g=t-s.start;if(g>-.08&&g<.14)glitch=1});
  wipe.style.left=wx+'px';wipe2.style.left=(wx+700)+'px';
  // pulso con cada golpe de bombo
  const bt=((t%BEAT)+BEAT)%BEAT, pulse=t>BEAT*4?Math.exp(-bt*14):0;
  flash.style.opacity=(t<0.12?1-t/.12:0)+(cur.key==='intro'&&t<BEAT*4?0.25*Math.exp(-bt*16):0);
  // subtítulos: aparecen palabra a palabra
  const c=CH.find(c=>t>=c.s-0.04&&t<=c.e+0.3);
  if(c){cap.innerHTML='<div>'+c.w.filter(w=>t>=w.s-0.04).map(w=>{const p=cl((t-w.s+0.04)/0.12);return `<span class="w ${t<w.e+0.06?'on':''}" style="transform:scale(${0.5+0.5*back(p)}) rotate(${(1-p)*-8}deg)">${w.t}</span>`}).join(' ')+'</div>'}else cap.innerHTML='';
  document.querySelectorAll('.sheen').forEach((n,i)=>{const ph=((t*0.55+i*0.17)%2.2)/2.2;n.style.setProperty('--sx',(ph<0.45?-60+ph/0.45*220:200)+'%')});
  const sx=shake?Math.sin(t*95)*18*shake:0, sy=shake?Math.cos(t*81)*18*shake:0;
  stage.style.transform=`translate(${sx}px,${sy}px) scale(${1+0.018*pulse})`;
  stage.style.filter=glitch?'drop-shadow(10px 0 0 rgba(255,0,80,.75)) drop-shadow(-10px 0 0 rgba(0,229,255,.75))':'';
}
window.render=render;
""".replace('__TL__', json.dumps(TL)).replace('__CH__', json.dumps(CH, ensure_ascii=False)).replace('__PTS__', json.dumps(PTS)).replace('__TOTAL__', str(TOTAL)).replace('__BEAT__', str(BEAT))
page = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Inter+Tight:wght@600;700;800;900&display=block" rel="stylesheet">
<style>{CSS}</style></head><body><div id="stage"><div id="bg"><div class="blob" id="b1"></div><div class="blob" id="b2"></div></div><div id="stripes"></div>{COURT}<div id="pts"></div>
<div class="brand"><span class="l">{OFFLOGO}</span><b>Off<span>court</span></b></div><div class="segs"></div>
{''.join(f'<div class="scene" id="sc-{k}">{v}</div>' for k, v, _ in scenes)}<div id="cap"></div></div><div id="wipe"></div><div id="wipe2"></div><div id="flash"></div>
<script>{JS}</script></body></html>"""
open(f'{WORK}/video.html', 'w', encoding='utf-8').write(page)

CAP = r"""const {chromium}=require('playwright');(async()=>{const [dir,fps,total]=[process.argv[1],+process.argv[2],+process.argv[3]];
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+dir+'/video.html');await p.waitForTimeout(3000);await p.evaluate(()=>document.fonts.ready);
const n=Math.ceil(total*fps);for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:dir+'/f/'+String(i).padStart(5,'0')+'.jpg',type:'jpeg',quality:86});}
await b.close()})();"""
subprocess.run(['node', '-e', CAP, WORK, str(FPS), str(TOTAL)], check=True)
dst = os.path.join(OUT, 'video_resumen_nba.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{WORK}/f/%05d.jpg', '-i', f'{WORK}/audio.wav',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst], check=True)
open(os.path.join(OUT, 'guion.txt'), 'w', encoding='utf-8').write('\n'.join(f"[{x['voice']:.1f}s] {x['text']}" for x in timeline))
shutil.rmtree(WORK, ignore_errors=True)
print('ok', dst, f'{TOTAL:.1f}s')
