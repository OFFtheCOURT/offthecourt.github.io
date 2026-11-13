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

R = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(R)
LIGA = 'nba'
if '--liga' in sys.argv:
    _i = sys.argv.index('--liga'); LIGA = sys.argv[_i + 1]; del sys.argv[_i:_i + 2]
assert LIGA in ('nba', 'el', 'acb'), 'liga: nba, el o acb'
OUT = os.path.join(R, 'salida', LIGA)
NOMBRE = {'nba': 'NBA', 'el': 'EuroLiga', 'acb': 'ACB'}[LIGA]
GH_REPO = 'OFFtheCOURT/offthecourt.github.io'
os.makedirs(OUT, exist_ok=True)


def madrid(utc):
    d = datetime.datetime.fromisoformat(utc.replace('Z', '+00:00'))
    y = d.year
    def last_sun(mo): x = datetime.datetime(y, mo, 31, 1, tzinfo=datetime.timezone.utc); return x - datetime.timedelta(days=(x.weekday() + 1) % 7)
    return d + datetime.timedelta(hours=2 if last_sun(3) <= d < last_sun(10) else 1)


def dia_europeo():
    """día de la jornada europea: hora de España menos 6 h (a las 00:40 cuenta aún el día anterior)"""
    if os.environ.get('OFFCOURT_FECHA'): return os.environ['OFFCOURT_FECHA']  # solo para pruebas
    return (madrid(datetime.datetime.now(datetime.timezone.utc).isoformat()) - datetime.timedelta(hours=6)).date().isoformat()


def partidos_del_dia(lg, fecha):
    """(jugados, pendientes, ronda) de EuroLiga/ACB en una fecha (hora de España)"""
    jug = []; ronda = None
    for p in lg['periods']:
        for g in p['games']:
            if g.get('utc') and madrid(g['utc']).date().isoformat() == fecha: jug.append(g); ronda = ronda or p.get('label')
    pen = []
    for u in lg.get('upcoming', []):
        for g in u['games']:
            if g.get('utc') and madrid(g['utc']).date().isoformat() == fecha: pen.append(g); ronda = ronda or u.get('label')
    return jug, pen, ronda


def proximos(lg, fecha):
    """siguiente día con partidos de esta liga después de 'fecha'"""
    gs = sorted([g for u in lg.get('upcoming', []) for g in u['games'] if g.get('utc') and madrid(g['utc']).date().isoformat() > fecha], key=lambda g: g['utc'])
    if not gs: return None, []
    d0 = madrid(gs[0]['utc']).date().isoformat(); return d0, [g for g in gs if madrid(g['utc']).date().isoformat() == d0]
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
    L, IMG, _ = web_data(); N = L[LIGA]; T = N['teams']
    if LIGA == 'nba':
        night = N['periods'][0]; lista = night['games']; fecha = night['key']; ronda = None
    else:
        fecha = dia_europeo(); lista, pend, ronda = partidos_del_dia(N, fecha); night = {'key': fecha}
    games = []
    for g in lista:
        A, H = g['teams']
        def side(t):
            st = t.get('st') or {}
            return {'equipo': t['abbr'], 'nombre': T[t['abbr']]['name'], 'corto': T[t['abbr']]['short'], 'puntos': t['score'], 'balance': t.get('rec'),
                    'cuartos': t.get('ls'), 'triples': st.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted'), 'rebotes': st.get('totalRebounds'),
                    'asistencias': st.get('assists'), 'pintura': st.get('pointsInPaint'), 'contraataque': st.get('fastBreakPoints'), 'maxima_ventaja': st.get('largestLead'),
                    'jugadores': [{'pid': p['pid'], 'nombre': p['n'], 'pos': p.get('pos'), 'pts': p['pts'], 'reb': p['reb'], 'ast': p['ast'], 'rob': p.get('stl'), 'tap': p.get('blk'), 'valoracion': p.get('val'),
                                   'tiros': p['fg'], 'triples': p['tp'], 'tl': p['ft'], 'min': p['min'], 'masmenos': p['pm'],
                                   'foto': os.path.exists(os.path.join(REPO, 'photos', p['pid'] + '.webp'))} for p in sorted(t.get('top') or [], key=lambda p: -p['pts'])]}
        best = max((p['pts'] for t in (A, H) for p in (t.get('top') or [])), default=0)
        games.append({'partido': f"{A['abbr']}-{H['abbr']}", 'estado': g.get('status'), 'terminado': g.get('completed', g.get('status') == 'Final'),
                      'pabellon': g.get('venue'), 'ciudad': g.get('city'), 'cronica_espn': g.get('recap'), 'nota': g.get('note'),
                      'visitante': side(A), 'local': side(H), 'interes': best + max(0, 15 - abs(A['score'] - H['score']))})
    games.sort(key=lambda g: -g['interes'])
    if LIGA == 'nba':
        up = N['upcoming'][0] if N.get('upcoming') else {'games': []}; prox_fecha = None
    else:
        prox_fecha, gs = proximos(N, fecha); up = {'games': gs}
    hoy = [{'partido': f"{g['teams'][0]['abbr']}-{g['teams'][1]['abbr']}", 'visitante': T[g['teams'][0]['abbr']]['name'], 'local': T[g['teams'][1]['abbr']]['name'],
            'visitante_corto': T[g['teams'][0]['abbr']]['short'], 'local_corto': T[g['teams'][1]['abbr']]['short'],
            'hora_es': hora_es(g.get('utc'))} for g in up['games']]
    pron = json.load(open(os.path.join(R, 'pronunciacion.json'), encoding='utf-8'))
    nombres = sorted({p['nombre'] for g in games for s in ('visitante', 'local') for p in g[s]['jugadores']} | {T[a]['name'] for a in T})
    out = {'liga': LIGA, 'jornada': ronda, 'proximo_dia': prox_fecha, 'fecha': night['key'], 'actualizado_web': os.path.getmtime(os.path.join(REPO, 'index.html')), 'partidos': games, 'esta_noche': hoy,
           'lideres_temporada': N.get('leaders'), 'pronunciacion_conocida': {n: pron[n] for n in nombres if n in pron},
           'sin_pronunciacion': [n for n in nombres if n not in pron]}
    p = os.path.join(OUT, 'borrador.json'); json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(LIGA, 'fecha', night['key'], '·', len(games), 'partidos ·', len(hoy), 'próximos ->', p)


