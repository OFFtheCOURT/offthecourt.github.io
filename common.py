import os
import json, urllib.request, io, os, time, colorsys
from PIL import Image
S=os.environ.get('OFFCOURT_DIR') or os.path.dirname(os.path.abspath(__file__)); B=S+'/build'
UA={'User-Agent':'Mozilla/5.0 (OffcourtStats personal project)'}
def get(u, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40) as r: return r.read()
        except Exception as e:
            print('retry',u[:90],e); time.sleep(3*(i+1))
    raise Exception('fail '+u)
def j(u): return json.loads(get(u))

def save_logo(url, path, size=160):
    if os.path.exists(path): return Image.open(path)
    im=Image.open(io.BytesIO(get(url))).convert('RGBA')
    im.thumbnail((size,size),Image.LANCZOS)
    c=Image.new('RGBA',(size,size),(0,0,0,0)); c.paste(im,((size-im.width)//2,(size-im.height)//2),im)
    c.save(path,'WEBP',quality=85); return c

def dominant(im):
    """Most common saturated colour of a crest -> hex (fallback: darkest strong colour)."""
    im=im.convert('RGBA').resize((64,64))
    buckets={}
    for r,g,b,a in im.getdata():
        if a<200: continue
        h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
        if l>0.92 or l<0.06: continue
        if s<0.25 and 0.2<l<0.85: continue
        key=(r//24,g//24,b//24)
        buckets.setdefault(key,[0,0,0,0]); bb=buckets[key]; bb[0]+=1; bb[1]+=r; bb[2]+=g; bb[3]+=b
    if not buckets: return '333333','999999'
    ranked=sorted(buckets.values(),key=lambda x:-x[0])
    def hx(b): return '%02x%02x%02x'%(b[1]//b[0],b[2]//b[0],b[3]//b[0])
    main=hx(ranked[0])
    alt=hx(ranked[1]) if len(ranked)>1 else 'ffffff'
    return main,alt

def records(games):
    """games: list of dict(date, home, away, hs, as_, played) -> {(gameid,abbr): 'W-L' after game}"""
    rec={}; out={}
    for g in sorted(games,key=lambda x:x['date']):
        if not g['played']: continue
        for ab,win in ((g['home'],g['hs']>g['as']),(g['away'],g['as']>g['hs'])):
            w,l=rec.get(ab,(0,0)); w,l=(w+1,l) if win else (w,l+1); rec[ab]=(w,l); out[(g['id'],ab)]=f'{w}-{l}'
    return out

def pct(m,a): return str(round(100*m/a)) if a else '0'
