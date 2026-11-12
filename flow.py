# Offcourt · evolución del marcador (jugada a jugada) de cada partido terminado.
# flow/<liga>.json -> {id: [[segundo, puntos_visitante, puntos_local], ...]}  (solo cambios de marcador)
# NBA: ESPN (summary.plays) · ACB: live.acb.com/partidos/partido-ID/jugadas · EuroLiga: live.euroleague.net (si responde)
# Se guarda lo ya descargado: cada partido se pide una sola vez.
import os, sys, json, re, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import get, S, B
try: from rsc import rsc
except Exception: rsc = None
os.makedirs(S + '/flow', exist_ok=True)
dec = json.JSONDecoder()

def secs(q, mm, ss, qlen):
    """segundos transcurridos al final de esa jugada (reloj descendente)"""
    base = sum(qlen if i < 4 else 300 for i in range(q - 1))
    ql = qlen if q <= 4 else 300
    return base + ql - (mm * 60 + ss)

def compact(pts):
    out = []; last = None
    for t, a, h in sorted(pts, key=lambda x: x[0]):
        if last is None or (a, h) != last: out.append([int(t), int(a), int(h)]); last = (a, h)
    if out and out[0][1:] != [0, 0]: out.insert(0, [0, 0, 0])
    return out

def nba(gid):
    d = json.loads(get(f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={gid}'))
    pts = [[0, 0, 0]]
    for p in d.get('plays', []):
        try:
            q = p['period']['number']; mm, ss = p['clock']['displayValue'].split(':') if ':' in p['clock']['displayValue'] else (0, float(p['clock']['displayValue']))
            pts.append([secs(q, int(mm), int(float(ss)), 720), p['awayScore'], p['homeScore']])
        except Exception: pass
    return compact(pts)

def acb(gid):
    t = rsc(get(f'https://live.acb.com/partidos/partido-{gid.replace("acb", "")}/jugadas').decode('utf-8', 'ignore'))
    m = re.search(r'"plays":\[\{"order"', t)
    if not m: return []
    plays = dec.raw_decode(t[m.start() + 8:])[0]; pts = [[0, 0, 0]]
    for p in sorted(plays, key=lambda p: p.get('order') or 0):   # la página las da de la última a la primera
        try: pts.append([secs(int(p['quarter']), int(p['minute']), int(p['second']), 600), p['scoreAway'], p['scoreHome']])
        except Exception: pass
    return compact(pts)

def el(gid):
    code = gid.replace('el', '')
    d = json.loads(get(f'https://live.euroleague.net/api/PlayByPlay?gamecode={code}&seasoncode=E2026', tries=2))
    pts = [[0, 0, 0]]; A = B_ = 0
    for qi, k in enumerate(['FirstQuarter', 'SecondQuarter', 'ThirdQuarter', 'ForthQuarter', 'ExtraTime'], 1):
        for p in d.get(k) or []:
            if p.get('POINTS_A') is None and p.get('POINTS_B') is None: continue
            A = p.get('POINTS_A') if p.get('POINTS_A') is not None else A; B_ = p.get('POINTS_B') if p.get('POINTS_B') is not None else B_
            try: mm, ss = str(p.get('MARKERTIME') or '0:0').split(':')
            except ValueError: mm, ss = 0, 0
            q = qi if qi < 5 else 5
            pts.append([secs(q, int(mm), int(ss), 600), B_, A])   # A = local, B = visitante
    return compact(pts)

FN = {'nba': nba, 'acb': acb, 'el': el}
SRC = {'nba': lambda: [g for day in json.load(open(B + '/data.json'))['days'] for g in day['games']],
       'el': lambda: [g for p in json.load(open(B + '/league_el.json'))['periods'] for g in p['games']],
       'acb': lambda: [g for p in json.load(open(B + '/league_acb.json'))['periods'] for g in p['games']]}
for lk in ('nba', 'acb', 'el'):
    f = f'{S}/flow/{lk}.json'; old = json.load(open(f)) if os.path.exists(f) else {}
    try: games = SRC[lk]()
    except Exception as e: print('evolución', lk, 'sin datos', e); continue
    ids = [g['id'] for g in games]; miss = [i for i in ids if i not in old]
    def one(i):
        try: return i, FN[lk](i)
        except Exception as e: return i, None
    ok = 0
    with cf.ThreadPoolExecutor(6) as ex:
        for i, ser in ex.map(one, miss):
            if ser and len(ser) > 10: old[i] = ser; ok += 1
    keep = {i: old[i] for i in ids if i in old}     # solo los partidos que salen en la web
    json.dump(keep, open(f, 'w'), separators=(',', ':'))
    print('evolución', lk, len(keep), 'partidos (+%d nuevos, %d sin datos)' % (ok, len(miss) - ok))