# ---------------------------------------------------------------- voz
def noche():
    return json.load(open(os.path.join(OUT, 'noche.json'), encoding='utf-8'))


def _texto(t, modo):
    return re.sub(r'\{([^|}]*)\|([^}]*)\}', lambda m: m.group(1) if modo == 'o' else m.group(2), t)


def _partir(n, vkey, d, full_t):
    """corta la locución continua en un trozo por segmento, por el centro de la pausa entre ellos"""
    modo = vkey.rsplit('_', 1)[1]; T = json.load(open(os.path.join(d, 'tiempos.json')))
    bounds = [b for b in T[vkey][0]['palabras'] if b['k'] == 'WordBoundary']
    partes = [_texto(x['t'], modo) for x in n['segmentos']]; spoken = ''; spans = []
    for ptxt in partes:
        if spoken: spoken += ' '
        spans.append((len(spoken), len(spoken) + len(ptxt))); spoken += ptxt
    low = spoken.lower(); cur = 0; por = [[] for _ in partes]
    for b in bounds:
        j = low.find(b['w'].lower(), cur)
        if j < 0: continue
        cur = j + len(b['w'])
        for k, (a, e) in enumerate(spans):
            if a <= j < e: por[k].append(b); break
    src = os.path.join(d, vkey, 'todo.mp3'); total = dur_of(src)
    ini = [p[0]['o'] if p else None for p in por]; fin = [p[-1]['o'] + p[-1]['d'] if p else None for p in por]
    cortes = [0.0]
    for k in range(len(partes) - 1):
        a = fin[k] if fin[k] is not None else cortes[-1]; b = ini[k + 1] if ini[k + 1] is not None else a
        cortes.append(round((a + b) / 2, 3))
    cortes.append(total); out = []
    for k, x in enumerate(n['segmentos']):
        a, b = cortes[k], cortes[k + 1]
        sh('ffmpeg', '-v', 'error', '-y', '-i', src, '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-c:a', 'libmp3lame', '-q:a', '2', os.path.join(d, vkey, x['id'] + '.mp3'))
        out.append({'id': x['id'], 'texto': partes[k], 'palabras': [dict(p, o=round(p['o'] - a, 3)) for p in por[k]]})
    T[vkey] = out; json.dump(T, open(os.path.join(d, 'tiempos.json'), 'w'), ensure_ascii=False)
    print('locución continua partida en', len(out), 'trozos')


