import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
import re, concurrent.futures as cf, urllib.parse
sys.path.insert(0,S+'/acb'); sys.path.insert(0,S); from rsc import rsc  # rsc.py dentro de acb/ o suelto
os.makedirs(B+'/img/acb',exist_ok=True)
dec=json.JSONDecoder()
def page(u): return rsc(get(u).decode('utf-8','ignore'))

# ---------- standings (with every team's matches) ----------
t=page('https://acb.com/es/liga/clasificacion')
i=t.find('"standings":['); arr=dec.raw_decode(t[i+12:])[0]
j0=t.rfind('"teams":[',0,i); TL=dec.raw_decode(t[j0+8:])[0]
def deref(x):
    if isinstance(x,dict): return x
    parts=x.split(':'); parts=parts[parts.index('data')+1:]
    cur={'teams':TL,'standings':arr}
    for q in parts: cur=cur[int(q)] if isinstance(cur,list) else cur[q]
    return deref(cur)
for e in arr: e['team']=deref(e['team'])
teams={}
def addteam(tm):
    ab=tm['abbreviatedName']
    if ab not in teams:
        teams[ab]={'abbr':ab,'name':tm['fullName'],'short':tm['shortName'],'logo':tm['logo'],'hint':tm.get('displayColor') or tm.get('primaryColorHex')}
    return ab
for e in arr: addteam(e['team'])
def resolve(x): return addteam(deref(x))
matches={}
for e in arr:
    for r in e['rounds']:
        md=r.get('matchData')
        if not md: continue
        matches[md['id']]={'id':md['id'],'round':r['roundData']['roundNumber'],'home':resolve(md['homeTeam']),'away':resolve(md['awayTeam']),
            'hs':md['homeScore'],'as':md['awayScore'],'date':md['startDateTime'],'played':md['matchStatus']=='FINALIZED'}
played=[m for m in matches.values() if m['played']]
print('matches',len(matches),'played',len(played))

for ab,tm in teams.items():
    im=save_logo(tm['logo'],f'{B}/img/acb/{ab}.webp')
    c,a=dominant(im)
    h=(tm['hint'] or '').lstrip('#').lower()
    tm['color']=h if h and h not in ('999999','ffffff','000000') else c
    tm['alt']=a
recs=records(list(matches.values()))

# ---------- box scores ----------
KEYS=['fieldGoals','twoPointers','threePointers','freeThrows','defensiveRebounds','offensiveRebounds','rebounds','assists','steals','turnovers','personalFouls','pointsOffTurnover','paintPoints','secondChancePoints','fastBreakPoints','benchPoints']
def box(mid):
    t=page(f'https://live.acb.com/partidos/partido-{mid}/resumen')
    comp={}
    for k in KEYS:
        m=re.search('"'+k+r'":\{"home":\{"title"',t)
        if m: comp[k]=dec.raw_decode(t[m.end()-len('{"home":{"title"'):])[0]
    sides=[]
    for m in re.finditer(r'\{"team":\{"id":\d+',t):
        try: o=dec.raw_decode(t[m.start():])[0]
        except Exception: continue
        if 'players' in o: sides.append(o)
    q=[]; m=re.search(r'"quarterScores":',t)
    if m: q=dec.raw_decode(t[m.end():])[0]
    return mid,{'comp':comp,'sides':sides,'q':q}
with cf.ThreadPoolExecutor(6) as ex: boxes=dict(ex.map(box,[m['id'] for m in played]))

def num(x):
    try: return float(str(x).replace(',','.').replace('%',''))
    except: return 0.0
def mins(s):
    try: a,b=s.split(':'); return int(a)+int(b)/60
    except: return 0
def side_stats(c,hk):
    g=lambda k:c.get(k,{}).get(hk,{})
    def ma(k):
        sub=g(k).get('subtitle') or '0/0'; a,b=(sub.split('/')+['0'])[:2]; return int(num(a)),int(num(b))
    fg=ma('fieldGoals'); tp=ma('threePointers'); ft=ma('freeThrows')
    t=lambda k:str(int(num(g(k).get('title','0'))))
    return {'fieldGoalsMade-fieldGoalsAttempted':f'{fg[0]}-{fg[1]}','fieldGoalPct':pct(*fg),'threePointFieldGoalsMade-threePointFieldGoalsAttempted':f'{tp[0]}-{tp[1]}',
      'threePointFieldGoalPct':pct(*tp),'freeThrowsMade-freeThrowsAttempted':f'{ft[0]}-{ft[1]}','freeThrowPct':pct(*ft),
      'totalRebounds':t('rebounds'),'offensiveRebounds':t('offensiveRebounds'),'assists':t('assists'),'steals':t('steals'),'totalTurnovers':t('turnovers'),
      'pointsInPaint':t('paintPoints'),'fastBreakPoints':t('fastBreakPoints'),'turnoverPoints':t('pointsOffTurnover'),'benchPoints':t('benchPoints'),'secondChancePoints':t('secondChancePoints')},(fg,tp,ft)

