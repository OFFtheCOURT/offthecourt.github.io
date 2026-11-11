#!/usr/bin/env python3
"""Vídeo resumen diario de Offcourt para redes (vertical 9:16, con voz y subtítulos).

Pasos (ver redes/LEEME.md):
  python3 redes/video.py borrador            -> redes/salida/borrador.json (datos de la noche para escribir el guion)
  (escribir redes/salida/noche.json)          -> guion con {Nombre|Pronunciación}, partidos y tarjetas
  python3 redes/video.py voz                  -> genera la voz en GitHub Actions y la descarga
  python3 redes/video.py montar               -> redes/salida/data.js
  python3 redes/video.py fotogramas 1:6,3:4   -> redes/salida/prueba_*.jpg (para revisar)
  python3 redes/video.py render               -> redes/salida/offcourt_AAAA-MM-DD.mp4
"""
import base64, datetime, json, os, re, shutil, subprocess, sys, time

R = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(R); OUT = os.path.join(R, 'salida')
GH_REPO = 'OFFtheCOURT/offthecourt.github.io'
os.makedirs(OUT, exist_ok=True)
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
ABR_D = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']; ABR_M = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']


def sh(*a, **k): return subprocess.run(a, check=True, **k)
def dur_of(p): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).decode())


def web_data():
    """lee los datos que la web lleva incrustados en index.html"""
    h = open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
    dec = json.JSONDecoder()
    m = re.search(r'(?:const|let|var)\s+\w+\s*=\s*(\{"nba":\{"key":"nba")', h); L, _ = dec.raw_decode(h[m.start(1):])
    m = re.search(r'const IMG\s*=\s*', h); IMG, _ = dec.raw_decode(h[m.end():])
    m = re.search(r'<div class="logo-slot" id="logoSlot">(<svg.*?</svg>)', open(os.path.join(REPO, 'tpl_head.html'), encoding='utf-8').read(), re.S)
    return L, IMG, m.group(1)


def hora_es(utc):
    if not utc: return ''
    d = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
    # horario de España: UTC+2 de último domingo de marzo a último domingo de octubre
    y = d.year
    def last_sun(mo): x = datetime.datetime(y, mo, 31, 1, tzinfo=datetime.timezone.utc); return x - datetime.timedelta(days=(x.weekday() + 1) % 7)
    off = 2 if last_sun(3) <= d < last_sun(10) else 1
    return (d + datetime.timedelta(hours=off)).strftime('%H:%M')


# ---------------------------------------------------------------- borrador
def borrador():
    L, IMG, _ = web_data(); N = L['nba']; T = N['teams']
    night = N['periods'][0]
    games = []
    for g in night['games']:
        A, H = g['teams']
        def side(t):
            st = t.get('st') or {}
            return {'equipo': t['abbr'], 'nombre': T[t['abbr']]['name'], 'corto': T[t['abbr']]['short'], 'puntos': t['score'], 'balance': t.get('rec'),
                    'cuartos': t.get('ls'), 'triples': st.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted'), 'rebotes': st.get('totalRebounds'),
                    'asistencias': st.get('assists'), 'pintura': st.get('pointsInPaint'), 'contraataque': st.get('fastBreakPoints'), 'maxima_ventaja': st.get('largestLead'),
                    'jugadores': [{'pid': p['pid'], 'nombre': p['n'], 'pos': p['pos'], 'pts': p['pts'], 'reb': p['reb'], 'ast': p['ast'], 'rob': p['stl'], 'tap': p['blk'],
                                   'tiros': p['fg'], 'triples': p['tp'], 'tl': p['ft'], 'min': p['min'], 'masmenos': p['pm'],
                                   'foto': os.path.exists(os.path.join(REPO, 'photos', p['pid'] + '.webp'))} for p in sorted(t.get('top') or [], key=lambda p: -p['pts'])]}
        best = max((p['pts'] for t in (A, H) for p in (t.get('top') or [])), default=0)
        games.append({'partido': f"{A['abbr']}-{H['abbr']}", 'estado': g.get('status'), 'terminado': g.get('completed', g.get('status') == 'Final'),
                      'pabellon': g.get('venue'), 'ciudad': g.get('city'), 'cronica_espn': g.get('recap'), 'nota': g.get('note'),
                      'visitante': side(A), 'local': side(H), 'interes': best + max(0, 15 - abs(A['score'] - H['score']))})
    games.sort(key=lambda g: -g['interes'])
    up = N['upcoming'][0] if N.get('upcoming') else {'games': []}
    hoy = [{'partido': f"{g['teams'][0]['abbr']}-{g['teams'][1]['abbr']}", 'visitante': T[g['teams'][0]['abbr']]['name'], 'local': T[g['teams'][1]['abbr']]['name'],
            'hora_es': hora_es(g.get('utc'))} for g in up['games']]
    pron = json.load(open(os.path.join(R, 'pronunciacion.json'), encoding='utf-8'))
    nombres = sorted({p['nombre'] for g in games for s in ('visitante', 'local') for p in g[s]['jugadores']} | {T[a]['name'] for a in T})
    out = {'fecha': night['key'], 'actualizado_web': os.path.getmtime(os.path.join(REPO, 'index.html')), 'partidos': games, 'esta_noche': hoy,
           'lideres_temporada': N.get('leaders'), 'pronunciacion_conocida': {n: pron[n] for n in nombres if n in pron},
           'sin_pronunciacion': [n for n in nombres if n not in pron]}
    p = os.path.join(OUT, 'borrador.json'); json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('fecha', night['key'], '·', len(games), 'partidos ·', len(hoy), 'esta noche ->', p)


