# Offcourt · fotos de jugadores desde Wikimedia Commons (licencias libres)
# Busca cada jugador en Wikipedia, toma su foto libre, la recorta por la cara y guarda autor y licencia.
# Lo ejecuta GitHub Actions (fotos.yml) una vez por semana; solo busca jugadores nuevos.
import os, re, io, json, time, html, urllib.request, urllib.parse, unicodedata
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__))
PH = S + '/photos'; os.makedirs(PH, exist_ok=True)
REPO = os.environ.get('GITHUB_REPOSITORY', 'martisosa/OFFCOURT')
OWNER, NAME = REPO.split('/')
SITE = f'https://{NAME.lower()}/' if NAME.lower().endswith('.github.io') else f'https://{OWNER.lower()}.github.io/{NAME}/'
UA = {'User-Agent': f'OffcourtBot/1.0 ({SITE}; fotos de jugadores para una web personal)'}
MAX_SEARCH = int(os.environ.get('MAX_SEARCH', '150'))   # búsquedas sueltas por ejecución
RECROP = os.environ.get('RECROP') == '1'                 # volver a descargar y recortar todas las fotos
STYLE = os.environ.get('STYLE') == '1'                   # aplicar el patrón Offcourt (sin fondo + fondo del equipo)
MAX_PHOTOS = int(os.environ.get('MAX_PHOTOS', '120'))   # fotos procesadas por ejecución (se hace por tandas)
DEADLINE = time.time() + 60 * float(os.environ.get('MAX_MIN', '55'))   # y como mucho estos minutos
ONLY = [x for x in os.environ.get('ONLY', '').replace(' ', '').split(',') if x]   # limitar a estos jugadores
import facecrop
W, H = 200, 146

