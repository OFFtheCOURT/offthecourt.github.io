# Offcourt · fotos de jugadores desde Wikimedia Commons (licencias libres)
# Busca cada jugador en Wikipedia, toma su foto libre, la recorta por la cara y guarda autor y licencia.
# Lo ejecuta GitHub Actions (fotos.yml) una vez por semana; solo busca jugadores nuevos.
import os, re, io, json, time, html, urllib.request, urllib.parse, unicodedata
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__))
PH = S + '/photos'; os.makedirs(PH, exist_ok=True)
REPO = os.environ.get('GITHUB_REPOSITORY', 'martisosa/OFFCOURT')
OWNER, NAME = REPO.split('/')
UA = {'User-Agent': f'OffcourtBot/1.0 (https://{OWNER.lower()}.github.io/{NAME}/; fotos de jugadores para una web personal)'}
MAX_SEARCH = int(os.environ.get('MAX_SEARCH', '150'))   # búsquedas sueltas por ejecución
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
names = {}
for lg in LG.values():
    for p in lg['periods']:
        for g in p['games']:
            for t in g['teams']:
                for x in t['top']: names[x['pid']] = x['n']
    for c in lg['leaders']:
        for x in c['ls']: names[x['pid']] = x['n']
print('jugadores', len(names))

idx_f, cr_f = PH + '/index.json', PH + '/credits.json'
idx = json.load(open(idx_f)) if os.path.exists(idx_f) else {}
credits = json.load(open(cr_f)) if os.path.exists(cr_f) else {}
def save():
    json.dump(idx, open(idx_f, 'w'), ensure_ascii=False, indent=0)
    json.dump(credits, open(cr_f, 'w'), ensure_ascii=False, indent=0)

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
need = {v['file']: pid for pid, v in idx.items() if v.get('file') and pid in names and not os.path.exists(f'{PH}/{pid}.webp')}
files = list(need)
meta = {}
for i in range(0, len(files), 40):
    r = api('commons.wikimedia.org', {'action': 'query', 'titles': '|'.join('File:' + f for f in files[i:i + 40]), 'prop': 'imageinfo',
                                      'iiprop': 'url|extmetadata', 'iiurlwidth': 330, 'iiextmetadatafilter': 'Artist|LicenseShortName'})
    for pg in r.get('query', {}).get('pages', []):
        if 'imageinfo' not in pg: continue
        ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
        art = html.unescape(re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', ''))).strip()
        meta[pg['title'][5:].replace(' ', '_')] = {'thumb': ii.get('thumburl'), 'page': ii['descriptionurl'], 'artist': art[:120] or 'Autor desconocido',
                                                   'lic': em.get('LicenseShortName', {}).get('value', '')}
try:
    import cv2, numpy as np
    CASC = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except Exception:
    CASC = None
ok = 0
for f, pid in need.items():
    mt = meta.get(f.replace(' ', '_'))
    if not mt or not mt['thumb']: continue
    raw = get(mt['thumb'].replace('https://thumb.wikimedia.org/', 'https://upload.wikimedia.org/').split('?')[0]); time.sleep(1.5)
    if not raw: continue
    im = Image.open(io.BytesIO(raw)).convert('RGB'); w, h = im.size
    face = None
    if CASC is not None:
        g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
        fs = CASC.detectMultiScale(g, 1.1, 5, minSize=(int(w * .06), int(w * .06)))
        if len(fs): face = max(fs, key=lambda r: r[2] * r[3])
    if face is not None:
        x, y, fw, fh = face; cw = min(w, fw * 3.4); ch = cw * H / W
        if ch > h: ch = h; cw = ch * W / H
        cx, cy = x + fw / 2, y + fh * 0.95
    else:
        cw = w; ch = cw * H / W
        if ch > h: ch = h; cw = ch * W / H
        cx, cy = w / 2, ch / 2 + h * 0.05
    l = max(0, min(w - cw, cx - cw / 2)); t = max(0, min(h - ch, cy - ch / 2))
    im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((W, H), Image.LANCZOS).save(f'{PH}/{pid}.webp', 'WEBP', quality=80)
    credits[pid] = {'a': mt['artist'], 'l': mt['lic'], 'u': mt['page']}; ok += 1
    if ok % 25 == 0: save()
save()
print('fotos nuevas', ok, '· total', sum(1 for p in credits if os.path.exists(f'{PH}/{p}.webp')), 'de', len(names), 'jugadores')
