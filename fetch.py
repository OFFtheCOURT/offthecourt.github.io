import os
import json, urllib.request, io, os, datetime, concurrent.futures as cf
from PIL import Image
S=os.environ.get('OFFCOURT_DIR') or os.path.dirname(os.path.abspath(__file__))
B=S+'/build'
API='https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
def get(u):
    with urllib.request.urlopen(u,timeout=30) as r: return r.read()
def j(u): return json.loads(get(u))
from zoneinfo import ZoneInfo
ET=datetime.datetime.now(ZoneInfo('America/New_York')).date()
days=[(ET-datetime.timedelta(days=1+i)) for i in range(11)]
out={'generated':datetime.date.today().isoformat(),'days':[]}
teams={}
players={}
def num(x):
    try: return float(x)
    except: return 0
def summ(eid):
    return eid, j(f'{API}/summary?event={eid}')
for day in days:
    ds=day.strftime('%Y%m%d')
    sb=j(f'{API}/scoreboard?dates={ds}')
    ids=[e['id'] for e in sb['events']]
    with cf.ThreadPoolExecutor(8) as ex: sums=dict(ex.map(summ,ids))
    games=[]
    for e in sb['events']:
        c=e['competitions'][0]; s=sums[e['id']]
        g={'id':e['id'],'status':e['status']['type']['shortDetail'],'completed':e['status']['type']['completed'],
           'venue':c.get('venue',{}).get('fullName',''),'city':c.get('venue',{}).get('address',{}).get('city',''),
           'att':c.get('attendance',0),'teams':[], 'videos':[], 'note':''}
        hl=[h.get('headline') for h in c.get('headlines',[]) if h.get('shortLinkText') or h.get('description')]
        if c.get('headlines'): g['recap']=c['headlines'][0].get('shortLinkText') or c['headlines'][0].get('description','')
        if c.get('notes'): g['note']=c['notes'][0].get('headline','')
        box={t['team']['id']:t for t in s['boxscore'].get('teams',[])}
        pl={p['team']['id']:p for p in s['boxscore'].get('players',[])}
        for comp in sorted(c['competitors'],key=lambda x: x['homeAway']!='away'):
            t=comp['team']; tid=t['id']
            teams[t['abbreviation']]={'id':tid,'abbr':t['abbreviation'],'name':t['displayName'],'short':t['shortDisplayName'],'color':t.get('color','333333'),'alt':t.get('alternateColor','ffffff'),'logo':t.get('logo','')}
            rec=next((r['summary'] for r in comp.get('records',[]) if r.get('type')=='total' or r.get('name')=='overall'), '')
            st={x['name']:x['displayValue'] for x in box.get(tid,{}).get('statistics',[])}
            top=[]
            if tid in pl:
                grp=pl[tid]['statistics'][0]; names=grp['labels']
                for a in grp['athletes']:
                    if not a.get('stats'): continue
                    m=dict(zip(names,a['stats']))
                    fg=m['FG'].split('-'); tp=m['3PT'].split('-'); ft=m['FT'].split('-')
                    pts=num(m['PTS']); reb=num(m['REB']); ast=num(m['AST']); stl=num(m['STL']); blk=num(m['BLK']); to=num(m['TO'])
                    gs=pts+0.4*num(fg[0])-0.7*num(fg[1])-0.4*(num(ft[1])-num(ft[0]))+0.7*num(m['OREB'])+0.3*num(m['DREB'])+stl+0.7*ast+0.7*blk-0.4*num(m['PF'])-to
                    ath=a['athlete']
                    players[ath['id']]=ath.get('headshot',{}).get('href','')
                    top.append({'pid':ath['id'],'n':ath['displayName'],'pos':ath.get('position',{}).get('abbreviation',''),'num':ath.get('jersey',''),
                        'st':a.get('starter',False),'min':m['MIN'],'pts':int(pts),'reb':int(reb),'ast':int(ast),'stl':int(stl),'blk':int(blk),'to':int(to),
                        'fg':m['FG'],'tp':m['3PT'],'ft':m['FT'],'pm':m['+/-'],'gs':round(gs,1)})
                top.sort(key=lambda x:-x['gs']); top=top[:5]
            g['teams'].append({'abbr':t['abbreviation'],'ha':comp['homeAway'],'score':int(comp.get('score',0) or 0),'win':comp.get('winner',False),'rec':rec,
               'ls':[int(num(l.get('value',l.get('displayValue',0)))) for l in comp.get('linescores',[])],
               'st':{k:st.get(k,'') for k in ['fieldGoalsMade-fieldGoalsAttempted','fieldGoalPct','threePointFieldGoalsMade-threePointFieldGoalsAttempted','threePointFieldGoalPct','freeThrowsMade-freeThrowsAttempted','freeThrowPct','totalRebounds','offensiveRebounds','assists','steals','blocks','totalTurnovers','pointsInPaint','fastBreakPoints','turnoverPoints','largestLead']},
               'top':top})
        for v in s.get('videos',[])[:6]:
            g['videos'].append({'h':v['headline'],'d':v.get('duration',0),'u':v['links'].get('web',{}).get('href','')})
        games.append(g)
    out['days'].append({'date':day.isoformat(),'games':games})
    print(ds,len(games))
json.dump(out,open(B+'/data.json','w'),separators=(',',':'),ensure_ascii=False)
def img(args):
    url,path,w,h=args
    if os.path.exists(path): return
    try:
        p=url.replace('https://a.espncdn.com','')
        raw=get(f'https://a.espncdn.com/combiner/i?img={p}&w={w}&h={h}')
        im=Image.open(io.BytesIO(raw)).convert('RGBA'); im.save(path,'WEBP',quality=80)
    except Exception as ex: print('fail',url,ex)
jobs=[(f'/i/teamlogos/nba/500/{t["abbr"].lower()}.png',f'{B}/img/t/{t["abbr"]}.webp',160,160) for t in teams.values()]
with cf.ThreadPoolExecutor(12) as ex: list(ex.map(img,jobs))
json.dump(teams,open(B+'/teams.json','w'))
print('players',len(players),'teams',len(teams))