# ---------------------------------------------------------------- voz
def noche():
    return json.load(open(os.path.join(OUT, 'noche.json'), encoding='utf-8'))


def voz():
    n = noche(); voice = n.get('voz', 'es-ES-AlvaroNeural:r')
    guion = [{'id': s['id'], 't': s['t']} for s in n['segmentos']]
    payload = {'ref': 'main', 'inputs': {'guion': base64.b64encode(json.dumps(guion, ensure_ascii=False).encode()).decode(), 'voces': voice, 'rate': n.get('velocidad', '+8%')}}
    pf = os.path.join(OUT, 'dispatch.json'); json.dump(payload, open(pf, 'w'))
    before = subprocess.run(['gh', 'run', 'list', '-R', GH_REPO, '-w', 'voz.yml', '-L', '1', '--json', 'databaseId', '-q', '.[0].databaseId'], capture_output=True, text=True).stdout.strip()
    sh('gh', 'api', '-X', 'POST', f'repos/{GH_REPO}/actions/workflows/voz.yml/dispatches', '--input', pf)
    rid = None
    for _ in range(120):
        time.sleep(5)
        r = subprocess.run(['gh', 'run', 'list', '-R', GH_REPO, '-w', 'voz.yml', '-L', '1', '--json', 'databaseId,status,conclusion'], capture_output=True, text=True).stdout
        j = json.loads(r or '[]')
        if j and str(j[0]['databaseId']) != before:
            rid = j[0]['databaseId']
            if j[0]['status'] == 'completed':
                if j[0]['conclusion'] != 'success': sys.exit(f'la voz ha fallado: gh run view {rid} -R {GH_REPO} --log')
                break
    else:
        sys.exit('la voz no ha terminado a tiempo')
    d = os.path.join(OUT, 'voz'); shutil.rmtree(d, ignore_errors=True)
    sh('git', 'clone', '-q', '--depth', '1', '-b', 'redes-voz', f'https://github.com/{GH_REPO}', d)
    T = json.load(open(os.path.join(d, 'tiempos.json')))
    print('voz lista:', list(T), '·', run_url(rid))


def run_url(rid): return f'https://github.com/{GH_REPO}/actions/runs/{rid}'


# ---------------------------------------------------------------- montar
def units(tpl):
    out = []
    for m in re.finditer(r'\{([^|}]*)\|([^}]*)\}|(\S+)', tpl):
        if m.group(3) is not None:
            w = m.group(3)
            if out and re.fullmatch(r'[.,:;!?…]+', w): out[-1]['o'] += w; out[-1]['r'] += w; continue
            out.append({'o': w, 'r': w})
        else:
            out.append({'o': m.group(1), 'r': m.group(2), 'name': True})
    # puntuación pegada a un bloque: "{Utah|Iúta}," -> la coma va en la siguiente palabra suelta
    for i, u in enumerate(out):
        mm = re.match(r'^([.,:;!?…]+)(.*)$', u['o']) if not u.get('name') else None
        if mm and i > 0 and mm.group(2) == '':
            pass
    return out


