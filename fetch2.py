import os
import json, urllib.request, io, os, datetime, concurrent.futures as cf
from PIL import Image
S=os.environ.get('OFFCOURT_DIR') or os.path.dirname(os.path.abspath(__file__)); B=S+'/build'
API='https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
def get(u):
    with urllib.request.urlopen(u,timeout=30) as r: return r.read()
def j(u): return json.loads(get(u))
teams=json.load(open(B+'/teams.json')); byid={v['id']:k for k,v in teams.items()}
ex={}
# upcoming
up=[]
from zoneinfo import ZoneInfo
ET=datetime.datetime.now(ZoneInfo('America/New_York')).date()
for i in range(3):
    ds=(ET+datetime.timedelta(days=i)).strftime('%Y%m%d')
    sb=j(f'{API}/scoreboard?dates={ds}'); gs=[]
    for e in sb['events']:
        c=e['competitions'][0]
        tm=[]
        for comp in sorted(c['competitors'],key=lambda x:x['homeAway']!='away'):
            rec=next((r['summary'] for r in comp.get('records',[]) if r.get('type')=='total'),'')
            tm.append({'abbr':comp['team']['abbreviation'],'rec':rec,'ha':comp['homeAway'],'score':int(comp.get('score') or 0)})
        tv=[n for b in c.get('broadcasts',[]) for n in b.get('names',[])]
        odds=(c.get('odds') or [{}])[0].get('details','')
        stt=e['status']['type']
        gs.append({'id':e['id'],'utc':e['date'],'teams':tm,'tv':tv[:2],'venue':c.get('venue',{}).get('fullName',''),'odds':odds,'state':stt.get('state','pre'),'detail':stt.get('shortDetail',''),'live':f"https://www.espn.com/nba/game/_/gameId/{e['id']}"})
    up.append({'date':(ET+datetime.timedelta(days=i)).isoformat(),'games':gs})
ex['upcoming']=up
# standings
st=j('https://site.api.espn.com/apis/v2/sports/basketball/nba/standings')
conf={}
for c in st['children']:
    rows=[]
    for e in c['standings']['entries']:
        m={x['name'] if x.get('name') else x.get('displayName'):x['displayValue'] for x in e['stats']}
        m2={x.get('displayName') or x.get('name'):x['displayValue'] for x in e['stats']}
        rows.append({'abbr':e['team']['abbreviation'],'w':int(m['wins']),'l':int(m['losses']),'pct':m['winPercent'],'gb':m['gamesBehind'],'seed':int(float(m['playoffSeed'])),
          'strk':m['streak'],'l10':m2.get('Last Ten Games',''),'home':m2.get('Home',''),'road':m2.get('Road',''),'ppg':m['avgPointsFor'],'opp':m['avgPointsAgainst'],'diff':m['differential']})
    rows.sort(key=lambda r:r['seed'])
    conf['east' if 'East' in c['name'] else 'west']=rows
ex['standings']=conf
# forma real: resultado de los últimos 5 partidos, del más antiguo al más reciente
CAL={}
def form(ab):
    t=teams[ab]
    try:
        ev=j(f"{API}/teams/{t['id']}/schedule")['events']
        for e in ev:   # calendario completo de la temporada (se juntan los de los 30 equipos)
            c=e['competitions'][0]; cp={x['homeAway']:x for x in c['competitors']}
            if 'home' not in cp or 'away' not in cp: continue
            sc=lambda x:int(float((x.get('score') or {}).get('value') or 0)) if isinstance(x.get('score'),dict) else int(float(x.get('score') or 0))
            utc=e['date']; etd=(datetime.datetime.fromisoformat(utc.replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))).date().isoformat()
            CAL[e['id']]={'id':e['id'],'utc':utc,'d':etd,'a':cp['away']['team']['abbreviation'],'h':cp['home']['team']['abbreviation'],
                         'as':sc(cp['away']),'hs':sc(cp['home']),'done':bool(c['status']['type']['completed'])}
        res=[]
        for e in sorted(ev,key=lambda e:e['date']):
            c=e['competitions'][0]
            if not c['status']['type']['completed']: continue
            me=next((x for x in c['competitors'] if x['team']['id']==t['id']),None)
            if me is not None: res.append('W' if me.get('winner') else 'L')
        return ab,res[-5:]
    except Exception as x:
        print('forma',ab,x); return ab,None
with cf.ThreadPoolExecutor(8) as e: FORM=dict(e.map(form,list(teams)))
for rows in conf.values():
    for r in rows:
        if FORM.get(r['abbr']): r['form']=FORM[r['abbr']]
ex['cal']=sorted(CAL.values(),key=lambda x:x['utc'])
print('calendario NBA',len(ex['cal']))
# leaders
L=j('https://site.api.espn.com/apis/site/v3/sports/basketball/nba/leaders')['leaders']['categories']
want={'pointsPerGame':'Puntos','reboundsPerGame':'Rebotes','assistsPerGame':'Asistencias','stealsPerGame':'Robos','blocksPerGame':'Tapones','3PointsMadePerGame':'Triples por partido','fieldGoalPercentage':'% Tiros de campo','doubleDouble':'Dobles-dobles'}
heads={}
ex['leaders']=[]
for c in L:
    if c['name'] not in want: continue
    ls=[]
    for x in c['leaders'][:10]:
        a=x['athlete']; heads[a['id']]=a.get('headshot',{}).get('href','')
        ls.append({'pid':a['id'],'n':a['displayName'],'abbr':x['team']['abbreviation'],'pos':a.get('position',{}).get('abbreviation',''),'num':a.get('jersey',''),'v':x['displayValue']})
    ex['leaders'].append({'k':c['name'],'t':want[c['name']],'ls':ls})
ex['leaders'].sort(key=lambda c:list(want).index(c['k']))
# team stats
def ts(ab):
    t=teams[ab]; d=j(f"{API}/teams/{t['id']}/statistics")['results']['stats']['categories']
    m={x['name']:x['displayValue'] for c in d for x in c['stats']}
    return ab,{k:m.get(k,'') for k in ['avgPoints','avgRebounds','avgAssists','avgSteals','avgBlocks','avgTurnovers','fieldGoalPct','threePointPct','freeThrowPct','avgThreePointFieldGoalsMade','avgOffensiveRebounds','gamesPlayed']}
with cf.ThreadPoolExecutor(8) as e: ex['teamstats']=dict(e.map(ts,list(teams)))
json.dump(ex,open(B+'/extra.json','w'),separators=(',',':'),ensure_ascii=False)
def img(a):
    pid,url=a; path=f'{B}/img/p/{pid}.webp'
    if os.path.exists(path) or not url: return
    try:
        raw=get(f"https://a.espncdn.com/combiner/i?img={url.replace('https://a.espncdn.com','')}&w=200&h=146")
        Image.open(io.BytesIO(raw)).convert('RGBA').save(path,'WEBP',quality=80)
    except Exception as x: print('fail',pid,x)

ex['_heads']=list(heads)
print(len(heads), {k:len(v['games']) for k,v in enumerate(up)}, ex['teamstats']['BOS'])
json.dump(list(heads),open(B+'/leader_ids.json','w'))
