# Offcourt · vídeo promocional (≤30 s, vertical 1080x1920) con figuras animadas, voz en off, música y subtítulos
import os, re, json, wave, subprocess, shutil, math
import numpy as np
from tts_kokoro import synth
S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, 'contenido'); os.makedirs(OUT, exist_ok=True)
WORK = os.path.join(OUT, '_promo'); shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK + '/f')
SITE = os.environ.get('OFFCOURT_URL', 'offthecourt.github.io'); HANDLE = os.environ.get('OFFCOURT_HANDLE', '@offcourt')
FPS, SR, BPM = 24, 44100, 124; BEAT = 60 / BPM
src = open(os.path.join(S, 'index.html'), encoding='utf-8').read()
m = re.search(r'<div class="logo-slot" id="logoSlot">(<svg.*?</svg>)', src, flags=re.S); LOGO = m.group(1)

# ---------- guion ----------
lines = [
  ('hook',  "¿Te perdiste el partido de anoche?"),
  ('logo',  "Offcourt te lo cuenta todo."),
  ('leagues', f"{'⟦NBA⟧'}, EuroLiga y ACB, en un solo sitio."),
  ('live',  "Resultados y marcadores en directo."),
  ('stats', "Estadísticas, clasificaciones y líderes."),
  ('video', "Y cada mañana, el resumen de la noche en vídeo."),
  ('end',   "Offcourt. ¡Síguenos!"),
]
q = lambda x, u=BEAT: math.ceil(x / u - 1e-6) * u
tl = []; t = 0.0
for k, (key, text) in enumerate(lines):
    wf = f'{WORK}/l{k}.wav'; dur, words, _ = synth(text, wf, speed=1.18)
    lead = BEAT * 0.5
    sd = q(dur + lead + BEAT * 0.5, BEAT * 2) if key != 'end' else q(dur + lead + BEAT * 4, BEAT * 2)
    tl.append({'key': key, 'start': round(t, 3), 'dur': round(sd, 3), 'voice': round(t + lead, 3), 'wav': wf, 'text': re.sub(r'[⟦⟧]', '', text),
               'words': [{'w': w['w'], 's': round(w['s'] + t + lead, 3), 'e': round(w['e'] + t + lead, 3)} for w in words]})
    t += sd
TOTAL = round(t, 3)
print('duración', TOTAL)

# ---------- audio: voz + música + efectos ----------
N = int(TOTAL * SR); voice = np.zeros(N, np.float32)
for x in tl:
    with wave.open(x['wav']) as f: a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32767; vs = f.getframerate()
    a = np.interp(np.arange(0, len(a), vs / SR), np.arange(len(a)), a); s0 = int(x['voice'] * SR); voice[s0:s0 + len(a)] += a[:N - s0]
rng = np.random.default_rng(3); X = lambda l: np.arange(int(l * SR)) / SR
def lp(s, a):
    o = np.zeros_like(s); y = 0.0
    for i in range(len(s)): y += a * (s[i] - y); o[i] = y
    return o
def put(buf, sig, at, g=1.0):
    s0 = int(at * SR)
    if 0 <= s0 < N: n = min(len(sig), N - s0); buf[s0:s0 + n] += sig[:n] * g
kick = (lambda x: np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-x * 30)) / SR) * np.exp(-x * 8))(X(.3))
clap = (lambda n: (n - lp(n, .15)) * np.exp(-X(.2) * 24) * .6)(rng.normal(0, 1, len(X(.2))))
hat = (lambda n: (n - lp(n, .5)) * np.exp(-X(.05) * 60) * .3)(rng.normal(0, 1, len(X(.05))))
def saw(fq, l, cut, dec): x = X(l); s = 2 * ((x * fq) % 1) - 1 + 2 * ((x * fq * 1.007) % 1) - 1; return lp(s, cut) * np.exp(-x * dec) * .5
pop = (lambda x: np.sin(2 * np.pi * (900 - 500 * x / .12) * x) * np.exp(-x * 40))(X(.12))
def whoosh(l=.45):
    x = X(l); n = rng.normal(0, 1, len(x)); o = np.zeros_like(n); y = 0.0
    for i in range(len(n)): a = .02 + .3 * math.sin(math.pi * i / len(n)); y += a * (n[i] - y); o[i] = y
    return o * np.sin(np.pi * x / l)
