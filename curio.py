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
    f = os.path.join(S, 'players', lk + '.json')
    if not os.path.exists(f) or not L.get('periods'): return []
    P = json.load(open(f))['p']; T = L['teams']
    night = {g['id'] for g in L['periods'][0]['games']}
    short = lambda ab: (T.get(ab) or {}).get('short', ab)
    out = []
    def add(score, kind, text, **k): out.append(dict(s=score, k=kind, t=text, **k))
    # todas las actuaciones de la temporada
    allg = [(pid, p, g) for pid, p in P.items() for g in p['g']]
    if not allg: return []
    cats = [('pts', 'puntos', 25 if lk != 'nba' else 35), ('reb', 'rebotes', 12 if lk != 'nba' else 16), ('ast', 'asistencias', 9 if lk != 'nba' else 13)]
    if lk != 'nba': cats.append(('val', 'de valoración', 30))
    for pid, p, g in allg:
        if g[G['id']] not in night: continue
        n = p['n']; tm = short(p['ab']); before = [x for x in p['g'] if x[G['date']] < g[G['date']]]
        for k, lbl, thr in cats:
            v = _num(g[G[k]])
            if v < thr: continue
            league_max = max(_num(x[G[k]]) for _, _, x in allg if x[G['id']] != g[G['id']] or x is g)
            others = [_num(x[G[k]]) for q, _, x in allg if not (q == pid and x[G['id']] == g[G['id']])]
            if v >= max(others or [0]):
                add(90 + v / 10, 'crown', f'{n} firma {int(v)} {lbl}: el récord de la temporada en la {"NBA" if lk=="nba" else ("EuroLiga" if lk=="el" else "ACB")}.', pid=pid, gid=g[G['id']])
            elif before and v > max(_num(x[G[k]]) for x in before):
                add(55 + v / 10, 'fire', f'{n} ({tm}) hace su mejor marca del año: {int(v)} {lbl}.', pid=pid, gid=g[G['id']])
        # dobles y triples-dobles
        dd = sum(1 for k in ('pts', 'reb', 'ast', 'stl', 'blk') if _num(g[G[k]]) >= 10)
        if dd >= 3:
            prev = sum(1 for x in p['g'] if sum(1 for k in ('pts', 'reb', 'ast', 'stl', 'blk') if _num(x[G[k]]) >= 10) >= 3)
            add(85, 'star', f'Triple-doble de {n}: {g[G["pts"]]} puntos, {g[G["reb"]]} rebotes y {g[G["ast"]]} asistencias' + (f' (el {prev}º de su temporada).' if prev > 1 else ', el primero de su temporada.'), pid=pid, gid=g[G['id']])
        elif dd == 2 and _num(g[G['pts']]) >= 20 and _num(g[G['reb']]) >= 15:
            add(50, 'star', f'Doble-doble enorme de {n}: {g[G["pts"]]} puntos y {g[G["reb"]]} rebotes.', pid=pid, gid=g[G['id']])
        # puntería perfecta
        fm, fa = _pair(g[G['fg']])
        if fa >= (8 if lk == 'nba' else 6) and fm == fa:
            add(60 + fa, 'target', f'Puntería perfecta de {n}: {fm} de {fa} en tiros de campo.', pid=pid, gid=g[G['id']])
        tm3, ta3 = _pair(g[G['tp']])
        if tm3 >= (8 if lk == 'nba' else 6):
            mx3 = max([_pair(x[G['tp']])[0] for q, _, x in allg if not (q == pid and x[G['id']] == g[G['id']])] or [0])
            add(70 + tm3, 'bolt', f'{n} mete {tm3} triples' + (', el máximo de la temporada.' if tm3 >= mx3 else '.'), pid=pid, gid=g[G['id']])
    # equipos: rachas, mayor anotación y mayor paliza
    cal = sorted([c for c in L.get('cal', []) if c.get('done')], key=lambda c: c['utc'])
    if cal:
        streak = {}
        for c in cal:
            hw = c['hs'] > c['as']
            for ab, w in ((c['h'], hw), (c['a'], not hw)):
                s = streak.get(ab, 0); streak[ab] = (s + 1 if s >= 0 else 1) if w else (s - 1 if s <= 0 else -1)
        played = {ab for c in cal if c['id'] in night for ab in (c['h'], c['a'])}
        best = max(streak.values()); worst = min(streak.values())
        for ab in played:
            s = streak.get(ab, 0)
            if s >= 4: add(60 + s * 2 + (15 if s == best else 0), 'fire', f'{short(ab)} suma {s} victorias seguidas' + (', la mejor racha de la liga.' if s == best else '.'), ab=ab)
            if s <= -5: add(40 + abs(s), 'ice', f'{short(ab)} encadena {abs(s)} derrotas seguidas' + (', la peor racha de la liga.' if s == worst else '.'), ab=ab)
            w = sum(1 for c in cal if (c['h'] == ab and c['hs'] > c['as']) or (c['a'] == ab and c['as'] > c['hs']))
            won_now = any(c['id'] in night and ((c['h'] == ab and c['hs'] > c['as']) or (c['a'] == ab and c['as'] > c['hs'])) for c in cal)
            if won_now and w == 1 and len([c for c in cal if ab in (c['h'], c['a'])]) >= 4: add(65, 'star', f'¡Por fin! Primera victoria de la temporada para {short(ab)}.', ab=ab)
        for c in cal:
            if c['id'] not in night: continue
            for ab, pts in ((c['h'], c['hs']), (c['a'], c['as'])):
                if pts >= max(max(x['hs'], x['as']) for x in cal):
                    add(75, 'crown', f'{short(ab)} anota {pts} puntos, la mayor anotación de la temporada.', ab=ab, gid=c['id'])
            m = abs(c['hs'] - c['as'])
            if m >= 20 and m >= max(abs(x['hs'] - x['as']) for x in cal):
                wn = c['h'] if c['hs'] > c['as'] else c['a']; ls = c['a'] if wn == c['h'] else c['h']
                add(70, 'bolt', f'La mayor paliza del año: {short(wn)} gana de {m} a {short(ls)}.', ab=wn, gid=c['id'])
    # quitar repetidos del mismo jugador (se queda el más interesante) y ordenar
    out.sort(key=lambda x: -x['s']); seen = set(); res = []
    for x in out:
        key = (x.get('pid'), x['k']) if x.get('pid') else (x.get('ab'), x['k'], x['t'][:20])
        if key in seen: continue
        seen.add(key); res.append({k: v for k, v in x.items() if k != 's'})
    return res[:8]

if __name__ == '__main__':
    import sys
    S = os.path.dirname(os.path.abspath(__file__)); src = open(S + '/index.html', encoding='utf-8').read()
    i = src.find('const LG = '); j = src.find(';\nconst UPDATED', i); LG = json.loads(src[i + 11:j])
    for lk in (sys.argv[1:] or ['nba', 'el', 'acb']):
        print('==', lk); [print(' ', x['k'], x['t']) for x in facts(lk, LG[lk], S)]
