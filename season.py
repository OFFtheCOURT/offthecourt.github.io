# Offcourt · temporada completa por jugador (para las fichas de jugador y de equipo).
# Escribe players/<liga>.json: para cada jugador, todos sus partidos de la temporada.
# NBA: la web solo descarga los últimos días, así que se guarda un archivo histórico (data/nba_games.json)
# que se completa una vez con los partidos que falten y luego crece con cada actualización.
import os, sys, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import j, S, B
os.makedirs(S + '/players', exist_ok=True); os.makedirs(S + '/data', exist_ok=True)
API = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
MAX_FETCH = int(os.environ.get('SEASON_MAX_FETCH', '400'))

def num(x):
    try: return float(x)
    except Exception: return 0

def espn_box(eid):
    """Fila por jugador de un partido NBA (mismo formato que box/nba.json)."""
    s = j(f'{API}/summary?event={eid}'); out = {}
    for pl in s.get('boxscore', {}).get('players', []):
        ab = pl['team']['abbreviation']; grp = pl['statistics'][0]; names = grp['labels']; rows = []
        for a in grp['athletes']:
            if not a.get('stats'): continue
            m = dict(zip(names, a['stats'])); ath = a['athlete']
            rows.append({'pid': ath['id'], 'n': ath['displayName'], 'num': ath.get('jersey', ''), 'pos': ath.get('position', {}).get('abbreviation', ''),
                         's': 1 if a.get('starter') else 0, 'min': m['MIN'], 'pts': int(num(m['PTS'])), 'fg': m['FG'], 'tp': m['3PT'], 'ft': m['FT'],
                         'or': int(num(m['OREB'])), 'dr': int(num(m['DREB'])), 'reb': int(num(m['REB'])), 'ast': int(num(m['AST'])), 'stl': int(num(m['STL'])),
                         'blk': int(num(m['BLK'])), 'to': int(num(m['TO'])), 'pf': int(num(m['PF'])), 'pm': m['+/-']})
        out[ab] = rows
    return eid, out

def safe_box(eid):
    try: return espn_box(eid)
    except Exception as e: print('sin ficha', eid, e); return eid, None

def games_nba():
    arch_f = S + '/data/nba_games.json'
    arch = json.load(open(arch_f)) if os.path.exists(arch_f) else {}
    cal = json.load(open(B + '/extra.json')).get('cal', [])
    info = {c['id']: c for c in cal if c.get('done')}
    # 1) lo que ya trae la descarga diaria
    d = json.load(open(B + '/data.json'))
    for day in d['days']:
        for g in day['games']:
            if all(t.get('box') for t in g['teams']) and g['id'] in info:
                arch[g['id']] = {t['abbr']: t['box'] for t in g['teams']}
    # 2) partidos de la temporada que faltan (solo la primera vez o si hubo huecos)
    miss = [i for i in info if i not in arch][:MAX_FETCH]
    if miss: print('NBA: descargando', len(miss), 'partidos que faltan')
    with cf.ThreadPoolExecutor(8) as ex:
        for eid, box in ex.map(safe_box, miss):
            if box and len(box) == 2: arch[eid] = box
    json.dump(arch, open(arch_f, 'w'), separators=(',', ':'))
    return [(info[i], arch[i]) for i in info if i in arch]

def games_eu(lg):
    L = json.load(open(f'{B}/league_{lg}.json')); info = {c['id']: c for c in L.get('cal', []) if c.get('done')}; out = []
    for p in L['periods']:
        for g in p['games']:
            if g['id'] in info and all(t.get('box') for t in g['teams']):
                out.append((info[g['id']], {t['abbr']: t['box'] for t in g['teams']}))
    return out

for lg, games in (('nba', games_nba()), ('el', games_eu('el')), ('acb', games_eu('acb'))):
    P = {}
    for c, box in sorted(games, key=lambda x: x[0]['utc']):
        for ab, rows in box.items():
            home = ab == c['h']; opp = c['a'] if home else c['h']
            my, ot = (c['hs'], c['as']) if home else (c['as'], c['hs'])
            for r in rows:
                p = P.setdefault(r['pid'], {'n': r['n'], 'ab': ab, 'num': r.get('num', ''), 'pos': r.get('pos', ''), 'g': []})
                p['n'] = r['n']; p['ab'] = ab; p['num'] = r.get('num') or p['num']; p['pos'] = r.get('pos') or p['pos']
                # [fecha, id, rival, local(1)/visitante(0), V/D, puntos equipo, puntos rival, titular, min, pts, reb, ast, rob, tap, pér, tc, t3, tl, +/-, val]
                p['g'].append([c['utc'][:10], c['id'], opp, 1 if home else 0, 'V' if my > ot else 'D', my, ot, r.get('s', 0), r['min'], r['pts'], r['reb'], r['ast'],
                               r['stl'], r['blk'], r['to'], r['fg'], r['tp'], r['ft'], r['pm'], r.get('val', '')])
    json.dump({'p': P}, open(f'{S}/players/{lg}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('temporada', lg, len(games), 'partidos ·', len(P), 'jugadores')
