# Offcourt · marcadores y fichas en directo de EuroLiga y ACB.
# Lo ejecuta GitHub Actions (directo.yml) en bucle mientras hay partidos: cada pocos minutos escribe live.json,
# que la web consulta para mostrar el resultado y la ficha completa durante el partido.
# ACB: páginas públicas de live.acb.com. EuroLiga: API pública api-live.euroleague.net.
# Código de salida: 0 = hay partidos hoy por jugar o en juego · 3 = ya no queda ninguno hoy.
import os, re, sys, json, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get
from rsc import rsc
S = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OFFCOURT_LIVE_OUT', S + '/live.json')
dec = json.JSONDecoder()
now = time.time()

src = open(S + '/index.html', encoding='utf-8').read()
i = src.find('const LG = '); j = src.find(';\n', i)
LG = json.loads(src[i + 11:j])

def num(x):
    try: return float(str(x).replace(',', '.'))
    except Exception: return 0.0
def mins(s):
    try: a, b = str(s).split(':'); return int(a) + int(b) / 60
    except Exception: return 0
def ts(u): return datetime.datetime.fromisoformat(u.replace('Z', '+00:00')).timestamp()

# partidos de hoy que ya han empezado (o están a punto) y no constan como terminados
todo = {'el': [], 'acb': []}
for lk in todo:
    for u in LG.get(lk, {}).get('upcoming', []):
        for g in u['games']:
            t0 = ts(g['utc'])
            if g.get('state') == 'post' or now > t0 + 5 * 3600: continue
            if now >= t0 - 10 * 60: todo[lk].append(g)

for x in filter(None, os.environ.get('OFFCOURT_TEST', '').split(',')):   # prueba: forzar partidos (p. ej. acb105429)
    todo['acb' if x.startswith('acb') else 'el'].append({'id': x, 'utc': '2000-01-01T00:00:00Z'})
old = json.load(open(OUT)) if os.path.exists(OUT) else {'g': {}}
res = {k: v for k, v in old.get('g', {}).items() if now - v.get('ts', 0) < 12 * 3600}   # se guardan los de hoy

# ---- ACB ----
for g in todo['acb']:
    mid = g['id'].replace('acb', '')
    try:
        page = rsc(get(f'https://live.acb.com/partidos/partido-{mid}/estadisticas').decode('utf-8', 'ignore'))
        m = re.search(r'"initialStatistics":', page)
        st = dec.raw_decode(page[m.end():])[0] if m else {}
    except Exception as e:
        print('acb', mid, 'sin datos', e); continue
    sc, box = {}, {}
    for tb in st.get('teamBoxscores') or []:
        ab = (tb.get('team') or {}).get('abbreviatedName'); q0 = next((p['stats'] for p in tb.get('statsByPeriods', []) if p.get('quarter') == 0), None)
        if not ab or not q0: continue
        rows = []
        for p in q0.get('players', []):
            if mins(p.get('playTime') or '0:00') <= 0: continue
            pl = p.get('player') or {}; n = lambda k: int(num(p.get(k, 0))); pm = n('plusMinus')
            rows.append({'pid': 'acb' + str(pl.get('id', '')), 'n': pl.get('nickname') or pl.get('firstInitialAndLastName', ''), 'num': pl.get('shirtNumber') or '',
                         'pos': pl.get('gameRole') or '', 's': 1 if p.get('isStarted') else 0, 'min': str(round(mins(p.get('playTime')))), 'pts': n('points'),
                         'fg': f"{n('twoPointersMade') + n('threePointersMade')}-{n('twoPointersAttempted') + n('threePointersAttempted')}",
                         'tp': f"{n('threePointersMade')}-{n('threePointersAttempted')}", 'ft': f"{n('freeThrowsMade')}-{n('freeThrowsAttempted')}",
                         'or': n('offRebounds'), 'dr': n('defRebounds'), 'reb': n('totalRebounds'), 'ast': n('assists'), 'stl': n('steals'), 'blk': n('blocks'),
                         'to': n('turnovers'), 'pf': n('personalFouls'), 'pm': ('+' if pm > 0 else '') + str(pm), 'val': n('rating')})
        tot = q0.get('total') or {}
        sc[ab] = int(num(tot.get('points'))) if tot.get('points') is not None else sum(r['pts'] for r in rows); box[ab] = rows
    if not sc: continue
    started = any(box.values())
    res[g['id']] = {'st': 'post' if st.get('matchFinished') else ('in' if started else 'pre'), 's': sc, 'box': box, 'ts': now}
    print('acb', mid, res[g['id']]['st'], sc)

