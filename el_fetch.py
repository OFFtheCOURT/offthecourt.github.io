import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
import concurrent.futures as cf, datetime, re
API='https://api-live.euroleague.net'; C='E'; SEA='E2026'
os.makedirs(B+'/img/el',exist_ok=True)

def nice(name):
    # "ALSTON JR. , DERRICK" -> "Derrick Alston Jr."
    if ',' in name:
        last,first=[x.strip() for x in name.split(',',1)]
        name=f'{first} {last}'
    return ' '.join(w.capitalize() if not re.match(r'^(II|III|IV)$',w) else w for w in name.split()).replace('Jr.','Jr.')

allg=j(f'{API}/v2/competitions/{C}/seasons/{SEA}/games')['data']
allg=[g for g in allg if g['phaseType']['code']=='RS']
played=[g for g in allg if g['played']]
last_round=max(g['round'] for g in played)
print('played',len(played),'last round',last_round)

teams={}
def team_of(club):
    c=club['code']
    if c not in teams:
        teams[c]={'abbr':c,'name':club['name'],'short':club.get('editorialName') or club['abbreviatedName'],'crest':club['images']['crest']}
    return c
for g in allg: team_of(g['local']['club']); team_of(g['road']['club'])

# logos + colours
for c,t in teams.items():
    im=save_logo(t['crest'],f'{B}/img/el/{c}.webp')
    t['color'],t['alt']=dominant(im)

recs=records([{'id':g['gameCode'],'date':g['utcDate'],'home':g['local']['club']['code'],'away':g['road']['club']['code'],'hs':g['local']['score'],'as':g['road']['score'],'played':g['played']} for g in allg])

def box(code): return code, j(f'{API}/v3/competitions/{C}/seasons/{SEA}/games/{code}/stats')
with cf.ThreadPoolExecutor(8) as ex: boxes=dict(ex.map(box,[g['gameCode'] for g in played]))

def mmss(sec): return str(round(sec/60))
def team_side(g,side,bx):
    s=g[side]; c=s['club']['code']; opp=g['road' if side=='local' else 'local']
    p=s['partials']; ls=[p.get(f'partials{i}') for i in range(1,5)]+[v for k,v in sorted((p.get('extraPeriods') or {}).items())]
    ls=[x for x in ls if x is not None]
    b=bx['local' if side=='local' else 'road']; T=b['total']['totals'] if 'totals' in b.get('total',{}) else b['total']
    st={
      'fieldGoalsMade-fieldGoalsAttempted':f"{int(T['fieldGoalsMadeTotal'])}-{int(T['fieldGoalsAttemptedTotal'])}",
      'fieldGoalPct':pct(T['fieldGoalsMadeTotal'],T['fieldGoalsAttemptedTotal']),
      'threePointFieldGoalsMade-threePointFieldGoalsAttempted':f"{int(T['fieldGoalsMade3'])}-{int(T['fieldGoalsAttempted3'])}",
      'threePointFieldGoalPct':pct(T['fieldGoalsMade3'],T['fieldGoalsAttempted3']),
      'freeThrowsMade-freeThrowsAttempted':f"{int(T['freeThrowsMade'])}-{int(T['freeThrowsAttempted'])}",
      'freeThrowPct':pct(T['freeThrowsMade'],T['freeThrowsAttempted']),
      'totalRebounds':str(int(T['totalRebounds'])),'offensiveRebounds':str(int(T['offensiveRebounds'])),
      'assists':str(int(T['assistances'])),'steals':str(int(T['steals'])),'blocks':str(int(T['blocksFavour'])),
      'totalTurnovers':str(int(T['turnovers'])),'valuation':str(int(T['valuation'])),'foulsReceived':str(int(T['foulsReceived']))}
    top=[]
    for pl in b['players']:
        x=pl['stats']
        if not x.get('timePlayed'): continue
        per=pl['player']['person']; pid='el'+per['code']
        top.append({'pid':pid,'n':nice(per['name']),'pos':{'Guard':'B','Forward':'A','Center':'P'}.get(pl['player'].get('positionName'),''),'num':str(x.get('dorsal','')),'st':bool(x.get('startFive')),
          'min':mmss(x['timePlayed']),'pts':int(x['points']),'reb':int(x['totalRebounds']),'ast':int(x['assistances']),'stl':int(x['steals']),'blk':int(x['blocksFavour']),
          'to':int(x['turnovers']),'fg':f"{int(x['fieldGoalsMadeTotal'])}-{int(x['fieldGoalsAttemptedTotal'])}",'tp':f"{int(x['fieldGoalsMade3'])}-{int(x['fieldGoalsAttempted3'])}",
          'ft':f"{int(x['freeThrowsMade'])}-{int(x['freeThrowsAttempted'])}",'pm':('+' if x['plusMinus']>0 else '')+str(int(x['plusMinus'])),'gs':x['valuation'],'val':int(x['valuation'])})
    top.sort(key=lambda z:(-z['gs'],-z['pts'])); top=top[:5]
    return {'abbr':c,'ha':'home' if side=='local' else 'away','score':s['score'],'win':s['score']>opp['score'],'rec':recs.get((g['gameCode'],c),''),'ls':ls,'st':st,'top':top}

