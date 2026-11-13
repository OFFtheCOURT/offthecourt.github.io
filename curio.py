# Offcourt · récords y curiosidades automáticas de la última jornada (las usa build2.py)
# Compara cada actuación de la última noche/jornada con toda la temporada (players/<liga>.json)
# y las rachas de los equipos con el calendario. Devuelve una lista ordenada por interés.
import os, json
G = dict(date=0, id=1, opp=2, home=3, res=4, my=5, ot=6, st=7, min=8, pts=9, reb=10, ast=11, stl=12, blk=13, to=14, fg=15, tp=16, ft=17, pm=18, val=19)

def _pair(x):
    try: a, b = str(x).split('-'); return int(a), int(b)
    except Exception: return 0, 0

def _num(x):
    try: return float(x)
    except Exception: return 0

def facts(lk, L, S):
    """lo más destacado de la última noche/jornada: 4 tarjetas como mucho, cada una con un número grande,
    una unidad, el protagonista, una línea de contexto y una etiqueta corta"""
    f = os.path.join(S, 'players', lk + '.json')
    if not os.path.exists(f) or not L.get('periods'): return []
    P = json.load(open(f))['p']; T = L['teams']
    games = {g['id']: g for g in L['periods'][0]['games']}
    night = set(games)
    short = lambda ab: (T.get(ab) or {}).get('short', ab)
    liga = {'nba': 'NBA', 'el': 'EuroLiga', 'acb': 'ACB'}.get(lk, '')
    def gline(gid):
        g = games.get(gid)
        if not g or len(g.get('teams', [])) < 2: return '', 0
        a, h = g['teams'][0], g['teams'][1]; ot = max(0, len(a.get('ls') or []) - 4)
        return f"{a['abbr']} {a['score']}-{h['score']} {h['abbr']}", ot
    def otx(n): return '' if not n else (' · prórroga' if n == 1 else f' · {n} prórrogas')
    out = []
    def add(score, kind, num, unit, who, line, tag, text, **k):
        out.append(dict(s=score, k=kind, n=str(num), u=unit, w=who, d=line, tag=tag, t=text, **k))
    allg = [(pid, p, g) for pid, p in P.items() for g in p['g']]
    if not allg: return []
    eu = lk != 'nba'
    cats = [('pts', 'PTS', 'puntos', 25 if eu else 35, 2.4 if eu else 1.6), ('reb', 'REB', 'rebotes', 12 if eu else 16, 3.5 if eu else 3),
            ('ast', 'AST', 'asistencias', 10 if eu else 13, 4 if eu else 3.5)]
    if eu: cats.append(('val', 'VAL', 'de valoración', 30, 2.2))
    for pid, p, g in allg:
        gid = g[G['id']]
        if gid not in night: continue
        n = p['n']; tm = short(p['ab']); before = [x for x in p['g'] if x[G['date']] < g[G['date']]]
        gl, ot = gline(gid); ctx = gl + otx(ot)
        for k, u, lbl, thr, w in cats:
            v = _num(g[G[k]])
            if v < thr: continue
            others = [_num(x[G[k]]) for q, _, x in allg if not (q == pid and x[G['id']] == gid)]
            if v >= max(others or [0]):
                add(100 + v * w / 10, 'crown', int(v), u, n, ctx, f'RÉCORD {liga.upper()}', f'{n} firma {int(v)} {lbl}: el récord de la temporada en la {liga}.', pid=pid, gid=gid, ab=p['ab'])
            elif before and v > max(_num(x[G[k]]) for x in before):
                add(v * w + 8, 'fire', int(v), u, n, ctx, 'MÁXIMO DEL AÑO', f'{n} ({tm}) hace su mejor marca del año: {int(v)} {lbl}.', pid=pid, gid=gid, ab=p['ab'])
            elif k == 'pts' and v >= (30 if eu else 40):
                add(v * w, 'fire', int(v), u, n, ctx, 'EXHIBICIÓN', f'{n} ({tm}) anota {int(v)} puntos.', pid=pid, gid=gid, ab=p['ab'])
        dd = sum(1 for k in ('pts', 'reb', 'ast', 'stl', 'blk') if _num(g[G[k]]) >= 10)
        if dd >= 3:
            prev = sum(1 for x in p['g'] if sum(1 for k in ('pts', 'reb', 'ast', 'stl', 'blk') if _num(x[G[k]]) >= 10) >= 3)
            tot = _num(g[G['pts']]) + _num(g[G['reb']]) + _num(g[G['ast']])
            add(62 + tot / 3, 'star', f"{int(_num(g[G['pts']]))}·{int(_num(g[G['reb']]))}·{int(_num(g[G['ast']]))}", 'PTS · REB · AST', n,
                ctx, 'TRIPLE-DOBLE', f'Triple-doble de {n}: {g[G["pts"]]} puntos, {g[G["reb"]]} rebotes y {g[G["ast"]]} asistencias' + (f' (el {prev}º de su temporada).' if prev > 1 else ', el primero de su temporada.'), pid=pid, gid=gid, ab=p['ab'])
        elif dd == 2 and _num(g[G['pts']]) >= 25 and _num(g[G['reb']]) >= 15:
            add(52, 'star', f"{int(_num(g[G['pts']]))}·{int(_num(g[G['reb']]))}", 'PTS · REB', n, ctx, 'DOBLE-DOBLE', f'Doble-doble de {n}: {g[G["pts"]]} puntos y {g[G["reb"]]} rebotes.', pid=pid, gid=gid, ab=p['ab'])
        fm, fa = _pair(g[G['fg']])
        if fa >= (9 if not eu else 7) and fm == fa:
            add(58 + fa, 'target', f'{fm}/{fa}', 'EN TIROS', n, ctx, 'PUNTERÍA PERFECTA', f'Puntería perfecta de {n}: {fm} de {fa} en tiros de campo.', pid=pid, gid=gid, ab=p['ab'])
        tm3, ta3 = _pair(g[G['tp']])
        if tm3 >= (8 if not eu else 6):
            mx3 = max([_pair(x[G['tp']])[0] for q, _, x in allg if not (q == pid and x[G['id']] == gid)] or [0])
            add(55 + tm3 * 3 + (12 if tm3 >= mx3 else 0), 'bolt', tm3, 'TRIPLES', n, ctx, 'RÉCORD DE TRIPLES' if tm3 >= mx3 else 'LLUVIA DE TRIPLES',
                f'{n} mete {tm3} triples' + (', el máximo de la temporada.' if tm3 >= mx3 else '.'), pid=pid, gid=gid, ab=p['ab'])
    # partidos: prórrogas y finales ajustados
    for gid, g in games.items():
        if len(g.get('teams', [])) < 2 or not g.get('completed', True): continue
        a, h = g['teams'][0], g['teams'][1]; gl, ot = gline(gid); m = abs(a['score'] - h['score'])
        wn, ls = (a, h) if a['score'] > h['score'] else (h, a)
        if ot: add(66 + 8 * ot, 'bolt', ot, 'PRÓRROGA' if ot == 1 else 'PRÓRROGAS', f"{short(wn['abbr'])} {wn['score']}-{ls['score']} {short(ls['abbr'])}", 'Partidazo hasta el final', 'PARTIDAZO', f'{short(wn["abbr"])} gana {wn["score"]}-{ls["score"]} a {short(ls["abbr"])} tras {ot} prórroga(s).', ab=wn['abbr'], gid=gid)
        elif m <= 2: add(64, 'bolt', f'+{m}', 'AL LÍMITE', f"{short(wn['abbr'])} {wn['score']}-{ls['score']} {short(ls['abbr'])}", 'Se decidió en la última posesión', 'FINAL DE INFARTO', f'{short(wn["abbr"])} gana {wn["score"]}-{ls["score"]} a {short(ls["abbr"])} por {m}.', ab=wn['abbr'], gid=gid)
    # equipos: rachas, primera victoria, anotación y paliza del año
    cal = sorted([c for c in L.get('cal', []) if c.get('done')], key=lambda c: c['utc'])
    if cal:
        streak = {}
        for c in cal:
            hw = c['hs'] > c['as']
            for ab, w in ((c['h'], hw), (c['a'], not hw)):
                s = streak.get(ab, 0); streak[ab] = (s + 1 if s >= 0 else 1) if w else (s - 1 if s <= 0 else -1)
        played = {ab for c in cal if c['id'] in night for ab in (c['h'], c['a'])}
        best = max(streak.values()); worst = min(streak.values())
        last = {}
        for c in cal:
            if c['id'] in night:
                for ab, op, me, ot_ in ((c['h'], c['a'], c['hs'], c['as']), (c['a'], c['h'], c['as'], c['hs'])): last[ab] = f'{me}-{ot_} a {short(op)}'
        for ab in played:
            s = streak.get(ab, 0)
            if s >= 4: add(48 + s * 3 + (14 if s == best else 0), 'fire', s, 'SEGUIDAS', short(ab), 'Última: ' + last.get(ab, ''), 'MEJOR RACHA' if s == best else 'EN RACHA', f'{short(ab)} suma {s} victorias seguidas' + (', la mejor racha de la liga.' if s == best else '.'), ab=ab)
            if s <= -6 and s == worst: add(40 + abs(s), 'ice', abs(s), 'DERROTAS', short(ab), 'Última: ' + last.get(ab, ''), 'EN CAÍDA LIBRE', f'{short(ab)} encadena {abs(s)} derrotas seguidas, la peor racha de la liga.', ab=ab)
            w = sum(1 for c in cal if (c['h'] == ab and c['hs'] > c['as']) or (c['a'] == ab and c['as'] > c['hs']))
            won_now = any(c['id'] in night and ((c['h'] == ab and c['hs'] > c['as']) or (c['a'] == ab and c['as'] > c['hs'])) for c in cal)
            if won_now and w == 1 and len([c for c in cal if ab in (c['h'], c['a'])]) >= 4: add(68, 'star', '1ª', 'VICTORIA', short(ab), last.get(ab, ''), '¡POR FIN!', f'¡Por fin! Primera victoria de la temporada para {short(ab)}.', ab=ab)
        for c in cal:
            if c['id'] not in night: continue
            for ab, pts in ((c['h'], c['hs']), (c['a'], c['as'])):
                if pts >= max(max(x['hs'], x['as']) for x in cal):
                    add(72, 'crown', pts, 'PUNTOS', short(ab), 'La mayor anotación de la temporada', 'RÉCORD DEL AÑO', f'{short(ab)} anota {pts} puntos, la mayor anotación de la temporada.', ab=ab, gid=c['id'])
            m = abs(c['hs'] - c['as'])
            if m >= 20 and m >= max(abs(x['hs'] - x['as']) for x in cal):
                wn = c['h'] if c['hs'] > c['as'] else c['a']; ls = c['a'] if wn == c['h'] else c['h']
                add(70, 'bolt', f'+{m}', 'PALIZA', short(wn), f'{max(c["hs"], c["as"])}-{min(c["hs"], c["as"])} a {short(ls)}', 'PALIZA DEL AÑO', f'La mayor paliza del año: {short(wn)} gana de {m} a {short(ls)}.', ab=wn, gid=c['id'])
    # selección: lo más interesante, sin repetir jugador, como mucho 2 por partido y 1 racha
    out.sort(key=lambda x: -x['s']); res = []; pids = set(); per_game = {}; streaks = 0
    for x in out:
        if x.get('pid') and x['pid'] in pids: continue
        gid = x.get('gid')
        if gid and per_game.get(gid, 0) >= 3: continue
        if x['k'] in ('fire', 'ice') and not x.get('pid'):
            if streaks >= 1: continue
            streaks += 1
        # si el partido ya sale por un jugador, la prórroga va en su línea y no como tarjeta aparte
        if x['tag'] == 'PARTIDAZO' and gid in per_game: continue
        if x.get('pid'): pids.add(x['pid'])
        if gid: per_game[gid] = per_game.get(gid, 0) + 1
        res.append({k: v for k, v in x.items() if k != 's'})
        if len(res) == 8: break
    return res

if __name__ == '__main__':
    import sys
    S = os.path.dirname(os.path.abspath(__file__)); src = open(S + '/index.html', encoding='utf-8').read()
    i = src.find('const LG = '); j = src.find(';\nconst UPDATED', i); LG = json.loads(src[i + 11:j])
    for lk in (sys.argv[1:] or ['nba', 'el', 'acb']):
        print('==', lk); [print(' ', x['tag'], '|', x['n'], x['u'], '|', x['w'], '|', x['d']) for x in facts(lk, LG[lk], S)]