# ---- EuroLiga (reserva: la web también lo consulta directamente) ----
API = 'https://api-live.euroleague.net/v2/competitions/E/seasons/E2026'
if todo['el']:
    rounds = {}
    for u in LG['el'].get('upcoming', []):
        rn = re.search(r'\d+', u.get('label', '')); rn = int(rn.group()) if rn else 0
        for g in u['games']: rounds[g['id']] = rn
    cache = {}
    for g in todo['el']:
        rn = rounds.get(g['id'])
        try:
            if rn not in cache: cache[rn] = {f"el{x['gameCode']}": x for x in json.loads(get(f'{API}/games?roundNumber={rn}'))['data']}
            x = cache[rn].get(g['id'])
            if not x: continue
            stt = json.loads(get(f"{API}/games/{x['gameCode']}/stats"))
        except Exception as e:
            print('el', g['id'], 'sin datos', e); continue
        sc, box = {}, {}
        for side in ('local', 'road'):
            ab = x[side]['club']['code']; rows = []
            for pl in (stt.get(side) or {}).get('players') or []:
                y = pl['stats']
                if not y.get('timePlayed'): continue
                per = pl['player']['person']; nm = per['name'].split(', '); nm = (nm[1] + ' ' + nm[0]).title() if len(nm) == 2 else per['name'].title()
                rows.append({'pid': 'el' + per['code'], 'n': nm, 'num': str(y.get('dorsal', '')), 'pos': '', 's': 1 if y.get('startFive') else 0, 'min': str(round(y['timePlayed'] / 60)),
                             'pts': int(y['points']), 'fg': f"{int(y['fieldGoalsMadeTotal'])}-{int(y['fieldGoalsAttemptedTotal'])}", 'tp': f"{int(y['fieldGoalsMade3'])}-{int(y['fieldGoalsAttempted3'])}",
                             'ft': f"{int(y['freeThrowsMade'])}-{int(y['freeThrowsAttempted'])}", 'or': int(y['offensiveRebounds']), 'dr': int(y['defensiveRebounds']),
                             'reb': int(y['totalRebounds']), 'ast': int(y['assistances']), 'stl': int(y['steals']), 'blk': int(y['blocksFavour']), 'to': int(y['turnovers']),
                             'pf': int(y['foulsCommited']), 'pm': ('+' if y['plusMinus'] > 0 else '') + str(int(y['plusMinus'])), 'val': int(y['valuation'])})
            box[ab] = rows; sc[ab] = int(x[side].get('score') or 0) or sum(r['pts'] for r in rows)
        started = any(box.values())
        res[g['id']] = {'st': 'post' if x.get('played') else ('in' if started else 'pre'), 's': sc, 'box': box, 'ts': now}
        print('el', g['id'], res[g['id']]['st'], sc)

pend = [k for k in todo['el'] + todo['acb'] if res.get(k['id'], {}).get('st') != 'post']
data = {'t': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'g': res}
new = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
if json.dumps({**old, 't': ''}, sort_keys=True) != json.dumps({**data, 't': ''}, sort_keys=True) or not os.path.exists(OUT):
    open(OUT, 'w').write(new); print('live.json actualizado')
quedan = sum(1 for lk in todo for u in LG.get(lk, {}).get('upcoming', []) for g in u['games']
             if g.get('state') != 'post' and res.get(g['id'], {}).get('st') != 'post' and -4 * 3600 < ts(g['utc']) - now < 3 * 3600)
print('pendientes hoy', quedan)
sys.exit(0 if quedan else 3)