PROG = [(55.0, (220, 277.2, 329.6)), (49.0, (196, 246.9, 293.7)), (43.65, (174.6, 220, 261.6)), (49.0, (196, 246.9, 311.1))]
music = np.zeros(N, np.float32); fx = np.zeros(N, np.float32); BAR = BEAT * 4
for b in range(int(TOTAL / BAR) + 1):
    fq, ch = PROG[b % 4]; t0 = b * BAR
    for s16 in range(16):
        at = t0 + s16 * BEAT / 4
        if at < tl[1]['start']:                       # el gancho: solo bajo y palmas suaves
            if s16 % 8 == 0: put(music, saw(fq, BEAT * .9, .04, 3), at, .5)
            continue
        if s16 % 4 == 0: put(music, kick, at, .9)
        if s16 in (4, 12): put(music, clap, at, .55)
        if s16 % 2 == 1: put(music, hat, at, .4)
        if s16 % 4 == 2: put(music, saw(fq, BEAT * .45, .05, 6), at, .5)
    if t0 >= tl[1]['start']: put(music, sum(saw(c * 2, BEAT * 1.6, .1, 3) for c in ch) / 3, t0, .25)
for x in tl[1:]: put(fx, whoosh(), x['start'] - .25, .6)
for x in tl: put(fx, pop, x['start'] + BEAT, .5); put(fx, pop, x['start'] + BEAT * 2, .4)
env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode='same'); duck = 1 - .5 * np.clip(env * 6, 0, 1)
tt = np.arange(N) / SR; fade = np.clip((TOTAL - tt) / .8, 0, 1)
mix = voice * 1.05 + (music * .33 * duck + fx * .3) * fade; mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix = mix / np.max(np.abs(mix)) * .97
with wave.open(f'{WORK}/audio.wav', 'wb') as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------- figuras (SVG propios) ----------
BALL = '<svg viewBox="0 0 100 100"><defs><radialGradient id="bg1" cx="35%" cy="30%"><stop offset="0" stop-color="#ffc07a"/><stop offset=".6" stop-color="#ff7a1a"/><stop offset="1" stop-color="#c24a00"/></radialGradient></defs><circle cx="50" cy="50" r="46" fill="url(#bg1)"/><g fill="none" stroke="#3a1600" stroke-width="3.2"><path d="M4 50h92M50 4v92"/><path d="M17 17q22 33 0 66M83 17q-22 33 0 66"/></g></svg>'
MOON = '<svg viewBox="0 0 100 100"><path d="M70 12A40 40 0 1 0 88 64 32 32 0 1 1 70 12z" fill="#ffd166"/><g fill="#fff"><circle cx="20" cy="22" r="3"/><circle cx="84" cy="30" r="2.4"/><circle cx="12" cy="70" r="2"/></g></svg>'
SUN = '<svg viewBox="0 0 100 100"><g stroke="#ffb100" stroke-width="7" stroke-linecap="round">' + ''.join(f'<path d="M50 50L{50 + 44 * math.cos(a):.1f} {50 + 44 * math.sin(a):.1f}"/>' for a in [i * math.pi / 4 for i in range(8)]) + '</g><circle cx="50" cy="50" r="24" fill="#ffd166"/></svg>'
TROPHY = '<svg viewBox="0 0 100 100"><path d="M28 10h44v20a22 22 0 0 1-44 0z" fill="#ffd166"/><path d="M28 16H14q0 20 18 22M72 16h14q0 20-18 22" fill="none" stroke="#ffd166" stroke-width="6"/><rect x="44" y="52" width="12" height="18" fill="#ffb100"/><rect x="30" y="70" width="40" height="12" rx="3" fill="#ffb100"/></svg>'
PHONE = '<svg viewBox="0 0 100 180"><rect x="4" y="4" width="92" height="172" rx="16" fill="#0b1220" stroke="#e8edf7" stroke-width="5"/><rect x="12" y="20" width="76" height="136" rx="6" fill="url(#pg)"/><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff5a1f"/><stop offset=".5" stop-color="#8f5bff"/><stop offset="1" stop-color="#2f6bff"/></linearGradient></defs><circle cx="50" cy="88" r="20" fill="#fff"/><path d="M45 77l17 11-17 11z" fill="#0b1220"/></svg>'
def figure(cls, svg, style=''): return f'<div class="fig {cls}" style="{style}">{svg}</div>'
chips = ''.join(f'<div class="chip" data-a="pop" data-d="{.15 + i * .22:.2f}" style="--c:{c}"><b>{n}</b><small>{s}</small></div>' for i, (n, s, c) in enumerate([('NBA', 'EE. UU.', '#2f6bff'), ('EuroLiga', 'Europa', '#ff7a1a'), ('ACB', 'España', '#e5484d')]))
bars = ''.join(f'<i style="--h:{h}%;--d:{.15 + i * .1:.2f}"></i>' for i, h in enumerate([45, 70, 55, 90, 65, 80]))
scenes = {
 'hook': f'''{figure('moon', MOON)}<div class="zz">z<span>z</span><span>z</span></div><div class="big" data-a="up" data-d=".1">¿Te perdiste<br>el partido<br><em>de anoche?</em></div>''',
 'logo': f'''<div class="logo" data-a="slam" data-d="0">{LOGO}</div><div class="word" data-a="up" data-d=".3">Off<span>court</span></div><div class="sub" data-a="up" data-d=".5">te lo cuenta todo</div>''',
 'leagues': f'''{figure('ballbounce', BALL)}<div class="chips">{chips}</div><div class="sub" data-a="up" data-d=".8">en un solo sitio</div>''',
 'live': f'''<div class="board" data-a="pop" data-d=".05"><div class="live"><i></i>EN DIRECTO</div><div class="sc"><span class="n" data-from="96" data-to="104">104</span><em>–</em><span class="n" data-from="99" data-to="101">101</span></div><div class="q">4º CUARTO · 1:12</div></div>{figure('ballspin', BALL)}<div class="sub" data-a="up" data-d=".4">resultados en directo</div>''',
 'stats': f'''<div class="row3"><div class="chart" data-a="pop" data-d=".05"><div class="bars">{bars}</div><small>ESTADÍSTICAS</small></div><div class="podium" data-a="pop" data-d=".3"><i class="p2"><b>2</b></i><i class="p1"><b>1</b></i><i class="p3"><b>3</b></i><small>CLASIFICACIÓN</small></div></div>{figure('trophy', TROPHY)}<div class="sub" data-a="up" data-d=".6">líderes y clasificaciones</div>''',
 'video': f'''{figure('sun', SUN)}{figure('phone', PHONE)}<div class="sub" data-a="up" data-d=".4">el resumen de la noche<br><b>cada mañana</b></div>''',
 'end': f'''<div class="logo" data-a="slam" data-d=".05">{LOGO}</div><div class="word" data-a="up" data-d=".3">Off<span>court</span></div><div class="url" data-a="pop" data-d=".6">{SITE}</div><div class="follow" data-a="up" data-d=".8">Síguenos {HANDLE}</div>''',
}
CSS = """
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1080px;height:1920px;overflow:hidden;background:#05070e;font-family:'Inter Tight',sans-serif;color:#fff}
#stage{position:absolute;inset:0;transform-origin:50% 45%}
.blob{position:absolute;width:1500px;height:1500px;border-radius:50%;filter:blur(130px);opacity:.75}
#b1{left:-650px;top:-600px;background:#ff6a1a}#b2{right:-700px;bottom:-600px;background:#5b3cff}
#stripes{position:absolute;inset:-400px;background:repeating-linear-gradient(112deg,rgba(255,255,255,.04) 0 3px,transparent 3px 40px)}
.dot{position:absolute;border-radius:50%}
.scene{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px;padding:0 70px 380px;opacity:0;text-align:center}
.big{font:900 150px/.9 'Big Shoulders Display';text-transform:uppercase}.big em{font-style:normal;background:linear-gradient(95deg,#ffd166,#ff8a1a 45%,#ff3d7f);-webkit-background-clip:text;color:transparent}
.sub{font:800 58px/1.1 'Inter Tight';letter-spacing:.02em;text-transform:uppercase;color:#e8edf7}.sub b{color:#ffd166}
.logo{width:340px;height:340px;filter:drop-shadow(0 30px 60px rgba(255,120,30,.5))}.logo svg{width:100%;height:100%}
.word{font:900 190px/.9 'Big Shoulders Display';text-transform:uppercase}.word span{color:#ff8a1a}
.fig{position:relative}.fig svg{width:100%;height:100%;display:block}
.moon{width:300px;height:300px}.zz{position:absolute;top:470px;right:250px;font:900 90px 'Big Shoulders Display';color:#ffd166}.zz span{font-size:.7em;margin-left:10px}
.ballbounce{width:220px;height:220px}.ballspin{width:170px;height:170px}
.chips{display:flex;flex-direction:column;gap:26px;width:100%}
.chip{display:flex;align-items:baseline;justify-content:space-between;padding:30px 48px;border-radius:40px;background:linear-gradient(100deg,var(--c),rgba(255,255,255,.06));border:2px solid rgba(255,255,255,.3);box-shadow:0 20px 50px rgba(0,0,0,.35)}
.chip b{font:900 120px/.9 'Big Shoulders Display';text-transform:uppercase}.chip small{font:800 34px 'Inter Tight';letter-spacing:.2em;text-transform:uppercase;opacity:.85}
.board{width:100%;padding:40px;border-radius:50px;background:linear-gradient(135deg,rgba(255,255,255,.16),rgba(255,255,255,.04));border:2px solid rgba(255,255,255,.3)}
.live{display:inline-flex;align-items:center;gap:16px;font:800 38px 'Inter Tight';letter-spacing:.2em;color:#ff5d6c}.live i{width:26px;height:26px;border-radius:50%;background:#ff3d5a;box-shadow:0 0 24px #ff3d5a}
.sc{font:900 260px/.9 'Big Shoulders Display';display:flex;justify-content:center;gap:20px;margin:16px 0}.sc em{font-style:normal;opacity:.4}.q{font:800 36px 'Inter Tight';letter-spacing:.2em;color:#ffd166}
.row3{display:flex;gap:30px;width:100%;align-items:flex-end}
.chart,.podium{flex:1;padding:34px 30px 24px;border-radius:44px;background:linear-gradient(135deg,rgba(255,255,255,.16),rgba(255,255,255,.04));border:2px solid rgba(255,255,255,.3);display:flex;flex-direction:column;gap:20px}
.chart small,.podium small{font:800 26px 'Inter Tight';letter-spacing:.2em;width:100%}
.bars{height:330px;display:flex;align-items:flex-end;gap:16px}.bars i{flex:1;border-radius:14px 14px 4px 4px;background:linear-gradient(180deg,#ffd166,#ff8a1a);height:var(--hh,0%)}
.podium{flex-direction:row;flex-wrap:wrap;align-items:flex-end;justify-content:center;gap:12px}.podium i{width:30%;border-radius:14px 14px 4px 4px;display:flex;justify-content:center;padding-top:14px;font-style:normal}
.podium b{font:900 70px 'Big Shoulders Display';color:#1a0b02}.p1{height:300px;background:linear-gradient(180deg,#ffe27a,#ffb100)}.p2{height:220px;background:linear-gradient(180deg,#f1f4fa,#aab6c8)}.p3{height:170px;background:linear-gradient(180deg,#ffb37a,#c46a2a)}
.trophy{width:200px;height:200px}
.sun{position:absolute;top:260px;right:120px;width:230px;height:230px}.phone{width:300px;height:540px}
.url{font:800 54px 'Inter Tight';color:#1a0b02;background:linear-gradient(95deg,#ffd166,#ff8a1a 50%,#ff3d7f);padding:20px 50px;border-radius:999px;box-shadow:0 20px 50px rgba(255,120,60,.45)}
.follow{font:800 46px 'Inter Tight';letter-spacing:.14em;text-transform:uppercase}
#cap{position:absolute;left:40px;right:40px;bottom:140px;height:230px;display:flex;align-items:center;justify-content:center}
#cap div{font:900 92px/1.2 'Big Shoulders Display';text-transform:uppercase;text-align:center;text-shadow:0 6px 24px rgba(0,0,0,.6)}
#cap .w{display:inline-block;margin:0 .06em;padding:0 .14em;border-radius:14px}#cap .w.on{color:#1a0b02;background:linear-gradient(95deg,#ffd166,#ff8a1a)}
#wipe{position:absolute;top:-200px;bottom:-200px;width:900px;background:linear-gradient(100deg,#ffd166,#ff8a1a 35%,#ff3d7f 70%,#8f5bff);transform:skewX(-14deg);left:-1500px;z-index:30}
#seg{position:absolute;left:64px;right:64px;top:80px;display:flex;gap:10px}#seg i{flex:1;height:7px;border-radius:9px;background:rgba(255,255,255,.22);overflow:hidden}#seg b{display:block;height:100%;width:0;background:#fff}
"""
TL = [{'key': x['key'], 'start': x['start'], 'dur': x['dur']} for x in tl]
WORDS = [w for x in tl for w in x['words']]
chunks = []; cur = []
for w in WORDS:
    cur.append(w)
    if len(cur) >= 3 or re.search(r'[.,:;!?]$', w['w']): chunks.append(cur); cur = []