def caption_words(tpl, mode, bounds, dur):
    us = units(tpl); spoken = ''; spans = []
    for u in us:
        txt = u['r'] if mode == 'r' else u['o']
        if spoken: spoken += ' '
        a = len(spoken); spoken += txt; spans.append((a, len(spoken)))
    cur = 0; times = [[] for _ in us]; low = spoken.lower()
    for b in [b for b in bounds if b['k'] == 'WordBoundary']:
        j = low.find(b['w'].lower(), cur)
        if j < 0: continue
        cur = j + len(b['w'])
        for ui, (a, e) in enumerate(spans):
            if a <= j < e: times[ui].append(b); break
    out = [{'u': u, 'o': times[i][0]['o'] if times[i] else None, 'e': (times[i][-1]['o'] + times[i][-1]['d']) if times[i] else None} for i, u in enumerate(us)]
    for i, x in enumerate(out):
        if x['o'] is None:
            prev = next((out[k]['e'] for k in range(i - 1, -1, -1) if out[k]['e'] is not None), 0)
            nxt = next((out[k]['o'] for k in range(i + 1, len(out)) if out[k]['o'] is not None), dur)
            x['o'] = prev + 0.02; x['e'] = max(x['o'] + 0.1, min(nxt, prev + 0.4))
    words = []
    for x in out:
        disp = x['u']['o'].split(' '); step = (x['e'] - x['o']) / len(disp)
        for k, w in enumerate(disp):
            words.append({'w': w, 'o': round(x['o'] + k * step, 3), 'd': round(step, 3), 'name': bool(x['u'].get('name')), 'src': x['u']['o'].strip('.,:;!?…')})
    return words