def mkgame(g):
    bx=boxes[g['gameCode']]
    A=team_side(g,'road',bx); H=team_side(g,'local',bx)
    v=g.get('venue') or {}
    city=(v.get('address') or '').split('-')[-1].strip() if v.get('address') else ''
    return {'id':'el'+str(g['gameCode']),'status':'Final','venue':(v.get('name') or '').title(),'city':city,'att':g.get('audience',0),'utc':g['utcDate'],
            'teams':[A,H],'videos':[],
            'yt':'https://www.youtube.com/results?search_query='+urllib.parse.quote(f"{teams[A['abbr']]['name']} vs {teams[H['abbr']]['name']} highlights EuroLeague round {g['round']}")}
import urllib.parse
periods=[]
for r in range(last_round,0,-1):
    gs=[g for g in played if g['round']==r]
    if not gs: continue
    ds=sorted(g['utcDate'] for g in gs)
    periods.append({'key':f'r{r}','round':r,'label':f'Jornada {r}','from':ds[0][:10],'to':ds[-1][:10],'games':[mkgame(g) for g in sorted(gs,key=lambda x:x['utcDate'])]})

# upcoming: next two rounds
upcoming=[]
for r in sorted({g['round'] for g in allg if not g['played']})[:2]:
    gs=sorted([g for g in allg if g['round']==r and not g['played']],key=lambda x:x['utcDate'])
    upcoming.append({'label':f'Jornada {r}','date':gs[0]['utcDate'][:10],'games':[{'id':'el'+str(g['gameCode']),'utc':g['utcDate'],
        'teams':[{'abbr':g['road']['club']['code'],'rec':'','score':g['road'].get('score') or 0},{'abbr':g['local']['club']['code'],'rec':'','score':g['local'].get('score') or 0}],'venue':((g.get('venue') or {}).get('name') or '').title(),'tv':[],'odds':'',
        'state':'in' if (g['road'].get('score') or g['local'].get('score')) else 'pre','live':'https://www.euroleaguebasketball.net/euroleague/game-center/'} for g in gs]})

# standings
bst=j(f'{API}/v3/competitions/{C}/seasons/{SEA}/rounds/{last_round}/basicstandings')['teams']
rows=[]
cur={}
for t in bst:
    c=t['club']['code']; form=t.get('last5Form') or []
    # current streak
    k=0; lastres=form[-1] if form else ''
    for x in reversed(form):
        if x==lastres: k+=1
        else: break
    gp=t['gamesPlayed'] or 1
    rows.append({'abbr':c,'w':t['gamesWon'],'l':t['gamesLost'],'pct':'%.3f'%(t['gamesWon']/gp),'gb':'','seed':t['position'],'strk':f'{lastres}{k}' if lastres else '-',
        'form':form,'home':t['homeRecord'],'road':t['awayRecord'],'ppg':'%.1f'%(t['pointsFor']/gp),'opp':'%.1f'%(t['pointsAgainst']/gp),'diff':'%+.1f'%((t['pointsFor']-t['pointsAgainst'])/gp)})
    cur[c]=f"{t['gamesWon']}-{t['gamesLost']}"