def voz():
    n = noche()
    if n.get('continua', True):
        vkey = n.get('voz', 'es-ES-AlvaroNeural:r').replace(':', '_'); d = os.path.join(OUT, 'voz')
        full = ' '.join(x['t'] for x in n['segmentos'])
        for intento in range(3):
            t_ = full if intento == 0 else full.replace('. ', ', ', intento)
            _voz_una_vez(dict(n, segmentos=[{'id': 'todo', 't': t_}]))
            if os.path.getsize(os.path.join(d, vkey, 'todo.mp3')) > 2000: break
        else:
            sys.exit('la voz sale vacía')
        _partir(n, vkey, d, t_); return
    _voz_una_vez()
    n = noche(); vkey = n.get('voz', 'es-ES-AlvaroNeural:r').replace(':', '_'); d = os.path.join(OUT, 'voz')
    for intento in range(2):
        vacios = [x['id'] for x in n['segmentos'] if os.path.getsize(os.path.join(d, vkey, x['id'] + '.mp3')) < 2000]
        if not vacios: return
        print('fragmentos vacíos, se regeneran con una variante:', vacios)
        guardado = json.load(open(os.path.join(d, 'tiempos.json'))); arch = {x: open(os.path.join(d, vkey, x + '.mp3'), 'rb').read() for x in [y['id'] for y in n['segmentos']] if x not in vacios}
        var = lambda t: (t.replace('. ', ', ', 1) if intento == 0 else 'Ojo: ' + t[0].lower() + t[1:])
        n2 = dict(n, segmentos=[dict(x, t=var(x['t'])) for x in n['segmentos'] if x['id'] in vacios])
        _voz_una_vez(n2)
        nuevo = {x['id']: x for x in json.load(open(os.path.join(d, 'tiempos.json')))[vkey]}
        guardado[vkey] = [nuevo.get(x['id'], x) for x in guardado[vkey]]
        for x, b in arch.items(): open(os.path.join(d, vkey, x + '.mp3'), 'wb').write(b)
        json.dump(guardado, open(os.path.join(d, 'tiempos.json'), 'w'), ensure_ascii=False)
        for x in n['segmentos']:
            if x['id'] in vacios: x['t'] = var(x['t'])
        json.dump(n, open(os.path.join(OUT, 'noche.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit('la voz sigue saliendo vacía en: ' + ', '.join(vacios))


def _voz_local(n, voice):
    """locución con edge-tts aquí mismo (GitHub Actions): mismo resultado que voz.yml"""
    import asyncio, edge_tts
    name, modo = voice.split(':') if ':' in voice else (voice, 'o'); vkey = f'{name}_{modo}'
    d = os.path.join(OUT, 'voz'); shutil.rmtree(d, ignore_errors=True); os.makedirs(os.path.join(d, vkey))
    rate, tono = n.get('velocidad', '+12%'), n.get('tono', '+2Hz'); res = []
    async def una(s):
        t = _texto(s['t'], modo); f = os.path.join(d, vkey, s['id'] + '.mp3')
        for intento in range(5):
            pal = []
            try:
                c = edge_tts.Communicate(t, name, rate=rate, pitch=tono, boundary='WordBoundary')
                with open(f, 'wb') as fh:
                    async for ch in c.stream():
                        if ch['type'] == 'audio': fh.write(ch['data'])
                        elif ch['type'] in ('WordBoundary', 'SentenceBoundary'): pal.append({'w': ch['text'], 'o': ch['offset'] / 1e7, 'd': ch['duration'] / 1e7, 'k': ch['type']})
                if os.path.getsize(f) < 2000: raise RuntimeError('audio vacío')
                return {'id': s['id'], 'texto': t, 'palabras': pal}
            except Exception as e:
                print('reintento voz', s['id'], repr(e)); await asyncio.sleep(3 + 4 * intento)
        raise SystemExit('la voz sale vacía')
    async def todas():
        for s in n['segmentos']: res.append(await una(s))
    asyncio.run(todas())
    json.dump({vkey: res}, open(os.path.join(d, 'tiempos.json'), 'w'), ensure_ascii=False)
    print('voz local lista:', vkey)


def _voz_una_vez(n=None):
    n = n or noche(); voice = n.get('voz', 'es-ES-AlvaroNeural:r')
    if os.environ.get('OFFCOURT_TTS_LOCAL'): return _voz_local(n, voice)
    guion = [{'id': s['id'], 't': s['t']} for s in n['segmentos']]
    payload = {'ref': 'main', 'inputs': {'guion': base64.b64encode(json.dumps(guion, ensure_ascii=False).encode()).decode(), 'voces': voice, 'rate': n.get('velocidad', '+12%'), 'tono': n.get('tono', '+2Hz')}}
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
    for m in re.finditer(r'([¡¿"(]*)\{([^|}]*)\|([^}]*)\}([^\s{]*)|(\S+)', tpl):
        if m.group(5) is not None:
            w = m.group(5)
            if out and re.fullmatch(r'[.,:;!?…]+', w): out[-1]['o'] += w; out[-1]['r'] += w; continue
            out.append({'o': w, 'r': w})
        else:
            pre, post = m.group(1), m.group(4)
            out.append({'o': pre + m.group(2) + post, 'r': pre + m.group(3) + post, 'name': True, 'key': m.group(2)})
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
            words.append({'w': w, 'o': round(x['o'] + k * step, 3), 'd': round(step, 3), 'name': bool(x['u'].get('name')), 'src': x['u'].get('key') or x['u']['o'].strip('.,:;!?…¡¿')})
    return words


KEEP = 0.34
# voz como la del vídeo de referencia (@iabsia_agency): más rápida, más clara y con presencia, sin eco ni oscurecer
SUAVE = 'highpass=f=80,equalizer=f=200:t=q:w=1:g=1.5,equalizer=f=3000:t=q:w=1.2:g=2,equalizer=f=7500:t=q:w=2:g=-2,acompressor=threshold=-18dB:ratio=2.2:attack=10:release=180'
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
    flt += ''.join(f'[a{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=0:a=1[c];[c]{SUAVE}[o]'
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
    try: tpm = int((pl.get('tp') or '0-0').split('-')[0])
    except ValueError: tpm = 0
    return {'three': tpm >= 3, 'big': (pl.get('pos') == 'C' or pl.get('reb', 0) >= 10) and tpm < 3}


def montar():
    DATA_CINE = True  # portada de sala de cine en las tres ligas (telón: NBA rojo, EuroLiga naranja, ACB negro)
    n = noche(); L, IMG, logo = web_data(); N = L[LIGA]; T = N['teams']; LOG = IMG['t'][LIGA]
    vkey = n.get('voz', 'es-ES-AlvaroNeural:r').replace(':', '_'); mode = vkey.rsplit('_', 1)[1]
    vdir = os.path.join(OUT, 'voz'); TIMES = json.load(open(os.path.join(vdir, 'tiempos.json')))[vkey]
    if LIGA == 'nba': night = next(p for p in N['periods'] if p['key'] == n['fecha']); ronda = None
    else: _j, _p, ronda = partidos_del_dia(N, n['fecha']); night = {'games': _j}
    games = {g['teams'][0]['abbr'] + '-' + g['teams'][1]['abbr']: g for g in night['games']}
    os.makedirs(os.path.join(OUT, 'audio'), exist_ok=True)
    PAD_IN, PAD_OUT = (0.05, 0.04) if n.get('continua', True) else (0.22, 0.18)
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
            scenes.append({'type': 'intro', 'id': 'intro', 'dur': round(max(3.6, d + PAD_IN + (.75 if DATA_CINE else .35)), 2), 'off': PAD_IN, 'words': w}); continue
        if seg['id'] == 'outro':
            ton = []; hl = []
            for g in ((N['upcoming'][0]['games'] if N.get('upcoming') else []) if LIGA == 'nba' else proximos(N, n['fecha'])[1]):
                a, h = g['teams'][0]['abbr'], g['teams'][1]['abbr']; used |= {a, h}
                ton.append({'a': h, 'h': a, 'an': T[h]['short'], 'hn': T[a]['short'], 'time': hora_es(g.get('utc'))})  # local a la izquierda
                k = (seg.get('resaltar') or {}).get(f'{a}-{h}'); hl.append(when(k) if k else None)
            scenes.append({'type': 'outro', 'id': 'outro', 'dur': round(d + PAD_IN + 1.7, 2), 'off': PAD_IN, 'words': w, 'hl': hl, 'tonight': ton}); continue
        g = games[seg['partido']]; Hm, A = g['teams']; used |= {A['abbr'], Hm['abbr']}  # A = local (izquierda), Hm = visitante (derecha)
        tA, tH = team_obj(A['abbr'], A, T), team_obj(Hm['abbr'], Hm, T)
        cards = []; marks = []
        for c in seg.get('tarjetas', []):
            wt = when(c['clave'])
            if c.get('stat') or 'pid' not in c:
                ti = 0 if c['equipo'] == A['abbr'] else 1; tm_ = (A, Hm)[ti]; st = tm_.get('st') or {}
                if c.get('stat') == 'triples':
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
        nx = scenes[i + 1]; sc['next'] = [nx['teams'][1]['c'], nx['teams'][0]['c']] if nx['type'] == 'game' else [{'nba': '#2f7bff', 'el': '#ff7a1a', 'acb': '#1fbf75'}[LIGA], {'nba': '#e5383b', 'el': '#386eff', 'acb': '#2f6bff'}[LIGA]]
    f = datetime.date.fromisoformat(n['fecha']); f2 = f + datetime.timedelta(days=1)
    if LIGA != 'nba':
        pd = proximos(N, n['fecha'])[0]
        if pd: f2 = datetime.date.fromisoformat(pd)
    ETQ = {'nba': ('LA NOCHE NBA', 'LA NOCHE', 'NBA', 'ESTA NOCHE'),
           'el': (f"EUROLIGA · {(ronda or '').upper()}", 'J' + re.sub(r'\D', '', ronda or '') if ronda else 'LA JORNADA', 'EUROLIGA', 'PRÓXIMOS'),
           'acb': (f"ACB · {(ronda or '').upper()}", 'J' + re.sub(r'\D', '', ronda or '') if ronda else 'LA JORNADA', 'ACB', 'PRÓXIMOS')}[LIGA]
    outro = next((s for s in scenes if s['type'] == 'outro'), None); ton = outro['tonight'] if outro else []
    DATA = {'eyebrow': ETQ[0], 'title1': ETQ[1], 'title2': ETQ[2], 'outTitle': ETQ[3], 'dateLabel': f'{ABR_D[f.weekday()]} {f.day} {ABR_M[f.month - 1]}', 'dateLong': f'{DIAS[f.weekday()]} {f.day} de {MESES[f.month - 1]}',
            'tonightLabel': f'{ABR_D[f2.weekday()]} {f2.day} {ABR_M[f2.month - 1]}', 'tonightCount': f'{len(ton)} PARTIDOS · HORA ESPAÑOLA',
            'ngames': len(narrated), 'scenes': scenes, 'tonight': ton,
            'mini': [{'a': g['teams'][1]['abbr'], 'h': g['teams'][0]['abbr'], 'as': g['teams'][1]['score'], 'hs': g['teams'][0]['score']} for g in night['games'] if g['teams'][0].get('score') is not None],
            'logos': {k: LOG[k] for k in used | {g['teams'][i]['abbr'] for g in night['games'] for i in (0, 1)} if k in LOG}, 'photos': photos,
            'logo': 'data:image/svg+xml;base64,' + base64.b64encode(logo.encode()).decode()}
    DATA['results'] = []
    DATA['theme'] = {'nba': {'a': '#4d94ff', 'b': '#ff5a66', 'bg': '#13213f', 'tela': '#a3122a'}, 'el': {'a': '#ff7a1a', 'b': '#386eff', 'tela': '#ff7a1a'}, 'acb': {'a': '#1fbf75', 'b': '#2f6bff', 'tela': '#141414'}}[LIGA]
    for _g in night['games']:
        _H, _A = _g['teams']  # [visitante, local]
        if _A.get('score') is None or _H.get('score') is None: continue
        _ot = len(_A.get('ls') or []) > 4; _m = abs(_A['score'] - _H['score'])
        _top = max([p for p in (_A.get('top') or []) + (_H.get('top') or [])], key=lambda p: p.get('pts', 0), default=None)
        _tag, _sc = None, 0
        if _ot: _tag, _sc = 'PRÓRROGA', 3
        elif _m <= 3: _tag, _sc = 'FINAL DE INFARTO', 2.5
        elif _m >= 25: _tag, _sc = f'PALIZA +{_m}', 2
        if _top and _top.get('pts', 0) >= (40 if LIGA == 'nba' else 30) and _sc < 2.6: _tag, _sc = f"{_top['pts']} DE {_top['n'].split(' ')[-1].upper()}", 2.6
        DATA['results'].append({'l': team_obj(_A['abbr'], _A, T), 'v': team_obj(_H['abbr'], _H, T), 'ot': _ot, 'tag': _tag, '_s': _sc + min(1, 10 / (1 + _m)) * .1})
    _best = sorted(range(len(DATA['results'])), key=lambda i: -DATA['results'][i]['_s'])[:2]
    for i, r in enumerate(DATA['results']):
        r['hot'] = i in _best and r['tag'] is not None; r.pop('_s')
    DATA['results'].sort(key=lambda r: (not r['hot'],))
    # portada de cine (NBA): focos = ganchos de la intro, la cámara vuela a cada pantalla
    if DATA_CINE and DATA['results']:
        DATA['cine'] = True
        intro = next((x for x in scenes if x['type'] == 'intro'), None); seg = next((x for x in n['segmentos'] if x['id'] == 'intro'), {})
        focos = []
        for f_ in seg.get('focos', []):
            a_, h_ = f_['partido'].split('-')
            idx = next((i for i, r in enumerate(DATA['results']) if r['l']['ab'] == h_ and r['v']['ab'] == a_), None)
            tt = next((w['o'] for w in intro['words'] if w['src'] == f_['clave']), None)
            if tt is None: tt = next((w['o'] for w in intro['words'] if f_['clave'].split()[-1].lower() in w['src'].lower()), None)
            if idx is not None and tt is not None: focos.append({'i': idx, 't': round(tt - .12, 3), 'tag': f_.get('etiqueta') or DATA['results'][idx].get('tag')})
        if not focos:
            hot = [i for i, r in enumerate(DATA['results']) if r.get('tag')][:4] or [0]
            focos = [{'i': i, 't': round(.5 + k * (intro['dur'] - 1.2) / len(hot), 3), 'tag': DATA['results'][i].get('tag')} for k, i in enumerate(hot)]
        intro['focos'] = focos
        nxt = scenes[scenes.index(intro) + 1] if scenes.index(intro) + 1 < len(scenes) else None
        if nxt and nxt['type'] == 'game': nxt['fromCine'] = True; intro.pop('next', None)
    _hero = {x['id'] for x in n['segmentos'] if x.get('hero')}
    for _sc in scenes:
        if _sc.get('id') in _hero: _sc['hero'] = True
    open(os.path.join(OUT, 'data.js'), 'w', encoding='utf-8').write('window.DATA=' + json.dumps(DATA, ensure_ascii=False) + ';')
    # guarda en el diccionario las pronunciaciones usadas
    pf = os.path.join(R, 'pronunciacion.json'); pron = json.load(open(pf, encoding='utf-8')); nuevo = 0
    for s in n['segmentos']:
        for m in re.finditer(r'\{([^|}]*)\|([^}]*)\}', s['t']):
            if m.group(1) not in pron: pron[m.group(1)] = m.group(2); nuevo += 1
    json.dump(dict(sorted(pron.items())), open(pf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('escenas', [(s['id'], s['dur']) for s in scenes], 'total', round(sum(s['dur'] for s in scenes), 1), 's · fotos', len(photos), '· pronunciaciones nuevas', nuevo)
    if sum(s['dur'] for s in scenes) > 60: print('AVISO: el vídeo dura más de 60 s; acorta las frases (se narran todos los partidos, pero con una frase corta cada uno)')


# ---------------------------------------------------------------- render
def fotogramas(lst):
    shutil.copy(os.path.join(OUT, 'data.js'), os.path.join(R, 'salida', 'data.js'))
    sh('node', os.path.join(R, 'render.js'), 'frames', lst)


def _sfx(d):
    """efectos sintetizados (sin derechos): golpe, pop y barrido"""
    import wave
    try:
        import numpy as np
    except ImportError:
        return
    SR = 48000
    def save(n, x):
        w = wave.open(os.path.join(d, n), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    t = np.arange(int(SR * .7)) / SR; save('boom.wav', .9 * np.sin(2 * np.pi * (50 * t + 80 / 12 * (1 - np.exp(-t * 12)))) * np.exp(-t * 6))
    t = np.arange(int(SR * .22)) / SR; save('pop.wav', .6 * np.sin(2 * np.pi * (900 * t - 250 * t * t)) * np.exp(-t * 18))
    t = np.arange(int(SR * 3.2)) / SR; r = np.random.default_rng(5).standard_normal(len(t)); r = np.convolve(r, np.ones(30) / 30, 'same') - np.convolve(r, np.ones(400) / 400, 'same')
    env = np.minimum(1, t / .15) * np.exp(-np.maximum(0, t - 1.2) * 1.2) * (1 + .35 * np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * .7 * t)); save('crowd.wav', r * env * 2.2)
    # "pick": tono de anuncio estilo draft (composición propia): arpegio de campanas brillante + acorde de metales
    def bell(f, dur, amp=1.):
        tt = np.arange(int(SR * dur)) / SR
        return amp * sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * k) for m, a, k in ((1, 1, 3.5), (2.76, .35, 7), (5.4, .18, 12), (8.9, .08, 20))) * np.minimum(1, tt / .003)
    def brass(fs, dur):
        tt = np.arange(int(SR * dur)) / SR; v = 1 + .004 * np.sin(2 * np.pi * 5.5 * tt)
        x = sum(sum(np.sin(2 * np.pi * f * h * tt * v) / h ** 1.3 for h in range(1, 9)) for f in fs)
        return x / len(fs) * np.minimum(1, tt / .04) * np.exp(-np.maximum(0, tt - .35) * 2.6) * .32
    def put(buf, x, at): i = int(at * SR); buf[i:i + len(x)] += x[:len(buf) - i]
    pk = np.zeros(int(SR * 1.6))
    for k, f in enumerate((587.3, 784.0, 987.8, 1174.7)): put(pk, bell(f, 1.2, .42), k * .085)
    put(pk, brass((293.7, 370.0, 440.0, 587.3), 1.2), .33)
    tt = np.arange(int(SR * .5)) / SR; put(pk, .5 * np.sin(2 * np.pi * 73 * tt) * np.exp(-tt * 7), .33)
    save('pick.wav', pk / np.abs(pk).max() * .85)
    pk2 = np.zeros(int(SR * 1.0))
    put(pk2, bell(784.0, .9, .5), 0); put(pk2, bell(1174.7, .9, .5), .09)
    save('pick2.wav', pk2 / np.abs(pk2).max() * .8)
    # si el usuario deja su propio tono en redes/sonidos/pick.(wav|mp3|m4a), se usa ese
    for ext in ('wav', 'mp3', 'm4a'):
        own = os.path.join(R, 'sonidos', 'pick.' + ext)
        if os.path.exists(own):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', own, '-ac', '1', '-ar', str(SR), os.path.join(d, 'pick.wav')], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', own, '-t', '1.2', '-af', 'afade=t=out:st=.9:d=.3', '-ac', '1', '-ar', str(SR), os.path.join(d, 'pick2.wav')], check=True); break
    t = np.arange(int(SR * .4)) / SR; r = np.random.default_rng(1).standard_normal(len(t)); r = np.convolve(r, np.ones(8) / 8, 'same') - np.convolve(r, np.ones(60) / 60, 'same'); save('whoosh.wav', r * np.sin(np.pi * t / .4) ** 2 * .5)


def render():
    shutil.copy(os.path.join(OUT, 'data.js'), os.path.join(R, 'salida', 'data.js'))
    D = json.loads(open(os.path.join(OUT, 'data.js'), encoding='utf-8').read()[len('window.DATA='):-1]); n = noche()
    esc = os.path.join(OUT, 'escenas'); shutil.rmtree(esc, ignore_errors=True); os.makedirs(esc)
    # OFFCOURT_HASTA=10 → solo los primeros 10 s (para probar la portada sin renderizar todo)
    HASTA = float(os.environ.get('OFFCOURT_HASTA') or 0)
    if HASTA:
        acc_ = 0; keep = 0
        for sc in D['scenes']:
            if acc_ < HASTA: keep += 1
            acc_ += sc['dur']
        D['scenes'] = D['scenes'][:keep]
    # Como mucho 3 Chrome a la vez: con 10+ partidos, lanzar todas las escenas juntas agota la memoria y Chrome se cae.
    from concurrent.futures import ThreadPoolExecutor
    def una(i):
        for _ in range(2):
            if subprocess.call(['node', os.path.join(R, 'render.js'), 'scene', str(i), os.path.join(esc, f's{i}.mp4')]) == 0: return 0
        return 1
    with ThreadPoolExecutor(3) as ex: fallos = sum(ex.map(una, range(len(D['scenes']))))
    if fallos: sys.exit('ha fallado el render de alguna escena')
    for i, sc in enumerate(D['scenes']):
        vd = dur_of(os.path.join(esc, f's{i}.mp4'))
        sh('ffmpeg', '-v', 'error', '-y', '-i', os.path.join(OUT, 'audio', sc['id'] + '.wav'), '-af', f"adelay={int(sc['off'] * 1000)},apad=whole_dur={vd:.3f},loudnorm=I=-15:TP=-1.5:LRA=7",
           '-ar', '48000', '-ac', '2', os.path.join(esc, f'a{i}.wav'))
    # efectos de sonido: barrido en cada cambio, golpe al entrar cada partido, pop en cada tarjeta
    sfx = os.path.join(OUT, 'sfx'); os.makedirs(sfx, exist_ok=True); _sfx(sfx)
    starts = []; acc = 0
    for sc in D['scenes']: starts.append(acc); acc += sc['dur']
    ev = [('boom', 0.0)]
    intro_ = next((x for x in D['scenes'] if x['type'] == 'intro'), {})
    if intro_.get('focos'):
        # sin petardos: tono de draft al empezar y campanilla en cada titular
        ev = [('pick', 0.0)] + [x for f_ in intro_['focos'][1:] for x in (('whoosh', max(0, f_['t'] - .12)), ('pick2', f_['t']))] + [('whoosh', intro_['dur'] - .5), ('boom', intro_['dur'] - .1)]
    nm = len(D['mini'])
    if not intro_.get('focos'): ev += [('pop', .15 + i * min(.1, .8 / max(1, nm))) for i in range(nm)]
    for i, sc in enumerate(D['scenes']):
        if i: ev.append(('whoosh', starts[i] - .15))
        if sc['type'] == 'game':
            ev.append(('boom', starts[i] + .05)); ev += [('pop', starts[i] + c['t']) for c in sc.get('cards', [])]
        if sc['type'] == 'outro': ev += [('pop', starts[i] + h) for h in sc.get('hl', []) if h is not None]
    if HASTA: ev = [e for e in ev if e[1] < HASTA]
    vol = {'boom': .55, 'pop': .4, 'whoosh': .45, 'crowd': .5, 'pick': .6, 'pick2': .45}
    open(os.path.join(esc, 'v.txt'), 'w').write(''.join(f"file 's{i}.mp4'\n" for i in range(len(D['scenes']))))
    open(os.path.join(esc, 'a.txt'), 'w').write(''.join(f"file 'a{i}.wav'\n" for i in range(len(D['scenes']))))
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(esc, 'v.txt'), '-c', 'copy', os.path.join(esc, 'v.mp4'))
    sh('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(esc, 'a.txt'), '-c:a', 'pcm_s16le', os.path.join(esc, 'a.wav'))
    inp = ['-i', os.path.join(esc, 'a.wav')]; flt = []
    for k, (nme, tt) in enumerate(ev):
        inp += ['-i', os.path.join(sfx, nme + '.wav')]; flt.append(f'[{k + 1}]adelay={int(max(0, tt) * 1000)}|{int(max(0, tt) * 1000)},volume={vol[nme]}[e{k}]')
    flt.append('[0]' + ''.join(f'[e{k}]' for k in range(len(ev))) + f'amix=inputs={len(ev) + 1}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[o]')
    sh('ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', ';'.join(flt), '-map', '[o]', '-ar', '48000', '-ac', '2', os.path.join(esc, 'mix.wav'))
    shutil.move(os.path.join(esc, 'mix.wav'), os.path.join(esc, 'a.wav'))
    final = os.path.join(OUT, f"offcourt_{'noche_nba' if LIGA == 'nba' else LIGA}_{n['fecha']}{'_prueba' if HASTA else ''}.mp4")
    sh('ffmpeg', '-v', 'error', '-y', '-i', os.path.join(esc, 'v.mp4'), '-i', os.path.join(esc, 'a.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
       '-shortest', *(['-t', str(HASTA)] if HASTA else []), '-movflags', '+faststart', final)
    if HASTA: print('prueba:', final); return
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

def hecho_de(lg):
    if os.environ.get('OFFCOURT_IGNORA_HECHO'): return None   # el automático lleva su propio registro (redes/videos.json)
    h = json.load(open(HECHO)) if os.path.exists(HECHO) else {}
    if 'fecha' in h and lg == 'nba': return h['fecha']
    return (h.get(lg) or {}).get('fecha')

def estado_europa(imprimir):
    L, _, _ = web_data(); N = L[LIGA]; now = datetime.datetime.now(datetime.timezone.utc)
    fecha = dia_europeo(); jug, pen, ronda = partidos_del_dia(N, fecha)
    res = {'liga': LIGA, 'noche': fecha, 'jornada': ronda, 'jugados': len(jug), 'pendientes': len(pen), 'ahora': now.isoformat()}
    if hecho_de(LIGA) == fecha: res['estado'] = 'HECHO'
    elif not jug and not pen: res['estado'] = 'SIN_PARTIDOS'
    elif not pen: res['estado'] = 'LISTO'
    else:
        etas = []
        for g in pen:
            tip = datetime.datetime.fromisoformat(g['utc'].replace('Z', '+00:00'))
            etas.append(max(0, (tip - now).total_seconds() / 60) + 125 if g.get('state', 'pre') == 'pre' else 40)
        res['estado'] = 'ESPERANDO'; res['minutos_restantes'] = round(max(etas))
    if imprimir: print(json.dumps(res, ensure_ascii=False))
    return res

def estado(imprimir=True):
    if LIGA != 'nba': return estado_europa(imprimir)
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
    if hecho_de('nba') == night: res['estado'] = 'HECHO'
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
    """hasta ~9 min: actualiza la web cada ~4 min y sale en cuanto la noche está LISTA (o si falta más de 100 min)"""
    t0 = time.time()
    while True:
        e = estado(False)
        if e['estado'] != 'ESPERANDO' or e.get('minutos_restantes', 0) > 100: break
        if time.time() - t0 > 7 * 60: break
        actualizar_web(); time.sleep(max(0, 240 - 60))
    print(json.dumps(estado(False), ensure_ascii=False))

def marcar_hecho():
    n = noche(); h = json.load(open(HECHO)) if os.path.exists(HECHO) else {}
    if 'fecha' in h: h = {'nba': {'fecha': h['fecha'], 'hora': h.get('hora')}}
    h[LIGA] = {'fecha': n['fecha'], 'hora': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    json.dump(h, open(HECHO, 'w'), indent=1); print('hecho', LIGA, n['fecha'])

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'estado': estado, 'esperar': esperar, 'hecho': marcar_hecho, 'borrador': borrador, 'voz': voz, 'montar': montar, 'render': render,
     'fotogramas': lambda: fotogramas(sys.argv[2])}.get(cmd, lambda: print(__doc__))()