season_players={}   # pid -> aggregate
season_teams={}
def mkside(m,bx,hk):
    ab=m['home'] if hk=='home' else m['away']
    st,(fg,tp,ft)=side_stats(bx['comp'],hk)
    side=next((s for s in bx['sides'] if s['team']['abbreviatedName']==ab),None)
    top=[]
    for p in (side or {}).get('players',[]):
        x=p.get('playerStats') or {}
        mn=mins(x.get('minutes','0:00'))
        if mn<=0: continue
        pl=p.get('player') or {}
        pid='acb'+str(p['id']); name=pl.get('nickname') or p.get('firstInitialAndLastName')
        val=int(num(x.get('valoration'))); pm=int(num(x.get('plusMinus')))
        rec={'pid':pid,'n':name,'pos':'','num':p.get('shirtNumber') or '','st':False,'min':str(round(mn)),'pts':int(num(x.get('points'))),'reb':int(num(x.get('rebounds'))),
             'ast':int(num(x.get('assists'))),'stl':0,'blk':0,'to':0,'fg':'','tp':'','ft':'','pm':('+' if pm>0 else '')+str(pm),'gs':val,'val':val,'pf':int(num(x.get('personalFouls')))}
        top.append(rec)
        a=season_players.setdefault(pid,{'pid':pid,'n':name,'abbr':ab,'num':rec['num'],'g':0,'min':0,'pts':0,'reb':0,'ast':0,'val':0,'pm':0})
        a['g']+=1; a['min']+=mn; a['pts']+=rec['pts']; a['reb']+=rec['reb']; a['ast']+=rec['ast']; a['val']+=val; a['pm']+=pm; a['abbr']=ab; a['num']=rec['num'] or a['num']
    top.sort(key=lambda z:(-z['gs'],-z['pts'])); top=top[:5]
    T=season_teams.setdefault(ab,{'g':0,'pts':0,'reb':0,'ast':0,'stl':0,'to':0,'oreb':0,'fgm':0,'fga':0,'tpm':0,'tpa':0,'ftm':0,'fta':0,'paint':0,'fb':0,'bench':0})
    score=m['hs'] if hk=='home' else m['as']
    T['g']+=1; T['pts']+=score
    for k,sk in [('reb','totalRebounds'),('ast','assists'),('stl','steals'),('to','totalTurnovers'),('oreb','offensiveRebounds'),('paint','pointsInPaint'),('fb','fastBreakPoints'),('bench','benchPoints')]: T[k]+=int(st[sk])
    T['fgm']+=fg[0];T['fga']+=fg[1];T['tpm']+=tp[0];T['tpa']+=tp[1];T['ftm']+=ft[0];T['fta']+=ft[1]
    ls=[q[hk] for q in bx['q']]
    return {'abbr':ab,'ha':hk,'score':score,'win':(m['hs']>m['as'])==(hk=='home'),'rec':recs.get((m['id'],ab),''),'ls':ls,'st':st,'top':top}

periods=[]
for r in sorted({m['round'] for m in played},reverse=True):
    gs=sorted([m for m in played if m['round']==r],key=lambda x:x['date'])
    games=[]
    for m in gs:
        bx=boxes[m['id']]
        A=mkside(m,bx,'away'); H=mkside(m,bx,'home')
        games.append({'id':'acb'+str(m['id']),'status':'Final','venue':'','city':'','att':0,'utc':m['date'],'teams':[A,H],'videos':[],
          'yt':'https://www.youtube.com/results?search_query='+urllib.parse.quote(f"resumen {teams[H['abbr']]['short']} {teams[A['abbr']]['short']} Liga Endesa jornada {r}")})
    periods.append({'key':f'r{r}','round':r,'label':f'Jornada {r}','from':gs[0]['date'][:10],'to':gs[-1]['date'][:10],'games':games})

# ---------- upcoming ----------
t=page('https://acb.com/es/liga/partidos')
i=t.find('"availableFilters"'); st0=t.rfind('{',0,i)
D=dec.raw_decode(t[st0:])[0]
tl=D['teams']
def ref(x):
    if isinstance(x,dict): return x['abbreviatedName']
    return tl[int(x.split(':')[-1])]['abbreviatedName']
cur={e['team']['abbreviatedName']:f"{e['wins']}-{e['losses']}" for e in arr}
ups=[m for m in D['matches'] if m['matchStatus']!='FINALIZED']
upcoming=[]
if ups:
    upcoming.append({'label':'Próxima jornada','date':min(m['startDateTime'] for m in ups)[:10],'games':[{'id':'acb'+str(m['id']),'utc':m['startDateTime'],
      'teams':[{'abbr':ref(m['awayTeam']),'rec':cur.get(ref(m['awayTeam']),'')},{'abbr':ref(m['homeTeam']),'rec':cur.get(ref(m['homeTeam']),'')}],'venue':'',
      'tv':[c['name'] for c in (m.get('broadcastChannels') or {}).get('primary',[])][:2],'odds':'','state':'pre' if m['matchStatus']=='NOT_STARTED' else 'in',
      'detail':(f"{m.get('currentQuarter')}º cuarto" if m['matchStatus']!='NOT_STARTED' else ''),'live':f"https://live.acb.com/es/partidos/partido-{m['id']}/resumen"} for m in sorted(ups,key=lambda x:x['startDateTime'])]})
    for g,m in zip(upcoming[0]['games'],sorted(ups,key=lambda x:x['startDateTime'])):
        g['teams'][0]['score']=m.get('awayScore') or 0; g['teams'][1]['score']=m.get('homeScore') or 0