for u in upcoming:
    for g in u['games']:
        for tm in g['teams']: tm['rec']=cur.get(tm['abbr'],'')
standings=[{'name':'Fase regular','zones':{'po':6,'pi':10,'rel':0},'rows':rows}]

# leaders
L=j(f'{API}/v3/competitions/{C}/statistics/players/leaders?seasonMode=Single&seasonCode={SEA}&statisticMode=PerGame&limit=10')
cats=[('pir','Valoración (PIR)'),('points','Puntos'),('rebounds','Rebotes'),('assists','Asistencias'),('steals','Robos'),('blocks','Tapones'),('threePointersPercentage','% Triples'),('offensiveRebounds','Rebotes ofensivos')]
POS={'Guard':'B','Forward':'A','Center':'P'}
leaders=[]
for k,t in cats:
    ls=[]
    for x in L.get(k,[])[:10]:
        d=x['details']; v=x.get('average') if x.get('average') is not None else x.get('value')
        vs=(f'{v:.1f}' if isinstance(v,(int,float)) else str(v))
        if 'Percentage' in k and isinstance(v,(int,float)): vs=f'{v:.1f}%' if v>1 else f'{v*100:.1f}%'
        ls.append({'pid':'el'+d['code'],'n':nice(d['name']),'abbr':d['team']['code'],'pos':POS.get(d.get('position'),''),'num':'','v':vs})
    leaders.append({'k':k,'t':t,'ls':ls})

# team stats
TS=j(f'{API}/v3/competitions/{C}/statistics/teams/traditional?seasonMode=Single&seasonCode={SEA}&statisticMode=PerGame')['teams']
def pf(x): return float(str(x).replace('%','') or 0)
teamstats={}
for t in TS:
    c=t['team']['code']
    fgm=t['twoPointersMade']+t['threePointersMade']; fga=t['twoPointersAttempted']+t['threePointersAttempted']
    teamstats[c]={'avgPoints':t['pointsScored'],'avgRebounds':t['totalRebounds'],'avgAssists':t['assists'],'avgSteals':t['steals'],'avgBlocks':t['blocks'],
      'avgTurnovers':t['turnovers'],'fieldGoalPct':round(100*fgm/fga,1) if fga else 0,'twoPointPct':pf(t['twoPointersPercentage']),'threePointPct':pf(t['threePointersPercentage']),
      'freeThrowPct':pf(t['freeThrowsPercentage']),'avgThreePointFieldGoalsMade':t['threePointersMade'],'avgOffensiveRebounds':t['offensiveRebounds'],'pir':t['pir']}

cal=[{'id':'el'+str(g['gameCode']),'utc':g['utcDate'],'r':g['round'],'a':g['road']['club']['code'],'h':g['local']['club']['code'],
      'as':g['road'].get('score') or 0,'hs':g['local'].get('score') or 0,'done':bool(g['played'])} for g in sorted(allg,key=lambda x:x['utcDate'])]
out={'key':'el','name':'EuroLiga','periodType':'round','teams':{c:{k:v for k,v in t.items() if k!='crest'} for c,t in teams.items()},
     'periods':periods,'upcoming':upcoming,'standings':standings,'leaders':leaders,'teamstats':teamstats,'cal':cal}
json.dump(out,open(B+'/league_el.json','w'),ensure_ascii=False,separators=(',',':'))
print('ok periods',len(periods),'teams',len(teams))