KEEP = 0.28
def tighten(src, out):
    """acorta los silencios largos entre frases; devuelve (duración, función para reajustar tiempos)"""
    log = subprocess.run(['ffmpeg', '-i', src, '-af', 'silencedetect=n=-40dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    total = dur_of(src); sil = list(zip(st, en + [total] * (len(st) - len(en))))
    keep = []; cur = 0.0; cuts = []
    for a, e in sil:
        if a < 0.05: a = 0.0
        lo = a + KEEP / 2 if a > 0 else max(0, e - 0.05); hi = e - KEEP / 2 if e < total - 0.01 else e
        if e >= total - 0.01: lo = a + 0.12
        if hi > lo: keep.append((cur, lo)); cuts.append((lo, hi)); cur = hi
    keep.append((cur, total)); keep = [(a, e) for a, e in keep if e - a > 0.01]
    flt = ''.join(f'[0:a]atrim={a:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}];' for i, (a, e) in enumerate(keep))
    flt += ''.join(f'[a{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=0:a=1[o]'
    sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-filter_complex', flt, '-map', '[o]', '-ar', '48000', '-ac', '1', out)
    def tm(t):
        r = t
        for lo, hi in cuts:
            if t >= hi: r -= hi - lo
            elif t > lo: r -= t - lo
        return max(0.0, r)
    return dur_of(out), tm


def team_obj(ab, tm, T):
    t = T[ab]; nums = [p['num'] for p in tm.get('top') or []][:5]
    while len(nums) < 5: nums.append(str(10 + len(nums) * 3))
    a2 = '#' + (t.get('alt') or 'ffffff')
    if a2.lower() == '#' + t['color'].lower(): a2 = '#ffffff'
    st = tm.get('st') or {}
    try:
        fga = int(st['fieldGoalsMade-fieldGoalsAttempted'].split('-')[1]) or 1; tpa = int(st['threePointFieldGoalsMade-threePointFieldGoalsAttempted'].split('-')[1])
    except Exception:
        fga, tpa = 1, 0
    sc = max(1, tm['score'])
    style = {'three': round(tpa / fga, 3), 'fast': round(int(st.get('fastBreakPoints') or 0) / sc * 4, 3), 'paint': round(int(st.get('pointsInPaint') or 0) / sc * 1.5, 3)}
    return {'style': style, 'ab': ab, 'c': '#' + t['color'], 'a': '#' + (t.get('alt') or 'ffffff'), 'a2': a2, 'short': t['short'], 'name': t['name'],
            'rec': tm.get('rec') or '', 'score': tm['score'], 'nums': nums}


def prof(pl):
    tpm = int((pl.get('tp') or '0-0').split('-')[0]); return {'three': tpm >= 3, 'big': (pl.get('pos') == 'C' or pl.get('reb', 0) >= 10) and tpm < 3}


def montar():
    n = noche(); L, IMG, logo = web_data(); N = L['nba']; T = N['teams']; LOG = IMG['t']['nba']
    vkey = n.get('voz', 'es-ES-AlvaroNeural:r').replace(':', '_'); mode = vkey.rsplit('_', 1)[1]
    vdir = os.path.join(OUT, 'voz'); TIMES = json.load(open(os.path.join(vdir, 'tiempos.json')))[vkey]
    night = next(p for p in N['periods'] if p['key'] == n['fecha'])
    games = {g['teams'][0]['abbr'] + '-' + g['teams'][1]['abbr']: g for g in night['games']}
    os.makedirs(os.path.join(OUT, 'audio'), exist_ok=True)
    PAD_IN, PAD_OUT = 0.55, 0.45
    scenes = []; photos = {}; used = set(); narrated = [s for s in n['segmentos'] if s.get('partido')]
    for seg in n['segmentos']:
        b = next(x['palabras'] for x in TIMES if x['id'] == seg['id'])
        d, tm = tighten(os.path.join(vdir, vkey, seg['id'] + '.mp3'), os.path.join(OUT, 'audio', seg['id'] + '.wav'))
        b = [dict(x, o=tm(x['o']), d=max(0.05, tm(x['o'] + x['d']) - tm(x['o']))) for x in b]
        w = caption_words(seg['t'], mode, b, d)
        for x in w: x['o'] = round(x['o'] + PAD_IN, 3)
        def when(key):
            t = next((x['o'] for x in w if x['src'] == key), None)
            if t is None: t = next((x['o'] for x in w if key.split()[-1] in x['src']), None)
            return t if t is not None else PAD_IN
        if seg['id'] == 'intro':
            scenes.append({'type': 'intro', 'id': 'intro', 'dur': round(max(5.2, d + PAD_IN + .5), 2), 'off': PAD_IN, 'words': w}); continue
        if seg['id'] == 'outro':
            ton = []; hl = []
            for g in (N['upcoming'][0]['games'] if N.get('upcoming') else []):
                a, h = g['teams'][0]['abbr'], g['teams'][1]['abbr']; used |= {a, h}
                ton.append({'a': a, 'h': h, 'an': T[a]['short'], 'hn': T[h]['short'], 'time': hora_es(g.get('utc'))})
                k = (seg.get('resaltar') or {}).get(f'{a}-{h}'); hl.append(when(k) if k else None)
            scenes.append({'type': 'outro', 'id': 'outro', 'dur': round(d + PAD_IN + 2.6, 2), 'off': PAD_IN, 'words': w, 'hl': hl, 'tonight': ton}); continue
        g = games[seg['partido']]; A, Hm = g['teams']; used |= {A['abbr'], Hm['abbr']}
        tA, tH = team_obj(A['abbr'], A, T), team_obj(Hm['abbr'], Hm, T)
        cards = []; marks = []
        for c in seg.get('tarjetas', []):
            wt = when(c['clave'])
            if c.get('stat'):
                ti = 0 if c['equipo'] == A['abbr'] else 1; tm_ = (A, Hm)[ti]; st = tm_.get('st') or {}
                if c['stat'] == 'triples':
                    m_, a_ = st['threePointFieldGoalsMade-threePointFieldGoalsAttempted'].split('-'); big, line, last = m_, f'{m_} DE {a_} EN TRIPLES', 'Lluvia de triples'
                else:
                    big, line, last = str(c.get('valor', '')), c.get('linea', ''), c.get('titulo', '')
                cards.append({'kind': 'stat', 'big': big, 'first': T[tm_['abbr']]['short'], 'last': c.get('titulo', last), 'line': c.get('linea', line), 'team': ti, 't': wt}); continue
            ti = 0 if any(p['pid'] == c['pid'] for p in A.get('top') or []) else 1; tm_ = (A, Hm)[ti]
            pl = next(p for p in tm_['top'] if p['pid'] == c['pid']); full = c.get('nombre', pl['n']); parts = full.split(' ', 1)
            cards.append({'kind': 'player', 'pid': c['pid'], 'first': parts[0], 'last': parts[1] if len(parts) > 1 else parts[0], 'line': c['linea'], 'team': ti, 't': wt})
            fig = [p['pid'] for p in tm_['top']].index(c['pid']); pr = prof(pl)
            marks.append({'t': wt, 'team': ti, 'fig': min(fig, 4), 'short': c.get('etiqueta', full.split(' ')[-1]).upper(), 'pts': 3 if pr['three'] else None, 'prof': pr})
            ph = os.path.join(REPO, 'photos', c['pid'] + '.webp')
            if os.path.exists(ph): photos[c['pid']] = 'data:image/webp;base64,' + base64.b64encode(open(ph, 'rb').read()).decode()
        scenes.append({'type': 'game', 'id': seg['id'], 'gi': narrated.index(seg), 'dur': round(d + PAD_IN + PAD_OUT, 2), 'off': PAD_IN,
                       'seed': int(re.sub(r'\D', '', str(g['id'])) or 1) % 100000, 'teams': [tA, tH], 'venue': g.get('venue') or '', 'cards': cards, 'marks': marks, 'words': w})
    for i, sc in enumerate(scenes[:-1]):
        nx = scenes[i + 1]; sc['next'] = [nx['teams'][1]['c'], nx['teams'][0]['c']] if nx['type'] == 'game' else ['#ff7a1a', '#386eff']
    f = datetime.date.fromisoformat(n['fecha']); f2 = f + datetime.timedelta(days=1)
    outro = next((s for s in scenes if s['type'] == 'outro'), None); ton = outro['tonight'] if outro else []
    DATA = {'dateLabel': f'{ABR_D[f.weekday()]} {f.day} {ABR_M[f.month - 1]}', 'dateLong': f'{DIAS[f.weekday()]} {f.day} de {MESES[f.month - 1]}',
            'tonightLabel': f'{ABR_D[f2.weekday()]} {f2.day} {ABR_M[f2.month - 1]}', 'tonightCount': f'{len(ton)} PARTIDOS · HORA ESPAÑOLA',
            'ngames': len(narrated), 'scenes': scenes, 'tonight': ton,
            'mini': [{'a': g['teams'][0]['abbr'], 'h': g['teams'][1]['abbr'], 'as': g['teams'][0]['score'], 'hs': g['teams'][1]['score']} for g in night['games'] if g['teams'][0].get('score') is not None],
            'logos': {k: LOG[k] for k in used | {g['teams'][i]['abbr'] for g in night['games'] for i in (0, 1)} if k in LOG}, 'photos': photos,
            'logo': 'data:image/svg+xml;base64,' + base64.b64encode(logo.encode()).decode()}
    open(os.path.join(OUT, 'data.js'), 'w', encoding='utf-8').write('window.DATA=' + json.dumps(DATA, ensure_ascii=False) + ';')
    # guarda en el diccionario las pronunciaciones usadas
    pf = os.path.join(R, 'pronunciacion.json'); pron = json.load(open(pf, encoding='utf-8')); nuevo = 0
    for s in n['segmentos']:
        for m in re.finditer(r'\{([^|}]*)\|([^}]*)\}', s['t']):
            if m.group(1) not in pron: pron[m.group(1)] = m.group(2); nuevo += 1
    json.dump(dict(sorted(pron.items())), open(pf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('escenas', [(s['id'], s['dur']) for s in scenes], 'total', round(sum(s['dur'] for s in scenes), 1), 's · fotos', len(photos), '· pronunciaciones nuevas', nuevo)


# ---------------------------------------------------------------- render
def fotogramas(lst):
    sh('node', os.path.join(R, 'render.js'), 'frames', lst)


def render():
    D = json.loads(open(os.path.join(OUT, 'data.js'), encoding='utf-8').read()[len('window.DATA='):-1]); n = noche()
    esc = os.path.join(OUT, 'escenas'); shutil.rmtree(esc, ignore_errors=True); os.makedirs(esc)
    procs = [subprocess.Popen(['node', os.path.join(R, 'render.js'), 'scene', str(i), os.path.join(esc, f's{i}.mp4')]) for i in range(len(D['scenes']))]
    if any(p.wait() for p in procs): sys.exit('ha fallado el render de alguna escena')
    for i, sc in enumerate(D['scenes']):
        vd = dur_of(os.path.join(esc, f's{i}.mp4'))
        sh('ffmpeg', '-v', 'error', '-y', '-i', os.path.join(OUT, 'audio', sc['id'] + '.wav'), '-af', f"adelay={int(sc['off'] * 1000)},apad=whole_dur={vd:.3f},loudnorm=I=-15:TP=-1.5:LRA=7",
           '-ar', '48000', '-ac', '2', os.path.join(esc, f'a{i}.wav'))
    open(os.path.join(esc, 'v.txt'), 'w').write(''.join(f"file 's{i}.mp4'\n" for i in range(len(D['scenes']))))
    open(os.path.join(esc, 'a.txt'), 'w').write(''.join(f"file 'a{i}.wav'\n" for i in range(len(D['scenes']))))
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(esc, 'v.txt'), '-c', 'copy', os.path.join(esc, 'v.mp4'))
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(esc, 'a.txt'), '-c:a', 'pcm_s16le', os.path.join(esc, 'a.wav'))
    final = os.path.join(OUT, f"offcourt_noche_nba_{n['fecha']}.mp4")
    sh('ffmpeg', '-v', 'error', '-y', '-i', os.path.join(esc, 'v.mp4'), '-i', os.path.join(esc, 'a.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
       '-shortest', '-movflags', '+faststart', final)
    # hoja de control: un fotograma de cada escena
    tl = 0; frames = []
    for i, sc in enumerate(D['scenes']):
        t = tl + min(sc['dur'] - .5, max(1.5, sc['dur'] * .6)); tl += sc['dur']
        f = os.path.join(esc, f'c{i}.jpg'); sh('ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', final, '-frames:v', '1', '-vf', 'scale=270:480', f); frames.append(f)
    sh('ffmpeg', '-v', 'error', '-y', *sum([['-i', f] for f in frames], []), '-filter_complex', ''.join(f'[{i}]' for i in range(len(frames))) + f'hstack=inputs={len(frames)}', os.path.join(OUT, 'control.jpg'))
    print('vídeo:', final, f'{dur_of(final):.1f}s', '· control:', os.path.join(OUT, 'control.jpg'))


# ---------------------------------------------------------------- estado de la noche
HECHO = os.path.join(R, 'hecho.json')
def _restante(detail):
    """minutos reales que faltan, aproximados, a partir del estado de ESPN ("4th 2:31", "Halftime"...)"""
    d = (detail or '').strip()
    if d.lower().startswith('final'): return 0
    if 'half' in d.lower(): return 24 * 2.4 + 15
    m = re.match(r'(?:End of )?(\d)(?:st|nd|rd|th)(?:\s*Qtr)?(?:\s*(\d+):(\d+))?', d)
    if m:
        q = int(m.group(1)); clk = int(m.group(2)) + int(m.group(3) or 0) / 60 if m.group(2) else 0
        if d.startswith('End of'): clk = 0
        return ((4 - q) * 12 + clk) * 2.4 + 4
    m = re.match(r'(\d*)OT\s*(\d+):(\d+)', d)
    if m: return (int(m.group(2)) + int(m.group(3)) / 60) * 2.4 + 4
    m = re.match(r'End of (\d*)OT', d)
    if m: return 3
    return None

def estado(imprimir=True):
    """LISTO / ESPERANDO (con hora estimada) / HECHO / SIN_PARTIDOS para la noche NBA más reciente"""
    L, _, _ = web_data(); N = L['nba']
    h = open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
    m = re.search(r'const UPDATED\s*=\s*"([^"]+)"', h); upd = datetime.datetime.fromisoformat(m.group(1)) if m else None
    now = datetime.datetime.now(datetime.timezone.utc)
    et = now - datetime.timedelta(hours=5)  # hora del este aproximada (vale para decidir la noche)
    night = (et - datetime.timedelta(hours=12)).date().isoformat()  # la noche "en curso o recién acabada"
    hecho = json.load(open(HECHO)) if os.path.exists(HECHO) else {}
    res = {'noche': night, 'datos_web': upd.isoformat() if upd else None, 'ahora': now.isoformat()}
    per = next((p for p in N['periods'] if p['key'] == night), None)
    upc = next((u for u in N.get('upcoming', []) if u.get('date') == night), None)
    if hecho.get('fecha') == night: res['estado'] = 'HECHO'
    elif per and per['games'] and all(g.get('completed') for g in per['games']): res['estado'] = 'LISTO'
    elif not per and not (upc and upc['games']): res['estado'] = 'SIN_PARTIDOS'
    else:
        etas = []
        for g in (per['games'] if per else upc['games']):
            if g.get('completed') or g.get('state') == 'post': etas.append(0); continue
            if g.get('state', 'in') == 'pre' and g.get('utc'):
                tip = datetime.datetime.fromisoformat(g['utc'].replace('Z', '+00:00')); etas.append(max(0, (tip - now).total_seconds() / 60) + 140); continue
            r = _restante(g.get('status') or g.get('detail')); etas.append(r if r is not None else 30)
        mins = max(etas) if etas else 0
        # los datos de la web van con retraso: cuenta desde la última actualización
        if upd: mins = max(0, mins - (now - upd).total_seconds() / 60)
        res['estado'] = 'ESPERANDO'; res['minutos_restantes'] = round(mins); res['fin_estimado'] = hora_es((now + datetime.timedelta(minutes=mins)).strftime('%Y-%m-%dT%H:%MZ'))
        res['partidos'] = [(g['teams'][0]['abbr'] + '-' + g['teams'][1]['abbr'], g.get('status') or g.get('detail')) for g in (per['games'] if per else upc['games'])]
    if imprimir: print(json.dumps(res, ensure_ascii=False))
    return res

def actualizar_web():
    """lanza el workflow de la web y espera a que suba los datos nuevos"""
    before = subprocess.run(['gh', 'run', 'list', '-R', GH_REPO, '-w', 'actualizar.yml', '-L', '1', '--json', 'databaseId', '-q', '.[0].databaseId'], capture_output=True, text=True).stdout.strip()
    sh('gh', 'api', '-X', 'POST', f'repos/{GH_REPO}/actions/workflows/actualizar.yml/dispatches', '-f', 'ref=main')
    for _ in range(60):
        time.sleep(5)
        j = json.loads(subprocess.run(['gh', 'run', 'list', '-R', GH_REPO, '-w', 'actualizar.yml', '-L', '1', '--json', 'databaseId,status'], capture_output=True, text=True).stdout or '[]')
        if j and str(j[0]['databaseId']) != before and j[0]['status'] == 'completed': break
    sh('git', '-C', REPO, 'pull', '-q', '--rebase', 'origin', 'main')

def esperar():
    """hasta ~9 min: actualiza la web cada ~4 min y sale en cuanto la noche está LISTA (o si falta más de 55 min)"""
    t0 = time.time()
    while True:
        e = estado(False)
        if e['estado'] != 'ESPERANDO' or e.get('minutos_restantes', 0) > 55: break
        if time.time() - t0 > 7 * 60: break
        actualizar_web(); time.sleep(max(0, 240 - 60))
    print(json.dumps(estado(False), ensure_ascii=False))

def marcar_hecho():
    n = noche(); json.dump({'fecha': n['fecha'], 'hora': datetime.datetime.now(datetime.timezone.utc).isoformat()}, open(HECHO, 'w')); print('hecho', n['fecha'])

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'estado': estado, 'esperar': esperar, 'hecho': marcar_hecho, 'borrador': borrador, 'voz': voz, 'montar': montar, 'render': render,
     'fotogramas': lambda: fotogramas(sys.argv[2])}.get(cmd, lambda: print(__doc__))()