if cur: chunks.append(cur)
CH = [{'s': c[0]['s'], 'e': c[-1]['e'], 'w': [{'t': x['w'], 's': x['s'], 'e': x['e']} for x in c]} for c in chunks]
JS = """
const TL=__TL__,CH=__CH__,TOTAL=__T__,BEAT=__B__;
const cl=x=>Math.min(1,Math.max(0,x)),ease=x=>1-Math.pow(1-cl(x),3),back=x=>{x=cl(x);const c=2.2;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
TL.forEach(()=>seg.insertAdjacentHTML('beforeend','<i><b></b></i>'));
const DOTS=[];for(let i=0;i<26;i++){const d=document.createElement('i');d.className='dot';const s=10+Math.random()*26;d.style.width=d.style.height=s+'px';d.style.background=['#ffd166','#ff8a1a','#ff3d7f','#8f5bff','#2f6bff'][i%5];stage.insertBefore(d,stage.children[3]);DOTS.push({d,x:Math.random()*1080,y:Math.random()*1920,v:40+Math.random()*120,o:.25+Math.random()*.5})}
function render(t){
  let shake=0;
  document.querySelectorAll('#seg b').forEach((b,i)=>b.style.width=cl((t-TL[i].start)/TL[i].dur)*100+'%');
  b1.style.transform=`translate(${Math.sin(t*.9)*120}px,${Math.cos(t*.7)*90}px) scale(${1+.08*Math.sin(t*1.4)})`;b2.style.transform=`translate(${Math.cos(t*.8)*120}px,${Math.sin(t*.6)*90}px)`;
  stripes.style.transform=`translateX(${-(t*90)%40}px)`;
  DOTS.forEach((q,i)=>{const y=((q.y-t*q.v)%1920+1920)%1920;q.d.style.transform=`translate(${q.x+Math.sin(t*1.5+i)*40}px,${y}px)`;q.d.style.opacity=q.o});
  TL.forEach(s=>{const el=document.getElementById('sc-'+s.key),lt=t-s.start,on=lt>=0&&lt<s.dur;el.style.opacity=on?1:0;if(!on)return;
    el.querySelectorAll('[data-a]').forEach(n=>{const d=parseFloat(n.dataset.d||0),p=(lt-d)/.32,a=n.dataset.a;let o=ease(p),tr='';
      if(a==='up')tr=`translateY(${(1-ease(p))*120}px)`;
      if(a==='pop')tr=`scale(${p<=0?0:.3+.7*back(p)})`;
      if(a==='slam'){tr=`scale(${p<=0?3.5:1+2.5*(1-back(p*1.2))}) rotate(${(1-ease(p))*-25}deg)`;o=p>0?1:0;if(p>.3&&p<1)shake=1-(p-.3)/.7}
      n.style.opacity=o;n.style.transform=tr});
    const beatp=(lt%BEAT)/BEAT;
    el.querySelectorAll('.moon').forEach(n=>n.style.transform=`translateY(${Math.sin(lt*2)*20}px) rotate(${Math.sin(lt*1.5)*8}deg) scale(${ease(lt/.4)})`);
    el.querySelectorAll('.zz').forEach(n=>{n.style.opacity=cl(lt-.3);n.style.transform=`translateY(${-lt*30}px)`});
    el.querySelectorAll('.ballbounce').forEach(n=>{const y=-Math.abs(Math.sin(lt*Math.PI/BEAT))*180;n.style.transform=`translateY(${y}px) rotate(${lt*240}deg)`});
    el.querySelectorAll('.ballspin').forEach(n=>n.style.transform=`rotate(${lt*360}deg) scale(${back(lt/.5)})`);
    el.querySelectorAll('.trophy').forEach(n=>n.style.transform=`scale(${back((lt-.4)/.4)}) rotate(${Math.sin(lt*3)*6}deg)`);
    el.querySelectorAll('.sun').forEach(n=>n.style.transform=`rotate(${lt*40}deg) scale(${back(lt/.5)})`);
    el.querySelectorAll('.phone').forEach(n=>n.style.transform=`translateY(${(1-ease(lt/.5))*600}px) rotate(${-8+Math.sin(lt*2)*3}deg)`);
    el.querySelectorAll('.bars i').forEach(n=>{const d=parseFloat(n.style.getPropertyValue('--d'));n.style.setProperty('--hh',(parseFloat(n.style.getPropertyValue('--h'))*ease((lt-d)/.5))+'%')});
    el.querySelectorAll('.n').forEach(n=>{const a=+n.dataset.from,b=+n.dataset.to;const k=Math.min(b-a,Math.floor(cl((lt-.3)/(s.dur-.8))*(b-a+1)));n.textContent=a+k});
    el.querySelectorAll('.live i').forEach(n=>n.style.opacity=.4+.6*Math.abs(Math.sin(lt*5)));
  });
  let wx=-1500;TL.forEach((s,i)=>{if(!i)return;const p=(t-(s.start-.22))/.44;if(p>0&&p<1)wx=-1100+p*3000});wipe.style.left=wx+'px';
  const c=CH.find(c=>t>=c.s-.04&&t<=c.e+.3);
  cap.innerHTML=c?'<div>'+c.w.filter(w=>t>=w.s-.04).map(w=>{const p=cl((t-w.s+.04)/.12);return `<span class="w ${t<w.e+.06?'on':''}" style="transform:scale(${.5+.5*back(p)})">${w.t}</span>`}).join(' ')+'</div>':'';
  const bt=((t%BEAT)+BEAT)%BEAT,pulse=t>TL[1].start?Math.exp(-bt*14):0;
  stage.style.transform=`translate(${shake?Math.sin(t*95)*16*shake:0}px,${shake?Math.cos(t*81)*16*shake:0}px) scale(${1+.015*pulse})`;
}
window.render=render;
""".replace('__TL__', json.dumps(TL)).replace('__CH__', json.dumps(CH, ensure_ascii=False)).replace('__T__', str(TOTAL)).replace('__B__', str(BEAT))
page = f"""<!doctype html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800;900&family=Inter+Tight:wght@700;800;900&display=block" rel="stylesheet">
<style>{CSS}</style></head><body><div id="stage"><div class="blob" id="b1"></div><div class="blob" id="b2"></div><div id="stripes"></div>
{''.join(f'<div class="scene" id="sc-{k}">{v}</div>' for k, v in scenes.items())}<div id="cap"></div><div id="seg"></div></div><div id="wipe"></div><script>{JS}</script></body></html>"""
open(f'{WORK}/promo.html', 'w', encoding='utf-8').write(page)
CAP = r"""const {chromium}=require('playwright');(async()=>{const [dir,fps,total]=[process.argv[1],+process.argv[2],+process.argv[3]];
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});await p.goto('file://'+dir+'/promo.html');await p.waitForTimeout(3000);await p.evaluate(()=>document.fonts.ready);
const n=Math.ceil(total*fps);for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:dir+'/f/'+String(i).padStart(5,'0')+'.jpg',type:'jpeg',quality:86});}await b.close()})();"""
subprocess.run(['node', '-e', CAP, WORK, str(FPS), str(TOTAL)], check=True)
dst = os.path.join(OUT, 'offcourt_promo.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{WORK}/f/%05d.jpg', '-i', f'{WORK}/audio.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst], check=True)
shutil.rmtree(WORK, ignore_errors=True); print('ok', dst, TOTAL)
