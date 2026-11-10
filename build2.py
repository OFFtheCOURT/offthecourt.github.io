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
     'leaders':ex['leaders'],'teamstats':ex['teamstats']}

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

# ---------- images ----------
credits=json.load(open(B+'/credits.json')) if os.path.exists(B+'/credits.json') else {}
img={'p':{},'t':{'nba':{},'el':{},'acb':{}}}
for pid in credits:
    f=f'{B}/img/w/{pid}.webp'
    if os.path.exists(f): img['p'][pid]=b64(f)
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
def svg_inline(p):
    x=open(p).read(); x=_re.sub(r'<\?xml[^>]*>','',x); return x.replace('<svg ','<svg aria-hidden="true" ',1)
html=html.replace('%%LOGO_NBA%%','<img src="data:image/webp;base64,'+base64.b64encode(open(S+'/lgl/nba.webp','rb').read()).decode()+'" alt="">')
html=html.replace('%%LOGO_ACB%%',svg_inline(S+'/lgl/acb.svg')).replace('%%LOGO_EL%%',svg_inline(S+'/lgl/el.svg'))
OUT=os.environ.get('OFFCOURT_OUT','noche-nba.html')
if OUT=='index.html':  # web propia: documento HTML completo
    html=('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
          '<style>html{color-scheme:dark}body{margin:0}img{max-width:100%}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style></head><body>'+html+'</body></html>')
open(S+'/'+OUT,'w').write(html)
print('photos',len(img['p']),'size',len(html))
