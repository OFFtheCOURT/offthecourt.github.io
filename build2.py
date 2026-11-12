import os
import json,base64,os,datetime,urllib.parse
S=os.environ.get('OFFCOURT_DIR') or os.path.dirname(os.path.abspath(__file__)); B=S+'/build'
def b64(p): return 'data:image/webp;base64,'+base64.b64encode(open(p,'rb').read()).decode()
WD=['lunes','martes','miércoles','jueves','viernes','sábado','domingo']

# ---------- NBA -> common schema ----------
d=json.load(open(B+'/data.json')); ex=json.load(open(B+'/extra.json')); nteams=json.load(open(B+'/teams.json'))
periods=[]
for day in d['days']:
    if not day['games']: continue
    dt=datetime.date.fromisoformat(day['date'])
    mo=dt.strftime('%B')+f' {dt.day}, {dt.year}'
    for g in day['games']:
        A,H=g['teams']
        g['yt']='https://www.youtube.com/results?search_query='+urllib.parse.quote(f"{nteams[A['abbr']]['name']} vs {nteams[H['abbr']]['name']} full game highlights {mo}")
    periods.append({'key':day['date'],'label':day['date'],'games':day['games']})
up=[]
for i,u in enumerate(ex['upcoming']):
    dt=datetime.date.fromisoformat(u['date'])
    up.append({'label':'Esta noche' if i==0 else WD[dt.weekday()].capitalize(),'date':u['date'],'games':u['games']})
nba={'key':'nba','name':'NBA','periodType':'day','teams':{k:{kk:v[kk] for kk in ('abbr','name','short','color','alt')} for k,v in nteams.items()},
     'periods':periods,'upcoming':up,
     'standings':[{'name':'Conferencia Este','zones':{'po':6,'pi':10,'rel':0},'rows':ex['standings']['east']},
                  {'name':'Conferencia Oeste','zones':{'po':6,'pi':10,'rel':0},'rows':ex['standings']['west']}],
     'leaders':ex['leaders'],'teamstats':ex['teamstats'],'cal':ex.get('cal',[])}

el=json.load(open(B+'/league_el.json')); acb=json.load(open(B+'/league_acb.json'))
# colour / name touch-ups (identity colours that the crest-sampling gets wrong)
EL_FIX={'BAR':('a50044','004d98','Barça'),'MAD':('3d2b8c','fec308','Real Madrid'),'PAN':('007a3d','ffffff',None),'BAS':('9d1c25','1d3a72',None),
        'ULK':('1b2b5c','fed100','Fenerbahçe'),'RED':(None,None,'Estrella Roja'),'HTA':(None,None,'Hapoel Tel Aviv'),'TEL':('f2c500','1f3875',None),
        'MIL':(None,None,'Olimpia Milano'),'PAR':('2b2b2b','bbbbbb',None),'VIR':('2b2b2b','bbbbbb',None),'ASV':('2b2b2b','bbbbbb',None),'DUB':('1f2a44','c9a35b',None)}
ACB_FIX={'RMB':('3d2b8c','fec308',None),'SBB':('2b2b2b','e0e0e0',None),'BKN':('9d1c25','1d3a72',None),'LLT':('f2c500','1d3a72',None),'BUR':(None,None,'San Pablo Burgos'),
         'MOB':(None,None,'Monbus Obradoiro'),'MBA':(None,None,'MoraBanc Andorra'),'CAZ':(None,None,'Casademont Zaragoza'),'LLT2':(None,None,None)}
for lg,fix in ((el,EL_FIX),(acb,ACB_FIX)):
    for k,(c,a,n) in fix.items():
        if k not in lg['teams']: continue
        t=lg['teams'][k]
        if c: t['color']=c
        if a: t['alt']=a
        if n: t['short']=n

LEAGUES={'nba':nba,'el':el,'acb':acb}
# páginas por partido con vista previa propia, sitemap y robots (og.py)
if os.environ.get('OFFCOURT_OUT','').endswith('index.html'):
    try:
        import og; og.build(S,B,LEAGUES)
    except Exception as _e: print('vistas previas: error', _e)
# récords y curiosidades de la última jornada (curio.py)
try:
    import curio
    for _k,_L in LEAGUES.items(): _L['facts']=curio.facts(_k,_L,S)
except Exception as _e: print('curiosidades: error', _e)
# fichas completas (todos los jugadores) en archivos aparte: la web solo los descarga al pulsar "Ficha completa"
os.makedirs(S+'/box',exist_ok=True)
for k,lg in LEAGUES.items():
    bx={}
    for p in lg['periods']:
        for g in p['games']:
            rows=[t.pop('box',None) for t in g['teams']]
            if all(rows): bx[str(g['id'])]=rows; g['bx']=1
    json.dump(bx,open(f'{S}/box/{k}.json','w'),ensure_ascii=False,separators=(',',':'))
    print('fichas',k,len(bx))