# label upcoming round number
nr=max(p['round'] for p in periods)+1
if upcoming: upcoming[0]['label']=f'Jornada {nr}'

# ---------- standings rows ----------
rows=[]
for e in arr:
    ab=e['team']['abbreviatedName']; gp=e['matchesPlayed'] or 1
    res=[]
    for r in sorted(e['rounds'],key=lambda r:r['roundData']['roundNumber']):
        md=r.get('matchData')
        if not md or md['matchStatus']!='FINALIZED': continue
        home=resolve(md['homeTeam'])==ab
        res.append('W' if (md['homeScore']>md['awayScore'])==home else 'L')
    k=0
    for x in reversed(res):
        if x==res[-1]: k+=1
        else: break
    rows.append({'abbr':ab,'w':e['wins'],'l':e['losses'],'pct':'%.3f'%(e['wins']/gp),'gb':'','seed':e['position'],'strk':f'{res[-1]}{k}' if res else '-','form':res[-5:],
      'home':f"{e['localBalanceWins']}-{e['localBalanceLosses']}",'road':f"{e['awayBalanceWins']}-{e['awayBalanceLosses']}",
      'ppg':'%.1f'%(e['pointsFor']/gp),'opp':'%.1f'%(e['pointsAgainst']/gp),'diff':'%+.1f'%((e['pointsFor']-e['pointsAgainst'])/gp)})
rows.sort(key=lambda r:r['seed'])
standings=[{'name':'Liga Endesa','zones':{'po':8,'pi':0,'rel':2},'rows':rows}]

# ---------- leaders (season averages, min 50% of games) ----------
maxg=max(p['g'] for p in season_players.values())
elig=[p for p in season_players.values() if p['g']>=max(2,maxg*0.5)]
cats=[('val','Valoración','%.1f'),('pts','Puntos','%.1f'),('reb','Rebotes','%.1f'),('ast','Asistencias','%.1f'),('min','Minutos','%.1f'),('pm','+/- por partido','%+.1f')]
leaders=[]
for k,tname,fmt in cats:
    ls=sorted(elig,key=lambda p:-p[k]/p['g'])[:10]
    leaders.append({'k':k,'t':tname,'ls':[{'pid':p['pid'],'n':p['n'],'abbr':p['abbr'],'pos':'','num':p['num'],'v':fmt%(p[k]/p['g'])} for p in ls]})

teamstats={}
for ab,T in season_teams.items():
    g=T['g'] or 1
    teamstats[ab]={'avgPoints':round(T['pts']/g,1),'avgRebounds':round(T['reb']/g,1),'avgAssists':round(T['ast']/g,1),'avgSteals':round(T['stl']/g,1),
      'avgTurnovers':round(T['to']/g,1),'avgOffensiveRebounds':round(T['oreb']/g,1),'fieldGoalPct':round(100*T['fgm']/max(T['fga'],1),1),
      'threePointPct':round(100*T['tpm']/max(T['tpa'],1),1),'freeThrowPct':round(100*T['ftm']/max(T['fta'],1),1),'avgThreePointFieldGoalsMade':round(T['tpm']/g,1),
      'paintPoints':round(T['paint']/g,1),'fastBreak':round(T['fb']/g,1),'benchPoints':round(T['bench']/g,1)}

cal=[]
try:
    t=page('https://acb.com/es/liga/calendario')
    i=t.find('"rounds":[{"id"'); RR=dec.raw_decode(t[i+9:])[0]
    j0=t.rfind('"teams":[',0,i); CTL=dec.raw_decode(t[j0+8:])[0]
    cref=lambda x:(x if isinstance(x,dict) else CTL[int(x.split(':')[-1])])['abbreviatedName']
    for r in RR:
        for m in r['matches']:
            cal.append({'id':'acb'+str(m['id']),'utc':m['startDateTime'],'r':r['roundNumber'],'a':cref(m['awayTeam']),'h':cref(m['homeTeam']),
                        'as':m.get('awayTeamScore') or 0,'hs':m.get('homeTeamScore') or 0,'done':m['matchStatus']=='FINALIZED'})
except Exception as x: print('calendario ACB',x)
out={'key':'acb','name':'ACB','periodType':'round','teams':{a:{k:v for k,v in t.items() if k not in('logo','hint')} for a,t in teams.items()},
     'periods':periods,'upcoming':upcoming,'standings':standings,'leaders':leaders,'teamstats':teamstats,'cal':cal}
json.dump(out,open(B+'/league_acb.json','w'),ensure_ascii=False,separators=(',',':'))
print('ok periods',len(periods),'teams',len(teams),'upcoming',sum(len(u['games']) for u in upcoming))