def get(u, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r: return r.read()
        except Exception as e:
            print('reintento', i, str(e)[:80]); time.sleep(15 * (i + 1))
    return None
def api(host, params):
    params.update(format='json', formatversion='2'); time.sleep(1.5)
    raw = get(f'https://{host}/w/api.php?' + urllib.parse.urlencode(params))
    return json.loads(raw) if raw else {}
def norm(x): return unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()
def isbb(pp): return 'basketball' in (pp or {}).get('wikibase-shortdesc', '').lower()

# --- jugadores que salen en la web (se leen del index.html actual) ---
src = open(S + '/index.html', encoding='utf-8').read()
i = src.find('const LG = '); j = src.find(';\nconst UPDATED', i)
LG = json.loads(src[i + 11:j])
names = {}; info = {}
for lk, lg in LG.items():
    for p in lg['periods']:
        for g in p['games']:
            for t in g['teams']:
                for x in t['top']: names[x['pid']] = x['n']; info[x['pid']] = (lk, t['abbr'], x.get('num', ''))
    for c in lg['leaders']:
        for x in c['ls']:
            names[x['pid']] = x['n']
            if x['pid'] not in info: info[x['pid']] = (lk, x['abbr'], x.get('num', ''))
if ONLY: names = {k: v for k, v in names.items() if k in ONLY}
print('jugadores', len(names))

idx_f, cr_f = PH + '/index.json', PH + '/credits.json'
st_f = PH + '/styled.json'                                # jugadores que ya tienen el patrón Offcourt
styled = set(json.load(open(st_f))) if os.path.exists(st_f) else set()
idx = json.load(open(idx_f)) if os.path.exists(idx_f) else {}
credits = json.load(open(cr_f)) if os.path.exists(cr_f) else {}
def save():
    json.dump(idx, open(idx_f, 'w'), ensure_ascii=False, indent=0)
    json.dump(credits, open(cr_f, 'w'), ensure_ascii=False, indent=0)
    json.dump(sorted(styled), open(st_f, 'w'))

# --- 1) páginas de Wikipedia por título exacto y "(basketball)" ---
for suf in ['', ' (basketball)']:
    todo = [p for p in names if p not in idx]
    for i in range(0, len(todo), 50):
        tmap = {names[p] + suf: p for p in todo[i:i + 50]}
        r = api('en.wikipedia.org', {'action': 'query', 'titles': '|'.join(tmap), 'redirects': 1, 'prop': 'pageprops',
                                     'ppprop': 'page_image_free|wikibase-shortdesc'})
        q = r.get('query', {}); back = {}
        for n in q.get('normalized', []): back[n['to']] = n['from']
        for n in q.get('redirects', []): back[n['to']] = back.get(n['from'], n['from'])
        for pg in q.get('pages', []):
            pid = tmap.get(back.get(pg['title'], pg['title']))
            if pid and isbb(pg.get('pageprops')):
                idx[pid] = {'title': pg['title'], 'file': pg['pageprops'].get('page_image_free')}
    save()
# --- 2) búsqueda para el resto (limitada por ejecución) ---
n = 0
for pid in [p for p in names if p not in idx]:
    if n >= MAX_SEARCH: break
    n += 1
    parts = [w for w in names[pid].split() if w not in ('Jr.', 'Jr', 'II', 'III', 'IV', 'Sr.')]
    last = norm(parts[-1]) if parts else ''
    r = api('en.wikipedia.org', {'action': 'query', 'generator': 'search', 'gsrsearch': names[pid] + ' basketball player', 'gsrlimit': 3,
                                 'prop': 'pageprops', 'ppprop': 'page_image_free|wikibase-shortdesc'})
    pages = sorted(r.get('query', {}).get('pages', []), key=lambda x: x.get('index', 9))
    hit = next((pg for pg in pages if isbb(pg.get('pageprops')) and last and last in norm(pg['title'])), None)
    idx[pid] = {'title': hit['title'], 'file': hit['pageprops'].get('page_image_free')} if hit else {'title': None, 'file': None}
    if n % 20 == 0: save()
save()

# --- 3) autor y licencia en Commons + descarga ---
need = {v['file']: pid for pid, v in idx.items() if v.get('file') and (not ONLY or pid in ONLY) and (
    (RECROP and not (STYLE and pid in styled and not ONLY)) or (pid in names and not os.path.exists(f'{PH}/{pid}.webp')))}
pending = len(need)
need = dict(list(need.items())[:MAX_PHOTOS])
print('pendientes', pending, '· en esta tanda', len(need), flush=True)
files = list(need)
meta = {}
for i in range(0, len(files), 40):
    r = api('commons.wikimedia.org', {'action': 'query', 'titles': '|'.join('File:' + f for f in files[i:i + 40]), 'prop': 'imageinfo',
                                      'iiprop': 'url|extmetadata', 'iiurlwidth': 500, 'iiextmetadatafilter': 'Artist|LicenseShortName'})
    for pg in r.get('query', {}).get('pages', []):
        if 'imageinfo' not in pg: continue
        ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
        art = html.unescape(re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', ''))).strip()
        meta[pg['title'][5:].replace(' ', '_')] = {'thumb': ii.get('thumburl'), 'page': ii['descriptionurl'], 'artist': art[:120] or 'Autor desconocido',
                                                   'lic': em.get('LicenseShortName', {}).get('value', '')}
ok = 0
done = 0
for f, pid in need.items():
    if time.time() > DEADLINE: print('tiempo agotado: sigue en la próxima tanda', flush=True); break
    done += 1
    mt = meta.get(f.replace(' ', '_'))
    if not mt or not mt['thumb']: styled.add(pid); continue      # sin foto descargable: no reintentar en cada tanda
    srcf = f'{PH}/src/{pid}.webp'
    if os.path.exists(srcf) and pid in credits:
        orig = Image.open(srcf).convert('RGB')                    # original ya guardado: no hace falta descargarlo
    else:
        raw = get(mt['thumb'].replace('https://thumb.wikimedia.org/', 'https://upload.wikimedia.org/').split('?')[0]); time.sleep(1.5)
        if not raw: styled.add(pid); continue                     # descarga fallida: no bloquear las tandas
        orig = Image.open(io.BytesIO(raw)).convert('RGB')
    os.makedirs(f'{PH}/src', exist_ok=True); orig.save(f'{PH}/src/{pid}.webp', 'WEBP', quality=80)   # original, para re-estilizar sin volver a descargar
    if STYLE and pid in info:
        import stylize
        lk, ab, num = info[pid]; tm = LG[lk]['teams'][ab]
        img = stylize.card(orig, tm['color'], tm['alt'], num, 300, 219)
    else:
        img, _ = facecrop.crop(orig, W, H)
    img.save(f'{PH}/{pid}.webp', 'WEBP', quality=84)
    credits[pid] = {'a': mt['artist'], 'l': mt['lic'], 'u': mt['page']}; ok += 1
    if STYLE: styled.add(pid)
    if ok % 10 == 0: save(); print('hechas', ok, flush=True)
save()
open(PH + '/pending.txt', 'w').write(str(max(0, pending - done)))
print('quedan', max(0, pending - done), flush=True)
print('fotos nuevas', ok, '· total', sum(1 for p in credits if os.path.exists(f'{PH}/{p}.webp')), 'de', len(names), 'jugadores')