# ---------- images ----------
# fotos de jugadores (Wikimedia Commons), generadas por photos.py en la carpeta photos/
PH=S+'/photos'
credits=json.load(open(PH+'/credits.json')) if os.path.exists(PH+'/credits.json') else {}
img={'p':{},'t':{'nba':{},'el':{},'acb':{}}}
for pid in credits:
    f=f'{PH}/{pid}.webp'
    # la foto va como archivo aparte (photos/ID.webp) y no dentro del HTML: la página pesa mucho menos y el
    # navegador solo descarga las que se ven. ?v= cambia cuando cambia la foto, para no usar una copia vieja.
    if os.path.exists(f): img['p'][pid]=f'photos/{pid}.webp?v={int(os.path.getmtime(f))%100000:x}{os.path.getsize(f)%4096:x}'
credits={k:v for k,v in credits.items() if k in img['p']}
for ab in nba['teams']: img['t']['nba'][ab]=b64(f'{B}/img/t/{ab}.webp')
for ab in el['teams']: img['t']['el'][ab]=b64(f'{B}/img/el/{ab}.webp')
for ab in acb['teams']: img['t']['acb'][ab]=b64(f'{B}/img/acb/{ab}.webp')

js=open(S+'/app.js').read()
js=js.replace('/*LEAGUES*/',json.dumps(LEAGUES,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
js=js.replace('/*LIVE*/false','true' if os.environ.get('OFFCOURT_LIVE') else 'false')
js=js.replace('/*UPDATED*/',json.dumps(datetime.datetime.now(datetime.timezone.utc).isoformat()))
js=js.replace('/*IMG*/',json.dumps(img,separators=(',',':'))).replace('/*CREDITS*/',json.dumps(credits,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
html=open(S+'/tpl_head.html').read()+js
import re as _re
def F(name):
    # admite los archivos dentro de lgl/ o sueltos en la raíz del repositorio
    a=os.path.join(S,'lgl',name)
    return a if os.path.exists(a) else os.path.join(S,name)
def svg_inline(p):
    x=open(p).read(); x=_re.sub(r'<\?xml[^>]*>','',x); return x.replace('<svg ','<svg aria-hidden="true" ',1)
html=html.replace('%%LOGO_NBA%%','<img src="data:image/webp;base64,'+base64.b64encode(open(F('nba.webp'),'rb').read()).decode()+'" alt="">')
def el_logo():
    # logo de la EuroLiga: euroleague.png (solo el balón, sin el texto) o, si no está, el emblema propio
    p=F('euroleague.png')
    if not os.path.exists(p): return svg_inline(F('el.svg'))
    from PIL import Image
    import io
    im=Image.open(p).convert('RGBA'); w,h=im.size
    px=im.load()
    for y in range(h):
        for x in range(w):
            r,g,b,a=px[x,y]
            if r>235 and g>235 and b>235: px[x,y]=(255,255,255,0)
    # se queda con la parte de arriba (el balón) si debajo hay texto
    rows=[y for y in range(h) if any(px[x,y][3]>0 for x in range(0,w,2))]
    if rows:
        gaps=[(rows[i],rows[i+1]) for i in range(len(rows)-1) if rows[i+1]-rows[i]>h*0.02]
        bottom=gaps[0][0] if gaps else rows[-1]
        im=im.crop((0,rows[0],w,bottom+1))
    bb=im.getbbox()
    if bb: im=im.crop(bb)
    im.thumbnail((96,96)); buf=io.BytesIO(); im.save(buf,'WEBP',quality=90)
    return '<img src="data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()+'" alt="">'
html=html.replace('%%LOGO_ACB%%',svg_inline(F('acb.svg'))).replace('%%LOGO_EL%%',el_logo())
# icono de la pestaña del navegador: el logo de Offcourt
m=_re.search(r'<div class="logo-slot" id="logoSlot">(<svg.*?</svg>)',html,flags=_re.S)
FAV=('<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+urllib.parse.quote(m.group(1))+'">') if m else ''
OUT=os.environ.get('OFFCOURT_OUT','noche-nba.html')
if OUT=='index.html':  # web propia: documento HTML completo
    html=('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
          '<title>Offcourt · Resultados y estadísticas de NBA, EuroLiga y ACB</title>'+FAV+'<meta name="theme-color" content="#ffffff">'
          '<meta name="description" content="Resultados, estadísticas, clasificaciones, líderes y marcadores en directo de la NBA, la EuroLiga y la ACB, actualizados cada día.">'
          '<link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="icons/apple-touch-icon.png">'
          '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Offcourt">'
          '<meta property="og:type" content="website"><meta property="og:site_name" content="Offcourt"><meta property="og:locale" content="es_ES">'
          '<meta property="og:title" content="Offcourt · El baloncesto, fuera de la pista">'
          '<meta property="og:description" content="Resultados, estadísticas y directo de NBA, EuroLiga y ACB. Actualizado cada día.">'
          '<meta property="og:url" content="https://offthecourt.github.io/"><meta property="og:image" content="https://offthecourt.github.io/icons/og.png">'
          '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
          '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://offthecourt.github.io/icons/og.png">'
          '<style>html{color-scheme:dark}body{margin:0}img{max-width:100%}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style></head><body>'+html+'</body></html>')
open(S+'/'+OUT,'w').write(html)
print('photos',len(img['p']),'size',len(html))
