<script>
const LG = /*LEAGUES*/;
const UPDATED = /*UPDATED*/;
const IMG = /*IMG*/;
const CR = /*CREDITS*/;
let CUR='nba', L=LG.nba, TEAMS=L.teams;

const TXT={
  nba:{tick:'Anoche',eyebrowNight:null,h1:'Partidos de la <span class="hl">noche</span>',hero:'Partido de la noche',mvp:'MVP de la noche',perH2:'Partidos por <span class="hl">fechas</span>',
       perSub:'Elige un día para ver sus partidos, estadísticas y jugadores destacados.',unit:'días',upSub:'Horarios en hora de España. Elige la noche.',
       stSub:'Del 1 al 6 entran directos a playoffs; del 7 al 10 juegan el play-in.',src:'ESPN',val:'valoración (game score)',m1:'Anoche',m3:'Por fechas'},
  el:{tick:null,h1:'Última <span class="hl">jornada</span>',hero:'Partido de la jornada',mvp:'MVP de la jornada',perH2:'Partidos por <span class="hl">jornadas</span>',
       perSub:'Elige una jornada para ver sus partidos, estadísticas y jugadores destacados.',unit:'jornadas',upSub:'Horarios en hora de España. Elige la jornada.',
       stSub:'Del 1 al 6 entran directos a playoffs; del 7 al 10 juegan el play-in.',src:'EuroLeague',val:'valoración PIR',m1:'Última jornada',m3:'Por jornadas'},
  acb:{tick:null,h1:'Última <span class="hl">jornada</span>',hero:'Partido de la jornada',mvp:'MVP de la jornada',perH2:'Partidos por <span class="hl">jornadas</span>',
       perSub:'Elige una jornada para ver sus partidos, estadísticas y jugadores destacados.',unit:'jornadas',upSub:'Horarios en hora de España. Elige la jornada.',
       stSub:'Del 1 al 8 juegan los playoffs por el título; los 2 últimos descienden.',src:'ACB',val:'valoración',m1:'Última jornada',m3:'Por jornadas'}
};
const $=id=>document.getElementById(id);
const fmtLong = d => new Date(d+'T12:00:00').toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long'});
const cap = s => s.charAt(0).toUpperCase()+s.slice(1);
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const madrid = (u,o)=>new Date(u).toLocaleString('es-ES',{timeZone:'Europe/Madrid',...o});
function range(a,b){const A=new Date(a+'T12:00'),B=new Date(b+'T12:00');const m=x=>x.toLocaleDateString('es-ES',{month:'short'}).replace('.','');
  return a===b?`${A.getDate()} ${m(A)}`:(A.getMonth()===B.getMonth()?`${A.getDate()}-${B.getDate()} ${m(B)}`:`${A.getDate()} ${m(A)} - ${B.getDate()} ${m(B)}`)}
const isDay=()=>L.periodType==='day';
function lum(hex){const n=parseInt(hex,16);const r=(n>>16)&255,g=(n>>8)&255,b=n&255;return (0.2126*r+0.7152*g+0.0722*b)/255}
function ink(t){const c=t.color,a=t.alt;if(lum(c)>0.28)return '#'+c;if(lum(a)>0.28&&a.toLowerCase()!=='ffffff')return '#'+a;return lum(c)>0.12?'#'+c:'#c4ced4'}
function hx(h){const n=parseInt(h.slice(1),16);return[(n>>16)&255,(n>>8)&255,n&255]}
function pair(ta,th){const a=ink(ta);let h=ink(th);const x=hx(a),y=hx(h);
  if(Math.hypot(x[0]-y[0],x[1]-y[1],x[2]-y[2])<90){h='#'+th.alt;const z=hx(h);if(lum(th.alt)<0.12||Math.hypot(x[0]-z[0],x[1]-z[1],x[2]-z[2])<90)h='#c4ced4'}
  return [a,h]}
function tc(t){return lum(t.color)<0.04?'#2a2f3a':'#'+t.color}
const logo=ab=>(IMG.t[CUR]||{})[ab]||'';
function credit(pid){const c=CR[pid];return c?esc('Foto: '+c.a+' · '+c.l+' · Wikimedia Commons'):''}
function photo(p){const src=IMG.p[p.pid];return src?`<img src="${src}" alt="${esc(p.n)}" title="${credit(p.pid)}" loading="lazy">`:''}
function initials(n){return String(n).split(' ').filter(Boolean).map(s=>s[0]).slice(0,2).join('')}
function splitName(t){const nick=t.short;const city=t.name.replace(' '+nick,'').trim();return {city:(city===t.name||city===nick)?'':city,nick}}
const qlbl=i=>i<4?(i+1)+'C':'PR'+(i>4?i-3:'');

/* ---------- partido ---------- */
function teamRow(g,side){
  const s=g.teams[side],t=TEAMS[s.abbr],nm=splitName(t);
  return `<div class="trow ${s.win?'win':''}" style="--tc:${tc(t)};--ti:${ink(t)}">
    <div class="lg"><img src="${logo(s.abbr)}" alt="${esc(t.name)}"></div>
    <div class="tn"><div class="city">${esc(nm.city)}</div><div class="nick">${esc(nm.nick)}</div><div class="rec">${esc(s.rec)}${s.ha==='home'?'<svg viewBox="0 0 24 24" aria-label="Local"><path d="M12 3l9 8h-3v9h-5v-6h-2v6H6v-9H3z"/></svg>':''}</div></div>
    <div class="qs">${s.ls.map(q=>`<span>${q}</span>`).join('')}</div>
    <div class="score">${s.score}</div>
  </div>`;
}
const STATS=[
  ['Tiros de campo','fieldGoalPct','fieldGoalsMade-fieldGoalsAttempted','%'],
  ['Triples','threePointFieldGoalPct','threePointFieldGoalsMade-threePointFieldGoalsAttempted','%'],
  ['Tiros libres','freeThrowPct','freeThrowsMade-freeThrowsAttempted','%'],
  ['Rebotes','totalRebounds','offensiveRebounds',' ofe.'],
  ['Asistencias','assists'],['Robos','steals'],['Tapones','blocks'],
  ['Pérdidas','totalTurnovers',null,null,true],['Valoración','valuation'],
  ['Pts. en pintura','pointsInPaint'],['Contraataque','fastBreakPoints'],['Tras pérdida','turnoverPoints'],
  ['Segundas opciones','secondChancePoints'],['Pts. banquillo','benchPoints'],['Faltas recibidas','foulsReceived'],['Máx. ventaja','largestLead']
];
function ring(v,c,lead){const r=26,C=2*Math.PI*r;return `<div class="ring ${lead?'lead':''}"><svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="${r}" fill="none" stroke="#243047" stroke-width="7"/><circle cx="32" cy="32" r="${r}" fill="none" stroke="${c}" stroke-width="7" stroke-linecap="round" stroke-dasharray="${C*v/100} ${C}"/></svg><b>${Math.round(v)}%</b></div>`}
function rings(g){
  const [A,H]=g.teams,[ca,ch]=pair(TEAMS[A.abbr],TEAMS[H.abbr]);
  return `<div class="rings">${STATS.slice(0,3).map(([k,key,sub])=>{const a=parseFloat(A.st[key])||0,h=parseFloat(H.st[key])||0;
    return `<div class="ring-box"><div class="rl">${k}</div><div class="ring-pair">${ring(a,ca,a>h)}${ring(h,ch,h>a)}</div><small><span>${A.st[sub]}</span><span>${H.st[sub]}</span></small></div>`}).join('')}</div>`;
}
function qchart(g){
  const [A,H]=g.teams,[ca,ch]=pair(TEAMS[A.abbr],TEAMS[H.abbr]);const n=Math.min(A.ls.length,H.ls.length);if(!n)return '';const mx=Math.max(...A.ls,...H.ls,1);
  const W=320,Hh=112,top=18,base=88,cw=W/n,bw=Math.min(22,cw/3.2);
  let o=`<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="Puntos por cuarto"><line x1="0" x2="${W}" y1="${base}" y2="${base}" stroke="#2c3954" stroke-width="1"/>`;
  for(let i=0;i<n;i++){const cx=cw*i+cw/2;
    [[A.ls[i],ca,-1],[H.ls[i],ch,1]].forEach(([v,c,dx])=>{const hgt=(v/mx)*(base-top);const x=cx+dx*(bw/2+2)-bw/2;
      o+=`<rect x="${x}" y="${base-hgt}" width="${bw}" height="${hgt}" rx="4" fill="${c}"/><text x="${x+bw/2}" y="${base-hgt-4}" text-anchor="middle" font-size="11" fill="#eef2f8">${v}</text>`;});
    const d=A.ls[i]-H.ls[i];
    o+=`<text x="${cx}" y="${base+14}" text-anchor="middle" font-size="10" fill="#8d99ae">${i<4?(i+1)+'º C':'PR'}</text>`;
    o+=`<text x="${cx}" y="${base+24}" text-anchor="middle" font-size="9.5" fill="${d===0?'#5d6a82':(d>0?ca:ch)}">${d===0?'=':(d>0?A.abbr:H.abbr)+' +'+Math.abs(d)}</text>`;
  }
  return `<div class="qchart">${o}</svg></div>`;
}
function cmp(g){
  const [A,H]=g.teams,[ca,ch]=pair(TEAMS[A.abbr],TEAMS[H.abbr]);
  return STATS.slice(3).filter(([,key])=>A.st[key]!==undefined&&A.st[key]!==''&&H.st[key]!==undefined).map(([k,key,subKey,unit,low])=>{
    const a=parseFloat(A.st[key])||0,h=parseFloat(H.st[key])||0,mx=Math.max(Math.abs(a),Math.abs(h),1);
    const la=low?a<h:a>h, lh=low?h<a:h>a;
    const sa=subKey&&A.st[subKey]!==undefined?`<small>${A.st[subKey]} ofe.</small>`:'', sh=subKey&&H.st[subKey]!==undefined?`<small>${H.st[subKey]} ofe.</small>`:'';
    return `<div class="cmp-row"><div class="v ${la?'lead':''}">${A.st[key]}${sa}</div><div class="bar l"><i style="width:${Math.max(0,a)/mx*100}%;--bc:${ca}"></i></div>
      <div class="k">${k}</div><div class="bar"><i style="width:${Math.max(0,h)/mx*100}%;--bc:${ch}"></i></div><div class="v r ${lh?'lead':''}">${H.st[key]}${sh}</div></div>`}).join('');
}
function crEx(p){
  if(p.fg) return `TC ${p.fg} · 3P ${p.tp}<br>${p.val!==undefined?'VAL '+p.val+' · ':''}ROB ${p.stl} · TAP ${p.blk} · ${p.pm}`;
  return `VAL ${p.val} · +/- ${p.pm}<br>${p.min} min${p.pf!==undefined?' · FP '+p.pf:''}`;
}
function topCol(s){
  const t=TEAMS[s.abbr];
  return `<div class="tcol" style="--tc:${tc(t)}"><h4><img src="${logo(s.abbr)}" alt="">${esc(t.short)} · Top 5</h4>
  <div class="cromos">${s.top.map((p,i)=>{const ph=photo(p);return `<div class="cromo ${i===0?'mvp':''}">
     <div class="cr-ph ${ph?'':'fb'}">${ph||initials(p.n)}<span class="cr-num">${esc(p.num)}</span><span class="cr-pos">${p.pos?esc(p.pos)+' · ':''}${p.min}'</span></div>
     <div class="cr-nm">${esc(p.n)}</div>
     <div class="cr-st"><div><b>${p.pts}</b><small>PTS</small></div><div><b>${p.reb}</b><small>REB</small></div><div><b>${p.ast}</b><small>AST</small></div></div>
     <div class="cr-ex">${crEx(p)}</div></div>`}).join('')}</div></div>`;
}
let uid=0;
function gameCard(g){
  const id='d'+(uid++);
  const nq=Math.max(g.teams[0].ls.length,4);
  const qlabels=Array.from({length:nq},(_,i)=>qlbl(i)).map(x=>`<span>${x}</span>`).join('');
  const [A,H]=g.teams,diff=Math.abs(A.score-H.score),[ca,ch]=pair(TEAMS[A.abbr],TEAMS[H.abbr]);
  const b=[];
  if(A.ls.length>4) b.push(`<span class="bdg ot">${A.ls.length>5?(A.ls.length-4)+' prórrogas':'Prórroga'}</span>`);
  if(diff>=20) b.push(`<span class="bdg blow">Paliza +${diff}</span>`); else if(diff<=5) b.push(`<span class="bdg close">Igualado · ${diff}</span>`);
  const mx=Math.max(0,...g.teams.flatMap(t=>t.top.map(p=>p.pts)));
  if(mx>=(CUR==='nba'?40:28)) b.push(`<span class="bdg big">${mx} pts</span>`);
  const tot=(A.score+H.score)||1;
  const when=CUR==='nba'?'':madrid(g.utc,{weekday:'short',day:'numeric',month:'short'}).replace(/\./g,'');
  return `<article class="game" id="g${g.id}" data-teams="${esc(A.abbr)},${esc(H.abbr)}" style="--ca:${ca};--ch:${ch}">
    <div class="g-head"><span class="badges"><span class="st">${when?esc(when):'Final'}</span>${b.join('')}</span><span class="ven">${esc(g.venue)}${g.city?'<span class="vc"> · '+esc(g.city)+'</span>':''}</span></div>
    <div class="qhead"><span></span><span></span><span class="qs">${qlabels}</span><span style="text-align:right">TOTAL</span></div>
    ${teamRow(g,0)}${teamRow(g,1)}
    <div class="margin" title="Reparto de puntos"><i style="width:${A.score/tot*100}%;background:${ca}"></i><i style="width:${H.score/tot*100}%;background:${ch}"></i></div>
    <div class="stars">${g.teams.map(s=>{const p=s.top[0];if(!p)return '';const t=TEAMS[s.abbr];const ph=photo(p);
      return `<div class="star" style="--tc:${tc(t)}"><div class="av ${ph?'':'fb'}">${ph||initials(p.n)}</div><div class="who"><div class="tg">Mejor de ${esc(t.short)}</div><b>${esc(p.n)}</b><span><em>${p.pts}</em> pts · ${p.reb} reb · ${p.ast} ast${CUR!=='nba'?' · '+p.val+' val':''}</span></div></div>`}).join('')}</div>
    <div class="g-foot">
      <button class="btn grow" type="button" aria-expanded="false" aria-controls="${id}" data-toggle="${id}"><span class="lbl-l">Estadísticas y top 5</span><span class="lbl-s">Detalles</span> <span class="car">▾</span></button>
      ${g.bx?`<button class="btn bx-btn" type="button" data-box="${esc(g.id)}"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14.5h18M9 4v16"/></svg>Ficha completa</button>`:''}
      <a class="btn primary" href="${esc(g.yt)}" target="_blank" rel="noopener">▶ Resumen</a>
    </div>
    <div class="g-detail" id="${id}" hidden>
      <div class="dtitle">Tiro</div>${rings(g)}
      <div class="dtitle">Puntos por cuarto</div>${qchart(g)}
      <div class="dtitle">Estadísticas de equipo</div><div class="cmp">${cmp(g)}</div>
      <div class="dtitle">Jugadores más destacados</div>
      <div class="tops">${topCol(g.teams[0])}${topCol(g.teams[1])}</div>
      ${(g.videos||[]).length?`<div class="dtitle clips-d">Jugadas destacadas</div><div class="clips">${g.videos.map(v=>`<a class="clip" href="${esc(v.u)}" target="_blank" rel="noopener"><span class="cd">▶ ${Math.floor(v.d/60)}:${String(v.d%60).padStart(2,'0')}</span><span class="ct">${esc(v.h)}</span></a>`).join('')}</div>`:''}
    </div>
  </article>`;
}

/* ---------- cifras ---------- */
function facts(day){
  const gs=day.games,P=[];
  gs.forEach(g=>g.teams.forEach(s=>s.top.forEach(p=>P.push({...p,abbr:s.abbr}))));
  const by=k=>[...P].sort((a,b)=>b[k]-a[k])[0];
  const tot=gs.reduce((s,g)=>s+g.teams[0].score+g.teams[1].score,0);
  const d=g=>Math.abs(g.teams[0].score-g.teams[1].score);
  const blow=[...gs].sort((a,b)=>d(b)-d(a))[0],close=[...gs].sort((a,b)=>d(a)-d(b))[0];
  const win=g=>g.teams.find(t=>t.win)||g.teams[0],los=g=>g.teams.find(t=>!t.win)||g.teams[1];
  const pf=(lbl,p,k,u)=>{const t=TEAMS[p.abbr],src=IMG.p[p.pid];return `<div class="fact" style="--tc:${tc(t)}"><div class="fl">${lbl}</div><div class="fv hot">${p[k]}<small style="font-size:16px;color:var(--muted)"> ${u}</small></div><div class="fs">${src?`<img class="av" src="${src}" alt="">`:`<img src="${logo(p.abbr)}" alt="">`}<span>${esc(p.n)}</span></div></div>`};
  const gf=(lbl,g,v)=>`<a class="fact" href="#g${g.id}"><div class="fl">${lbl}</div><div class="fv">${v}</div><div class="fs"><img src="${logo(win(g).abbr)}" alt=""><span>${win(g).score}-${los(g).score}</span><img src="${logo(los(g).abbr)}" alt=""></div></a>`;
  const third = CUR==='nba' ? pf('Más asistencias',by('ast'),'ast','AST') : pf('Mejor valoración',by('val'),'val','VAL');
  return `<div class="fact"><div class="fl">Partidos</div><div class="fv">${gs.length}</div><div class="fs"><span>${tot} puntos · ${(tot/gs.length/2).toFixed(0)} por equipo</span></div></div>`
   + pf('Máximo anotador',by('pts'),'pts','PTS') + pf('Más rebotes',by('reb'),'reb','REB') + third
   + gf('Mayor paliza',blow,'+'+d(blow)) + gf('Más igualado',close,d(close)+' pts');
}
function periodTitle(p){return isDay()?cap(fmtLong(p.key)):`${p.label} · ${range(p.from,p.to)}`}

/* ---------- portada ---------- */
function renderTop(){
  const T=TXT[CUR], night=L.periods[0];
  $('h1').innerHTML=T.h1;
  $('nightEyebrow').innerHTML='<span>'+(isDay()?cap(fmtLong(night.key))+' · '+new Date(night.key+'T12:00').getFullYear():`${night.label} · ${range(night.from,night.to)} ${night.to.slice(0,4)}`)+'</span>';
  const totalPts=night.games.reduce((s,g)=>s+g.teams[0].score+g.teams[1].score,0);
  $('nightSub').textContent=`${night.games.length} partidos · ${totalPts} puntos en total · media de ${(totalPts/night.games.length/2).toFixed(1)} por equipo`;
  $('facts').innerHTML=facts(night);
  // hero
  const sc=g=>{const d=Math.abs(g.teams[0].score-g.teams[1].score);return -d+(g.teams[0].ls.length>4?8:0)+(g.teams[0].score+g.teams[1].score)/60};
  const g=[...night.games].sort((a,b)=>sc(b)-sc(a))[0];const [A,H]=g.teams,ta=TEAMS[A.abbr],th=TEAMS[H.abbr];
  const team=(s,t)=>{const p=s.top[0];const src=p&&IMG.p[p.pid];return `<div class="h-team ${s.win?'':'lose'}"><img class="hl" src="${logo(s.abbr)}" alt="${esc(t.name)}"><div class="hn">${esc(t.short)}</div><div class="hr">${esc(s.rec)}</div>
    ${p?`<div class="h-star"><span class="av">${src?`<img src="${src}" alt="" title="${credit(p.pid)}">`:initials(p.n)}</span><span class="hs"><b>${esc(p.n)}</b><small><em>${p.pts}</em> pts · ${p.reb} reb · ${p.ast} ast</small></span></div>`:''}</div>`};
  const n=A.ls.length;
  $('hero').innerHTML=`<article class="hero" style="--a:${tc(ta)};--h:${tc(th)}"><div class="hero-in">
    ${team(A,ta)}
    <div class="h-mid"><span class="h-lbl">${T.hero}</span>
      <div class="h-score"><span class="${A.win?'':'lo'}" data-count="${A.score}">${A.score}</span><em>–</em><span class="${H.win?'':'lo'}" data-count="${H.score}">${H.score}</span></div>
      <div class="h-q" style="grid-auto-flow:row;grid-template-columns:repeat(${n+1},auto)"><span class="qh"></span>${A.ls.map((_,i)=>`<span class="qh">${qlbl(i)}</span>`).join('')}<span>${A.abbr}</span>${A.ls.map(v=>`<span>${v}</span>`).join('')}<span>${H.abbr}</span>${H.ls.map(v=>`<span>${v}</span>`).join('')}</div>
      <div class="h-btns"><a class="btn primary" href="${esc(g.yt)}" target="_blank" rel="noopener">▶ Ver resumen</a><a class="btn" href="#g${g.id}" data-open="g${g.id}">Estadísticas</a></div>
    </div>
    ${team(H,th)}
  </div></article>`;
  // destacados
  const all=[];night.games.forEach(g=>g.teams.forEach(s=>s.top.forEach(p=>all.push({...p,abbr:s.abbr,opp:g.teams.find(x=>x!==s).abbr,win:s.win}))));
  all.sort((a,b)=>b.gs-a.gs);
  $('leaders').innerHTML=all.slice(0,3).map((p,i)=>{const t=TEAMS[p.abbr];const ph=photo(p);return `
  <div class="leader" style="--tc:${tc(t)}"><div class="rank">${i+1}</div>
    ${ph?ph.replace('<img','<img class="ph"'):`<div class="ph fb" style="display:grid;place-items:center;font:900 40px var(--f-display);border-radius:50%;background:rgba(255,255,255,.12)">${initials(p.n)}</div>`}
    <div class="meta"><div class="lbl">${i===0?T.mvp:'Destacado'} · ${esc(t.short)} ${p.win?'gana a':'cae ante'} ${esc(TEAMS[p.opp].short)}</div>
    <div class="nm">${esc(p.n)}</div>
    <div class="line"><b>${p.pts}</b>PTS · ${p.reb} REB · ${p.ast} AST${CUR!=='nba'?' · '+p.val+' VAL':''}</div></div>
  </div>`}).join('');
  const fv=FAV[CUR];$('nightGames').innerHTML=[...night.games].sort((a,b)=>(b.teams.some(t=>t.abbr===fv)?1:0)-(a.teams.some(t=>t.abbr===fv)?1:0)).map(gameCard).join('');
  // ticker
  $('ticker').innerHTML=`<span class="tk-lbl">${T.tick||('J'+night.round)}</span>`+night.games.map(g=>`<a class="tk" href="#g${g.id}" data-teams="${g.teams.map(s=>esc(s.abbr)).join(',')}">${g.teams.map(s=>`<img src="${logo(s.abbr)}" alt=""><span class="${s.win?'w':'l'}">${esc(s.abbr)}</span><span class="s">${s.score}</span>`).join('')}</a>`).join('');
}
function countUp(){
  if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  [...document.querySelectorAll('#anoche [data-count]'),...document.querySelectorAll('#facts .fact .fv')].forEach(el=>{const node=el.firstChild;if(!node||node.nodeType!==3)return;const m=node.textContent.match(/^([+]?)(\d+)(.*)$/);if(!m)return;
    const to=+m[2],from=Math.round(to*.55),t0=performance.now(),dur=900;
    const step=t=>{const k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);node.textContent=m[1]+Math.round(from+(to-from)*e)+m[3];if(k<1)requestAnimationFrame(step)};requestAnimationFrame(step);});
}

/* ---------- por fechas / jornadas ---------- */
let past=[],shown=5,selected=null;
function dayBtn(d){
  let top,big,small;
  if(isDay()){const dt=new Date(d.key+'T12:00:00');top=dt.toLocaleDateString('es-ES',{weekday:'long'});big=dt.getDate();small=dt.toLocaleDateString('es-ES',{month:'short'}).replace('.','');}
  else{top=range(d.from,d.to);big=d.round;small='Jor.';}
  return `<button class="day" type="button" data-day="${d.key}" aria-pressed="${selected===d.key}">
    <span class="dw">${top}</span>
    <span><span class="dn">${big}</span><span class="dm">${small}</span></span>
    <span class="dc">${d.games.length} partido${d.games.length>1?'s':''}</span>
    <span class="mini">${d.games.slice(0,4).map(g=>{const w=g.teams.find(t=>t.win)||g.teams[0],l=g.teams.find(t=>t!==w);return `<div><img src="${logo(w.abbr)}" alt=""><span class="w">${esc(w.abbr)} ${w.score}</span><span>${l.score} ${esc(l.abbr)}</span></div>`}).join('')}${d.games.length>4?`<span class="more">+${d.games.length-4} más</span>`:''}</span>
  </button>`;
}
function renderDays(){
  const T=TXT[CUR];
  $('days').innerHTML=past.slice(0,shown).map(dayBtn).join('');
  const mb=$('moreBtn');
  if(shown>=past.length){mb.innerHTML=`Ocultar ${T.unit} anteriores <span class="car">▴</span>`;mb.dataset.mode='less';mb.hidden=past.length<=5;}
  else{mb.innerHTML=`Ver 5 ${T.unit} anteriores <span class="car">▾</span>`;mb.dataset.mode='more';mb.hidden=false;}
}
function renderPanel(){
  const el=$('dayPanel');const d=past.find(x=>x.key===selected);
  if(!d){el.innerHTML='';return}
  el.innerHTML=`<div class="panel-head"><h3>${esc(periodTitle(d))}</h3><span class="chip">${d.games.length} partidos</span></div><div class="facts">${facts(d)}</div>
   <div class="games">${d.games.map(gameCard).join('')}</div>`;
}

/* ---------- próximos ---------- */
let upSel=0;
function renderUp(){
  const U=L.upcoming||[];
  $('upTabs').innerHTML=U.map((d,i)=>`<button class="tab" type="button" data-up="${i}" aria-pressed="${i===upSel}">${esc(d.label)}${isDay()?' '+new Date(d.date+'T12:00').getDate():''} · ${d.games.length} partidos</button>`).join('');
  const d=U[upSel]; if(!d){$('upGrid').innerHTML='<p class="sub">No hay partidos programados.</p>';return}
  $('upGrid').innerHTML=d.games.map(g=>{const [A,H]=g.teams,ta=TEAMS[A.abbr],th=TEAMS[H.abbr];
    return `<article class="up" style="--a:${tc(ta)};--h:${tc(th)}">
      <div class="up-top"><span class="hr">${madrid(g.utc,{hour:'2-digit',minute:'2-digit'})}<small>${madrid(g.utc,isDay()?{weekday:'short'}:{weekday:'short',day:'numeric'}).replace('.','')}</small></span><span>${esc(g.venue)}</span></div>
      <div class="up-mid">
        <div class="up-t"><img src="${logo(A.abbr)}" alt=""><b>${esc(ta.short)}</b><span>${esc(A.rec)}</span></div>
        <div class="vs">@</div>
        <div class="up-t"><img src="${logo(H.abbr)}" alt=""><b>${esc(th.short)}</b><span>${esc(H.rec)}</span></div>
      </div>
      <div class="up-bot">${(g.tv||[]).map(t=>`<span class="tv">TV · ${esc(t)}</span>`).join('')}${g.odds?`<span class="tv od">Favorito ${esc(g.odds)}</span>`:''}</div>
    </article>`}).join('');
}

/* ---------- clasificación ---------- */
function confTable(grp){
  const z=grp.zones,n=grp.rows.length;
  const leg=[z.po?`<span><i style="background:var(--win)"></i>${CUR==='acb'?'Playoffs':'Playoffs'}</span>`:'',z.pi?`<span><i style="background:var(--accent)"></i>Play-in</span>`:'',z.rel?`<span><i style="background:var(--loss)"></i>Descenso</span>`:''].join('');
  return `<div class="conf"><h3>${esc(grp.name)}<span>${leg}</span></h3><div class="tbl-hint">Desliza para ver más →</div><div class="tbl-wrap"><table class="st">
  <thead><tr><th></th><th>Equipo</th><th>V-D</th><th>%</th><th>PF</th><th>PC</th><th>Dif.</th><th>Casa</th><th>Fuera</th><th>Racha</th><th title="Últimos 5 partidos, del más antiguo (izquierda) al más reciente (derecha)">Últimos 5 →</th></tr></thead><tbody>
  ${grp.rows.map(r=>{const t=TEAMS[r.abbr];const df=parseFloat(r.diff);
   const cls=r.seed<=z.po?'po':(z.pi&&r.seed<=z.pi?'pi':(z.rel&&r.seed>n-z.rel?'rel':''));
   const cut=(r.seed===z.po||r.seed===z.pi||(z.rel&&r.seed===n-z.rel))?'cut':'';
   const form=r.form?`<span class="form" title="Del más antiguo al más reciente">${r.form.slice(-5).map((x,i,a)=>`<i class="${x}${i===a.length-1?' last':''}">${x==='W'?'V':'D'}</i>`).join('')}</span>`:`<span class="dots" title="${r.l10}">${Array.from({length:10},(_,i)=>`<i class="${i<(parseInt(r.l10)||0)?'on':''}"></i>`).join('')}</span>`;
   return `<tr class="${cls} ${cut}" data-ab="${esc(r.abbr)}">
    <td class="sd"><span>${r.seed}</span></td>
    <td class="tm"><div><img src="${logo(r.abbr)}" alt=""><span>${esc(t.short)}</span></div></td>
    <td class="wl"><b>${r.w}-${r.l}</b></td>
    <td><span class="pct">${r.pct}</span><div class="pbar"><i style="width:${(r.w/Math.max(r.w+r.l,1))*100}%;--tcol:${ink(t)}"></i></div></td>
    <td>${r.ppg}</td><td>${r.opp}</td>
    <td class="${df>0?'pos':df<0?'neg':''}">${r.diff}</td>
    <td>${r.home}</td><td>${r.road}</td>
    <td><span class="strk ${(r.strk||'-')[0]}">${(r.strk||'-').replace(/^W/,'V').replace(/^L/,'D')}</span></td>
    <td>${form}</td>
   </tr>`}).join('')}</tbody></table></div></div>`;
}
function renderStandings(){
  $('stSub').textContent=TXT[CUR].stSub;
  $('standings').classList.toggle('one',L.standings.length===1);
  $('standings').innerHTML=L.standings.map(confTable).join('');
}

/* ---------- líderes ---------- */
function ldrCard(c){
  const p=c.ls[0];if(!p)return '';const t=TEAMS[p.abbr]||{short:p.abbr,color:'333333',alt:'999999'};
  const li=(x,j)=>{const tt=TEAMS[x.abbr]||t;const s=IMG.p[x.pid];return `<li style="--tc:${tc(tt)}" ${j>=5?'data-x hidden':''}><span class="r">${j+1}</span><span class="av ${s?'':'fb'}">${s?`<img src="${s}" alt="">`:`<img src="${logo(x.abbr)}" alt="" style="width:22px;height:22px;object-fit:contain;margin:auto">`}</span><span class="nm">${esc(x.n)}<small>${[x.abbr,x.pos].filter(Boolean).map(esc).join(' · ')}</small></span><span class="v">${x.v}</span></li>`};
  const src=IMG.p[p.pid];
  return `<article class="ldr"><div class="ldr-hero" style="--tc:${tc(t)}">
    <span class="cat">${esc(c.t)}</span><span class="val">${p.v}</span>
    <img class="tl" src="${logo(p.abbr)}" alt="">
    ${src?`<img class="ph" src="${src}" alt="${esc(p.n)}" title="${credit(p.pid)}">`:`<span class="ph-fb">${initials(p.n)}</span>`}
    <span class="who"><b>${esc(p.n)}</b><span>${[t.short,p.num?'#'+p.num:'',p.pos].filter(Boolean).map(esc).join(' · ')}</span></span></div>
    <ol>${c.ls.slice(1).map((x,j)=>li(x,j+1)).join('')}</ol>
    <button class="btn more10" type="button" data-more10 aria-expanded="false">Ver top 10 <span class="car">▾</span></button></article>`;
}

/* ---------- estadísticas de equipos ---------- */
const TSM=[['Puntos','avgPoints'],['Puntos recibidos','opp',1],['Diferencial','diff'],['Valoración','pir'],['Rebotes','avgRebounds'],['Rebotes ofensivos','avgOffensiveRebounds'],
  ['Asistencias','avgAssists'],['Robos','avgSteals'],['Tapones','avgBlocks'],['Pérdidas','avgTurnovers',1],['% Tiros de campo','fieldGoalPct'],['% Tiros de 2','twoPointPct'],
  ['% Triples','threePointPct'],['Triples anotados','avgThreePointFieldGoalsMade'],['% Tiros libres','freeThrowPct'],['Pts. en pintura','paintPoints'],['Contraataque','fastBreak'],['Pts. banquillo','benchPoints']];
let tsSel=0,ST={},TSA=[];
function tsVal(ab,k){if(k==='opp'||k==='diff')return parseFloat((ST[ab]||{})[k]);return parseFloat((L.teamstats[ab]||{})[k])}
function renderTS(){
  $('tsEyebrow').innerHTML=`<span>Ranking de los ${Object.keys(TEAMS).length} equipos</span>`;
  $('tsTabs').innerHTML=TSA.map((m,i)=>`<button class="tab" type="button" data-ts="${i}" aria-pressed="${i===tsSel}">${m[0]}</button>`).join('');
  const [lbl,k,low]=TSA[tsSel];
  const rows=Object.keys(TEAMS).map(ab=>({ab,v:tsVal(ab,k)})).filter(r=>!isNaN(r.v)).sort((a,b)=>low?a.v-b.v:b.v-a.v);
  const vs=rows.map(r=>r.v),mn=Math.min(...vs),mx=Math.max(...vs);const span=(mx-mn)||1,lo=mn-span*0.35;
  $('tsList').innerHTML=rows.map((r,i)=>{const t=TEAMS[r.ab];const w=low?(mx-r.v+span*0.35)/(span*1.35)*100:(r.v-lo)/(mx-lo)*100;
    return `<div class="ts-row ${i<3?'top3':''}"><span class="r">${i+1}</span><img src="${logo(r.ab)}" alt=""><span class="nm">${esc(t.short)}</span>
      <div class="ts-bar"><i style="width:${Math.max(4,Math.min(100,w))}%;--tcol:${ink(t)}"></i></div><span class="v">${k==='diff'&&r.v>0?'+':''}${r.v.toFixed(1)}${/Pct/.test(k)?'%':''}</span></div>`}).join('');
}

/* ---------- menú ---------- */
const IC={
 night:'<svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>',
 next:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 cal:'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
 table:'<svg viewBox="0 0 24 24"><path d="M8 21V11M12 21V5M16 21v-7M4 21h16"/></svg>',
 star:'<svg viewBox="0 0 24 24"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/></svg>',
 bars:'<svg viewBox="0 0 24 24"><path d="M4 6h10M4 12h16M4 18h7"/></svg>',
 grid:'<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="3"/><path d="M3 9h18M8 2v4M16 2v4M7.5 13h2M11 13h2M14.5 13h2M7.5 17h2M11 17h2"/></svg>'
};
function renderMenu(){
  const T=TXT[CUR],night=L.periods[0],U=(L.upcoming||[])[0],fu=U&&U.games[0];
  const st=L.standings,pl=L.leaders[0].ls[0],c0=L.leaders[0];
  const bestO=Object.keys(TEAMS).sort((a,b)=>tsVal(b,'avgPoints')-tsVal(a,'avgPoints'))[0];
  const stPrev=st.map(g=>{const r=g.rows[0];return `<img src="${logo(r.abbr)}" alt=""><em>${r.w}-${r.l}</em>${st.length>1?' '+esc(g.name.replace('Conferencia ','')):''}`}).join(' · ');
  const M=[
   ['#anoche',T.m1,IC.night,'#ff7a1a',`<em>${night.games.length} partidos</em> · resultados y resúmenes`],
   ['#proximos','Próximos partidos',IC.next,'#2f7cf6',fu?`<img src="${logo(fu.teams[0].abbr)}" alt=""><img src="${logo(fu.teams[1].abbr)}" alt="">${madrid(fu.utc,{weekday:'short'}).replace('.','')} a las <em>${madrid(fu.utc,{hour:'2-digit',minute:'2-digit'})}</em>`:'Sin partidos'],
   ['#fechas',T.m3,IC.cal,'#8b5cf6',`Últimas <em>${L.periods.length} ${T.unit}</em> con partido`.replace('Últimas','Últim'+(CUR==='nba'?'os':'as'))],
   ['#calendario','Calendario',IC.grid,'#0ea5a4',`Toda la temporada · <em>${(L.cal||[]).filter(g=>!g.done).length}</em> partidos por jugar`],
   ['#clasificacion','Clasificación',IC.table,'#16a36a',stPrev],
   ['#lideres','Líderes individuales',IC.star,'#d99a00',`${IMG.p[pl.pid]?`<img src="${IMG.p[pl.pid]}" alt="" style="border-radius:50%;object-fit:cover;object-position:top;background:${tc(TEAMS[pl.abbr])}">`:`<img src="${logo(pl.abbr)}" alt="">`}${esc(pl.n)} <em>${pl.v}</em> ${esc(c0.t.toLowerCase())}`],
   ['#miequipo','Mi equipo',IC.star,'#ffb100',favAb()?`<img src="${logo(favAb())}" alt="">${esc(TEAMS[favAb()].short)}`:'Elige tu equipo favorito'],
   ['#equipos','Estadísticas equipos',IC.bars,'#e5484d',`<img src="${logo(bestO)}" alt="">Mejor ataque: <em>${tsVal(bestO,'avgPoints').toFixed(1)}</em>`]
  ];
  $('menuGrid').innerHTML=M.map((m,i)=>`<a class="mp-item" href="${m[0]}" style="--ib:${m[3]}"><span class="n">${i+1}</span><span class="ic">${m[2]}</span><span><b>${m[1]}</b><span class="pv">${m[4]}</span></span></a>`).join('');
}

/* ---------- hoy: NBA desde las 17:00, EuroLiga y ACB desde las 12:00 (hora de España) ---------- */
const mdDate=ms=>new Date(ms).toLocaleDateString('en-CA',{timeZone:'Europe/Madrid'});
const mdHour=ms=>+new Date(ms).toLocaleString('en-GB',{timeZone:'Europe/Madrid',hour:'2-digit',hour12:false});
const OPEN_H={nba:17,el:12,acb:12};
function hoyPool(){
  const up=(L.upcoming||[]).flatMap(u=>u.games);
  const fin=L.periods.slice(0,2).flatMap(p=>p.games.map(g=>({id:g.id,utc:g.utc,venue:g.venue,tv:[],odds:'',state:'post',live:g.yt,yt:g.yt,
    teams:g.teams.map(t=>({abbr:t.abbr,rec:t.rec,score:t.score}))})));
  const seen=new Set(),out=[];[...up,...fin].forEach(g=>{if(g.utc&&!seen.has(g.id)){seen.add(g.id);out.push(g)}});return out;
}
function hoyWindow(now){
  if(CUR==='nba'){ // la noche NBA se juega de madrugada en España: de las 17:00 de hoy a las 12:00 de mañana
    const base=mdHour(now)<12?now-24*3600e3:now;const d0=mdDate(base),d1=mdDate(base+24*3600e3);
    return {day:base,test:t=>(mdDate(t)===d0&&mdHour(t)>=12)||(mdDate(t)===d1&&mdHour(t)<12),open:mdHour(now)>=OPEN_H.nba||mdHour(now)<12};
  }
  const d=mdDate(now);return {day:now,test:t=>mdDate(t)===d,open:null};
}
const PREVSC={};
function renderHoy(){
  const now=Date.now(),W=hoyWindow(now),sec=$('hoy');
  const gs=hoyPool().filter(g=>W.test(Date.parse(g.utc))).sort((a,b)=>Date.parse(a.utc)-Date.parse(b.utc));
  const first=gs.length?Date.parse(gs[0].utc):0;
  const open=gs.length&&(W.open!==null?W.open:(mdHour(now)>=OPEN_H[CUR]||now>=first-2*3600e3));
    if(open&&CUR==='nba'&&mdHour(now)<12&&gs.every(g=>g.state==='post'||now>Date.parse(g.utc)+3.5*3600e3)){sec.hidden=true;$('hoyGrid').innerHTML='';return}
  sec.hidden=!open; if(!open){$('hoyGrid').innerHTML='';return}
  const left=ms=>{const m=Math.round(ms/60000);return m>=60?`${Math.floor(m/60)} h${m%60?' '+m%60+' min':''}`:`${m} min`};
  let live=0,done=0;
  $('hoyGrid').innerHTML=gs.map(g=>{const [A,H]=g.teams,ta=TEAMS[A.abbr],th=TEAMS[H.abbr],t=Date.parse(g.utc);
    const sc=(A.score||H.score)?`${A.score}-${H.score}`:'';
    let st,cls='',btn='';
    if(g.state==='post'){done++;st=`Final${sc?' · '+sc:''}`;cls='done';btn=g.yt?`<a class="btn primary" href="${esc(g.yt)}" target="_blank" rel="noopener">▶ Resumen</a>`:''}
    else if(g.state==='in'||(now>=t&&now<t+2.5*3600e3)){live++;st='● En directo';cls='live';}
    else if(now<t){st=`Empieza en ${left(t-now)}`}
    else {done++;st='Terminado · resultado en la próxima actualización';cls='done'}
    if(!btn&&g.live&&g.state!=='post'&&now>=t-30*60e3) btn=`<a class="btn primary" href="${esc(g.live)}" target="_blank" rel="noopener">● Seguir en directo</a>`;
    const mid=sc?`<div class="lboard"><b class="${A.score>H.score?'w':''}" data-sk="${g.id}-a">${A.score}</b><i>–</i><b class="${H.score>A.score?'w':''}" data-sk="${g.id}-h">${H.score}</b>${cls==='live'&&g.detail?`<span class="lclock">${esc(g.detail)}</span>`:''}</div>`:'<div class="vs">@</div>';
    return `<article class="up ${cls}" style="--a:${tc(ta)};--h:${tc(th)}">
      <div class="up-top"><span class="hr">${madrid(g.utc,{hour:'2-digit',minute:'2-digit'})}<small>${madrid(g.utc,{weekday:'short'}).replace('.','')}</small></span><span>${esc(g.venue)}</span></div>
      <div class="up-mid${sc?' has-sc':''}"><div class="up-t"><img src="${logo(A.abbr)}" alt=""><b>${esc(ta.short)}</b><span>${esc(A.rec)}</span></div>${mid}
        <div class="up-t"><img src="${logo(H.abbr)}" alt=""><b>${esc(th.short)}</b><span>${esc(H.rec)}</span></div></div>
      <div class="stt"><span class="${cls}">${st}</span></div>
      ${btn?`<div class="stt">${btn}</div>`:''}
      <div class="up-bot">${(g.tv||[]).map(x=>`<span class="tv">TV · ${esc(x)}</span>`).join('')}${g.odds?`<span class="tv od">Favorito ${esc(g.odds)}</span>`:''}</div></article>`}).join('');
  document.querySelectorAll('#hoyGrid [data-sk]').forEach(el=>{const k=el.dataset.sk,v=el.textContent;if(PREVSC[k]!==undefined&&PREVSC[k]!==v){el.classList.remove('bump');void el.offsetWidth;el.classList.add('bump')}PREVSC[k]=v});
  $('hoyEyebrow').innerHTML=`<span>${cap(new Date(W.day).toLocaleDateString('es-ES',{timeZone:'Europe/Madrid',weekday:'long',day:'numeric',month:'long'}))}</span>`;
  $('hoyH2').innerHTML=CUR==='nba'?'Esta noche se <span class="hl">juega</span>':'Hoy hay <span class="hl">jornada</span>';
  const upd=UPDATED?new Date(UPDATED).toLocaleString('es-ES',{timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit'}):'';
  $('hoySub').textContent=`${gs.length} partido${gs.length>1?'s':''} · primer salto a las ${madrid(gs[0].utc,{hour:'2-digit',minute:'2-digit'})} (hora de España)${upd?' · datos actualizados a las '+upd:''}`;
  $('hoyChip').textContent=live?`● ${live} en directo`:(done===gs.length?'● Terminados':'● Próximamente');
}
setInterval(()=>{try{renderHoy()}catch(e){}},60000);


/* ---------- mi equipo (se guarda en el navegador de cada persona) ---------- */
let FAV={};try{FAV=JSON.parse(localStorage.getItem('offcourt-fav')||'{}')||{}}catch(e){FAV={}}
const favAb=()=>FAV[CUR]&&TEAMS[FAV[CUR]]?FAV[CUR]:null;
function saveFav(){try{localStorage.setItem('offcourt-fav',JSON.stringify(FAV))}catch(e){}}
function favGames(ab){const out=[];L.periods.forEach(p=>p.games.forEach(g=>{if(g.teams.some(t=>t.abbr===ab))out.push({g,p})}));return out}
function renderFav(){
  const ab=favAb(),box=$('miequipo');
  document.querySelectorAll('.fav').forEach(n=>n.classList.remove('fav'));
  if(!ab){box.innerHTML=`<div class="fav-empty"><span class="fav-star">★</span><div><b>Elige tu equipo de ${CUR==='nba'?'la NBA':CUR==='el'?'la EuroLiga':'la ACB'}</b><small>Verás sus partidos, su forma y su próximo rival al abrir la web</small></div><button class="btn primary" type="button" data-favpick>Elegir equipo</button></div>`;return}
  const t=TEAMS[ab],r=ST[ab]||{},grp=L.standings.find(gr=>gr.rows.some(x=>x.abbr===ab));
  const last=favGames(ab)[0];let lastHtml='<small class="fav-none">Sin partidos recientes</small>';
  if(last){const g=last.g,me=g.teams.find(x=>x.abbr===ab),op=g.teams.find(x=>x.abbr!==ab),p=me.top[0];
    lastHtml=`<a class="fav-res" href="#g${g.id}"><span class="wl ${me.win?'W':'L'}">${me.win?'V':'D'}</span><b>${me.score}-${op.score}</b><span>vs <img src="${logo(op.abbr)}" alt="">${esc(TEAMS[op.abbr].short)}</span></a>${p?`<small>Mejor: <b>${esc(p.n)}</b> · ${p.pts} pts · ${p.reb} reb · ${p.ast} ast</small>`:''}`}
  let nx=null;(L.upcoming||[]).forEach(u=>u.games.forEach(g=>{if(!nx&&g.teams.some(x=>x.abbr===ab)&&g.state!=='post')nx=g}));
  const nxHtml=nx?(()=>{const op=nx.teams.find(x=>x.abbr!==ab),home=nx.teams[1].abbr===ab;return `<div class="fav-next"><img src="${logo(op.abbr)}" alt=""><div><b>${home?'vs':'@'} ${esc(TEAMS[op.abbr].short)}</b><small>${cap(madrid(nx.utc,{weekday:'long',day:'numeric',month:'short'}))} · ${madrid(nx.utc,{hour:'2-digit',minute:'2-digit'})} h</small></div></div>`})():'<small class="fav-none">Sin partido programado</small>';
  const form=(r.form||[]).slice(-5).map((x,i,a)=>`<i class="${x}${i===a.length-1?' last':''}">${x==='W'?'V':'D'}</i>`).join('');
  box.innerHTML=`<div class="fav-card" style="--tc:${tc(t)};--ti:${ink(t)}">
    <img class="fav-logo" src="${logo(ab)}" alt="">
    <div class="fav-main"><small class="fav-k">★ Mi equipo</small><b class="fav-name">${esc(t.name)}</b>
      <div class="fav-meta"><span class="fav-pos">${r.seed?r.seed+'º':''}</span><span>${grp?esc(grp.name):''}</span><span class="fav-wl">${r.w??''}-${r.l??''}</span>${form?`<span class="form">${form}</span>`:''}</div></div>
    <div class="fav-col"><small class="fav-k">Último partido</small>${lastHtml}</div>
    <div class="fav-col"><small class="fav-k">Próximo partido</small>${nxHtml}</div>
    <button class="fav-change" type="button" data-favpick>Cambiar</button></div>`;
  document.querySelectorAll(`#standings tr[data-ab="${CSS.escape(ab)}"]`).forEach(n=>n.classList.add('fav'));
  document.querySelectorAll('.game').forEach(n=>{if(n.dataset.teams&&n.dataset.teams.split(',').includes(ab))n.classList.add('fav')});
  document.querySelectorAll('.tk').forEach(n=>{if(n.dataset.teams&&n.dataset.teams.split(',').includes(ab))n.classList.add('fav')});
}
function openPicker(){
  const ab=favAb();
  $('favPicker').innerHTML=`<div class="fp-box" role="dialog" aria-label="Elige tu equipo"><div class="fp-head"><b>Elige tu equipo</b><button type="button" class="fp-x" data-favclose aria-label="Cerrar">✕</button></div>
   <div class="fp-grid">${Object.keys(TEAMS).sort((a,b)=>TEAMS[a].short.localeCompare(TEAMS[b].short)).map(k=>`<button type="button" class="fp-t ${k===ab?'on':''}" data-fav="${esc(k)}" style="--tc:${tc(TEAMS[k])}"><img src="${logo(k)}" alt=""><span>${esc(TEAMS[k].short)}</span></button>`).join('')}</div>
   ${ab?'<button type="button" class="btn fp-clear" data-fav="">Quitar mi equipo</button>':''}</div>`;
  $('favPicker').hidden=false;
}
document.addEventListener('click',e=>{
  if(e.target.closest('[data-favpick]')){openPicker();return}
  const f=e.target.closest('[data-fav]');
  if(f){if(f.dataset.fav)FAV[CUR]=f.dataset.fav;else delete FAV[CUR];saveFav();$('favPicker').hidden=true;renderAll();return}
  if(e.target.closest('[data-favclose]')||e.target.id==='favPicker')$('favPicker').hidden=true;
});
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('favPicker').hidden=true});

/* ---------- calendario completo de la temporada ---------- */
let calSel=null,calFav=false;
const etToday=()=>new Date().toLocaleDateString('en-CA',{timeZone:'America/New_York'});
const addDays=(d,n)=>{const x=new Date(d+'T12:00:00Z');x.setUTCDate(x.getUTCDate()+n);return x.toISOString().slice(0,10)};
const monday=d=>{const x=new Date(d+'T12:00:00Z');const w=(x.getUTCDay()+6)%7;return addDays(d,-w)};
function calRow(g,showRound){
  const fv=favAb(),A=TEAMS[g.a]||{short:g.a},H=TEAMS[g.h]||{short:g.h},aw=g.done&&g.as>g.hs,hw=g.done&&g.hs>g.as;
  const when=`${madrid(g.utc,{weekday:'short',day:'numeric',month:'short'}).replace(/\./g,'')}<b>${g.done?'Final':madrid(g.utc,{hour:'2-digit',minute:'2-digit'})}</b>`;
  return `<div class="cg ${g.done?'done':''} ${(g.a===fv||g.h===fv)?'fav':''}">
    <span class="cg-w">${showRound&&g.r?`<i>J${g.r}</i>`:''}${when}</span>
    <span class="cg-t a ${aw?'w':''}"><b>${esc(A.short)}</b><img src="${logo(g.a)}" alt=""></span>
    <span class="cg-s">${g.done?`<b class="${aw?'w':''}">${g.as}</b><i>–</i><b class="${hw?'w':''}">${g.hs}</b>`:'<em>vs</em>'}</span>
    <span class="cg-t h ${hw?'w':''}"><img src="${logo(g.h)}" alt=""><b>${esc(H.short)}</b></span></div>`;
}
function renderCal(){
  const C=L.cal||[],sec=$('calendario');
  if(!C.length){sec.hidden=true;return} sec.hidden=false;
  const fv=favAb(),round=L.periodType==='round';
  const favBtn=fv?`<button class="tab cal-fav" type="button" data-calfav aria-pressed="${calFav}"><img src="${logo(fv)}" alt="">Solo ${esc(TEAMS[fv].short)}</button>`:'';
  if(calFav&&fv){
    const mine=C.filter(g=>g.a===fv||g.h===fv),w=mine.filter(g=>g.done&&((g.a===fv&&g.as>g.hs)||(g.h===fv&&g.hs>g.as))).length,l=mine.filter(g=>g.done).length-w;
    $('calCtl').innerHTML=favBtn;
    $('calSub').textContent=`Temporada de ${TEAMS[fv].name}: ${mine.length} partidos · ${w}-${l} · quedan ${mine.filter(g=>!g.done).length}`;
    let html='',mo='';
    mine.forEach(g=>{const m=cap(madrid(g.utc,{month:'long',year:'numeric'}));if(m!==mo){html+=`<div class="cal-m">${m}</div>`;mo=m}html+=calRow(g,round)});
    $('calList').innerHTML=html;
    const nx=$('calList').querySelector('.cg:not(.done)');if(nx)nx.classList.add('next');
    return;
  }
  if(round){
    const rs=[...new Set(C.map(g=>g.r))].sort((a,b)=>a-b);
    if(calSel===null||!rs.includes(calSel)){const pend=C.find(g=>!g.done);calSel=pend?pend.r:rs[rs.length-1]}
    const gs=C.filter(g=>g.r===calSel),ds=gs.map(g=>g.utc).sort();
    $('calCtl').innerHTML=`<button class="cal-arr" type="button" data-calstep="-1" aria-label="Jornada anterior">‹</button><div class="cal-chips" id="calChips">${rs.map(r=>{const done=C.filter(g=>g.r===r).every(g=>g.done);return `<button type="button" class="cal-c ${done?'past':''}" data-calr="${r}" aria-pressed="${r===calSel}"><small>Jor.</small><b>${r}</b></button>`}).join('')}</div><button class="cal-arr" type="button" data-calstep="1" aria-label="Jornada siguiente">›</button>${favBtn}`;
    $('calSub').textContent=`Jornada ${calSel} de ${rs.length} · ${range(mdDate(Date.parse(ds[0])),mdDate(Date.parse(ds[ds.length-1])))} · ${gs.length} partidos`;
    $('calList').innerHTML=gs.map(g=>calRow(g,false)).join('');
  } else {
    const days=new Set(C.map(g=>g.d));
    if(calSel===null||!days.has(calSel)){const t=etToday();calSel=[...days].sort().find(d=>d>=t)||[...days].sort().pop()}
    const m0=monday(calSel),week=[0,1,2,3,4,5,6].map(i=>addDays(m0,i));
    $('calCtl').innerHTML=`<button class="cal-arr" type="button" data-calw="-7" aria-label="Semana anterior">‹</button><div class="cal-chips" id="calChips">${week.map(d=>{const n=C.filter(g=>g.d===d).length,dt=new Date(d+'T12:00:00Z');return `<button type="button" class="cal-c ${d<etToday()?'past':''} ${n?'':'empty'}" ${n?`data-cald="${d}"`:'disabled'} aria-pressed="${d===calSel}"><small>${dt.toLocaleDateString('es-ES',{weekday:'short',timeZone:'UTC'}).replace('.','')}</small><b>${dt.getUTCDate()}</b><i>${n?n+' p.':'—'}</i></button>`}).join('')}</div><button class="cal-arr" type="button" data-calw="7" aria-label="Semana siguiente">›</button>${favBtn}`;
    const gs=C.filter(g=>g.d===calSel);
    $('calSub').textContent=`${cap(new Date(calSel+'T12:00:00Z').toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long',timeZone:'UTC'}))} (fecha de EE. UU.) · ${gs.length} partidos · horario de España`;
    $('calList').innerHTML=gs.map(g=>calRow(g,false)).join('');
  }
  const on=document.querySelector('#calChips [aria-pressed="true"]');if(on){const box=on.parentElement;box.scrollLeft=on.offsetLeft-(box.clientWidth-on.offsetWidth)/2}
}
document.addEventListener('click',e=>{
  const C=L.cal||[];let b;
  if((b=e.target.closest('[data-calr]'))){calSel=+b.dataset.calr;renderCal()}
  else if((b=e.target.closest('[data-cald]'))){calSel=b.dataset.cald;renderCal()}
  else if((b=e.target.closest('[data-calstep]'))){const rs=[...new Set(C.map(g=>g.r))].sort((a,b)=>a-b);const i=rs.indexOf(calSel)+(+b.dataset.calstep);if(rs[i]!==undefined){calSel=rs[i];renderCal()}}
  else if((b=e.target.closest('[data-calw]'))){const ds=[...new Set(C.map(g=>g.d))].sort();const tgt=addDays(calSel,+b.dataset.calw);const m=monday(tgt);calSel=ds.find(d=>d>=m&&d<addDays(m,7))||tgt;renderCal()}
  else if(e.target.closest('[data-calfav]')){calFav=!calFav;renderCal()}
});

/* ---------- liga ---------- */
function renderAll(){
  L=LG[CUR];TEAMS=L.teams;uid=0;
  document.querySelectorAll('[data-lg]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.lg===CUR));
  document.documentElement.dataset.league=CUR;
  const T=TXT[CUR];
  $('perH2').innerHTML=T.perH2;$('perSub').textContent=T.perSub;$('upSub').textContent=T.upSub;
  $('srcTxt').textContent=T.src;$('valTxt').textContent=T.val;
  past=L.periods.slice(1);shown=5;selected=past[0]&&past[0].key;upSel=0;tsSel=0;
  ST={};L.standings.forEach(g=>g.rows.forEach(r=>ST[r.abbr]=r));
  TSA=TSM.filter(([,k])=>Object.keys(TEAMS).some(ab=>!isNaN(tsVal(ab,k))));
  renderHoy();renderTop();renderUp();renderDays();renderPanel();renderStandings();
  $('leadersGrid').innerHTML=L.leaders.map(ldrCard).join('');
  calSel=null;renderTS();renderFav();renderCal();renderMenu();countUp();setHH();
}
function setLeague(k,scroll){setTimeout(()=>{try{liveTick()}catch(e){}},300);
  if(!LG[k]||k===CUR&&scroll!==undefined)return;CUR=k;
  try{localStorage.setItem('offcourt-league',k)}catch(e){}
  renderAll();
  if(scroll)window.scrollTo({top:0,behavior:'auto'});
}

/* ---------- eventos (una sola vez) ---------- */
document.addEventListener('click',e=>{
  const b=e.target.closest('[data-toggle]'); if(!b) return;
  const p=$(b.dataset.toggle); const open=p.hidden; p.hidden=!open; b.setAttribute('aria-expanded',open);
});
function goGame(id,open){
  const card=$(id); if(!card) return;
  if(open){const b=card.querySelector('[data-toggle]');if(b&&b.getAttribute('aria-expanded')!=='true')b.click();}
  const head=document.querySelector('header.top').getBoundingClientRect().bottom;
  const y=window.scrollY+card.getBoundingClientRect().top-head-14;
  window.scrollTo({top:Math.max(0,y),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  card.classList.remove('flash');void card.offsetWidth;card.classList.add('flash');
}
document.addEventListener('click',e=>{const a=e.target.closest('a[href^="#g"]');if(!a)return;e.preventDefault();goGame(a.getAttribute('href').slice(1),a.hasAttribute('data-open'));});
$('days').addEventListener('click',e=>{const b=e.target.closest('[data-day]');if(!b)return;selected=selected===b.dataset.day?null:b.dataset.day;renderDays();renderPanel();
  if(selected)$('dayPanel').scrollIntoView({behavior:'smooth',block:'start'});});
$('moreBtn').addEventListener('click',e=>{const m=e.currentTarget.dataset.mode;shown=m==='more'?Math.min(shown+5,past.length):5;
  if(m==='less'&&past.findIndex(x=>x.key===selected)>=5){selected=null;renderPanel();}renderDays();});
$('upTabs').addEventListener('click',e=>{const b=e.target.closest('[data-up]');if(!b)return;upSel=+b.dataset.up;renderUp()});
$('leadersGrid').addEventListener('click',e=>{const b=e.target.closest('[data-more10]');if(!b)return;
  const card=b.closest('.ldr');const open=b.getAttribute('aria-expanded')!=='true';card.querySelectorAll('[data-x]').forEach(li=>li.hidden=!open);
  b.setAttribute('aria-expanded',open);b.firstChild.textContent=open?'Ver top 5 ':'Ver top 10 ';});
$('tsTabs').addEventListener('click',e=>{const b=e.target.closest('[data-ts]');if(!b)return;tsSel=+b.dataset.ts;renderTS()});
$('leagues').addEventListener('click',e=>{const b=e.target.closest('[data-lg]');if(b)setLeague(b.dataset.lg,true)});
const mBtn=$('menuBtn'),mPanel=$('menuPanel');
function setMenu(o){if(o&&matchMedia('(max-width:560px)').matches){const t=Math.max(0,document.querySelector('header.top').getBoundingClientRect().bottom)+8;mPanel.style.top=t+'px';mPanel.style.maxHeight=(innerHeight-t-12)+'px'}else{mPanel.style.top=mPanel.style.maxHeight=''}
  mPanel.hidden=!o;mBtn.setAttribute('aria-expanded',o)}
mBtn.addEventListener('click',e=>{e.stopPropagation();setMenu(mPanel.hidden)});
mPanel.addEventListener('click',e=>{if(e.target.closest('a'))setMenu(false)});
document.addEventListener('click',e=>{if(!mPanel.hidden&&!e.target.closest('.menu'))setMenu(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false)});
/* ---------- ficha completa del partido (todos los jugadores) ---------- */
const BOX={};let boxCur=null;
function loadBox(lg){if(!BOX[lg])BOX[lg]=fetch('box/'+lg+'.json?v='+encodeURIComponent(UPDATED||'')).then(r=>{if(!r.ok)throw 0;return r.json()}).catch(e=>{delete BOX[lg];throw e});return BOX[lg]}
function findGame(id){for(const p of L.periods)for(const g of p.games)if(String(g.id)===String(id))return Object.assign({},g,{_day:p.key});return null}
const BXC=()=>[['min','Min','Minutos'],['pts','Pts','Puntos'],['reb','Reb','Rebotes'],['ast','Ast','Asistencias'],['fg','TC','Tiros de campo (anotados-intentados)'],['tp','T3','Triples'],['ft','TL','Tiros libres'],['or','RO','Rebotes ofensivos'],['dr','RD','Rebotes defensivos'],['stl','Rob','Robos'],['blk','Tap','Tapones'],['to','Pér','Pérdidas'],['pf','FP','Faltas personales'],['pm','+/-','Más/menos'],...(CUR!=='nba'?[['val','Val','Valoración']]:[])];
const nv=v=>{if(typeof v==='number')return v;const s=String(v||'');if(s.includes('-')&&!s.startsWith('-')&&!s.startsWith('+'))return parseInt(s)||0;return parseFloat(s)||0};
function boxTable(rows,side,sortK){
  const C=BXC();let rs=rows.slice();
  if(sortK)rs.sort((a,b)=>nv(b[sortK])-nv(a[sortK]));
  const best={};C.forEach(([k])=>{if(['min','pf','to','pm'].includes(k))return;best[k]=Math.max(...rows.map(r=>nv(r[k])))});
  const sum=k=>rows.reduce((t,r)=>t+nv(r[k]),0),pair=k=>{let m=0,a=0;rows.forEach(r=>{const x=String(r[k]||'0-0').split('-');m+=+x[0]||0;a+=+x[1]||0});return m+'-'+a};
  const pc=k=>{const [m,a]=pair(k).split('-').map(Number);return a?Math.round(m/a*100)+'%':'—'};
  const tr=(r,cls)=>`<tr class="${cls||''}"><th scope="row"><span class="bx-n">${r.num!==''&&r.num!=null?`<i>${esc(r.num)}</i>`:''}<b>${esc(r.n)}</b>${r.pos?`<small>${esc(r.pos)}</small>`:''}</span></th>${C.map(([k])=>{const v=r[k]??'';return `<td class="${best[k]&&nv(v)===best[k]&&best[k]>0?'top':''} ${k==='pts'?'pts':''}">${esc(v)}</td>`}).join('')}</tr>`;
  let body='';
  if(sortK){body=rs.map(r=>tr(r)).join('')}
  else{const st=rs.filter(r=>r.s),bn=rs.filter(r=>!r.s);
    body=(st.length?`<tr class="sep"><td colspan="${C.length+1}">Titulares</td></tr>`+st.map(r=>tr(r)).join(''):'')+(bn.length?`<tr class="sep"><td colspan="${C.length+1}">${st.length?'Banquillo':'Jugadores'}</td></tr>`+bn.map(r=>tr(r)).join(''):'')}
  const tot={n:'Total equipo',num:'',min:'',pts:sum('pts'),reb:sum('reb'),ast:sum('ast'),fg:pair('fg'),tp:pair('tp'),ft:pair('ft'),or:sum('or'),dr:sum('dr'),stl:sum('stl'),blk:sum('blk'),to:sum('to'),pf:sum('pf'),pm:'',val:sum('val')};
  const pct={n:'Porcentaje',num:'',fg:pc('fg'),tp:pc('tp'),ft:pc('ft')};
  return `<div class="bx-scroll"><table class="bx"><thead><tr><th scope="col">Jugador</th>${C.map(([k,l,t])=>`<th scope="col"><button type="button" data-bxsort="${k}" title="Ordenar por ${t}" aria-pressed="${sortK===k}">${l}</button></th>`).join('')}</tr></thead>
   <tbody>${body}</tbody><tfoot>${tr(tot,'tot').replace(/class="top ?/g,'class="')}${tr(pct,'pc').replace(/class="top ?/g,'class="')}</tfoot></table></div>`;
}
function renderBox(){
  const {g,rows,side,sort}=boxCur,[A,H]=g.teams,t=g.teams[side],T=TEAMS[t.abbr];
  const when=g.utc?madrid(g.utc,{weekday:'long',day:'numeric',month:'long'}):(/^\d{4}-\d\d-\d\d$/.test(g._day||'')?new Date(g._day+'T12:00:00Z').toLocaleDateString('es-ES',{timeZone:'UTC',weekday:'long',day:'numeric',month:'long'})+' (EE. UU.)':'');
  $('boxSheet').innerHTML=`<div class="bx-box" role="dialog" aria-modal="true" aria-label="Ficha completa del partido">
   <div class="bx-head"><div class="bx-score">${[A,H].map((s,i)=>`<span class="bx-tm ${s.win?'w':''}"><img src="${logo(s.abbr)}" alt=""><b>${esc(TEAMS[s.abbr].short)}</b><em>${s.score}</em></span>${i===0?'<i>–</i>':''}`).join('')}</div>
    <button type="button" class="fp-x" data-boxclose aria-label="Cerrar">✕</button></div>
   <div class="bx-sub">Ficha completa${when?' · '+esc(when):''}</div>
   <div class="bx-tabs" role="tablist">${[A,H].map((s,i)=>`<button type="button" role="tab" data-bxside="${i}" aria-selected="${i===side}" style="--tc:${tc(TEAMS[s.abbr])}"><img src="${logo(s.abbr)}" alt="">${esc(TEAMS[s.abbr].short)}</button>`).join('')}</div>
   ${boxTable(rows[side],side,sort)}
   <div class="bx-leg">Toca una columna para ordenar · <b>en color</b>: mejor dato del equipo · TC: tiros de campo · T3: triples · TL: tiros libres · RO/RD: rebotes ofensivos/defensivos${CUR!=='nba'?' · Val: valoración':''}</div></div>`;fitBox()
}
/* ajusta la tabla a la altura disponible para que no haga falta desplazarse */
function fitBox(){
  const sc=$('boxSheet').querySelector('.bx-scroll'),tb=sc&&sc.querySelector('table.bx');if(!tb)return;
  const bx=sc.closest('.bx-box');tb.style.zoom='';sc.style.overflowY='';bx.classList.remove('tight');
  const mob=matchMedia('(max-width:640px)').matches,minZ=mob?.8:.6;
  if(sc.scrollHeight-sc.clientHeight>1)bx.classList.add('tight');   // primero se quitan fecha y leyenda
  const over=sc.scrollHeight-sc.clientHeight;
  if(over>1){let z=1;for(let k=0;k<6&&sc.scrollHeight-sc.clientHeight>1&&z>minZ;k++){z=Math.max(minZ,Math.floor(z*sc.clientHeight/sc.scrollHeight*100)/100-.01);tb.style.zoom=z}}
  if(sc.scrollHeight-sc.clientHeight<=2)sc.style.overflowY='hidden';
}
addEventListener('resize',()=>{if(boxCur)fitBox()});
async function openBox(id){
  const g=findGame(id);if(!g)return;
  const sh=$('boxSheet');sh.hidden=false;document.body.classList.add('noscroll');
  sh.innerHTML='<div class="bx-box"><div class="bx-load">Cargando ficha completa…</div></div>';
  try{const all=await loadBox(CUR);const rows=all[String(id)];if(!rows)throw 0;
    const fv=favAb();boxCur={g,rows,side:g.teams[1].abbr===fv?1:0,sort:null};renderBox();}
  catch(e){sh.innerHTML='<div class="bx-box"><div class="bx-head"><b>Ficha no disponible</b><button type="button" class="fp-x" data-boxclose aria-label="Cerrar">✕</button></div><p class="bx-load">No se ha podido cargar la ficha de este partido. Prueba de nuevo en un rato.</p></div>'}
}
function closeBox(){$('boxSheet').hidden=true;document.body.classList.remove('noscroll');boxCur=null}
document.addEventListener('click',e=>{
  const b=e.target.closest('[data-box]');if(b){openBox(b.dataset.box);return}
  if(!boxCur&&$('boxSheet').hidden)return;
  if(e.target.closest('[data-boxclose]')||e.target.id==='boxSheet'){closeBox();return}
  const sd=e.target.closest('[data-bxside]');if(sd&&boxCur){boxCur.side=+sd.dataset.bxside;renderBox();return}
  const so=e.target.closest('[data-bxsort]');if(so&&boxCur){const k=so.dataset.bxsort;boxCur.sort=boxCur.sort===k?null:k;const x=$('boxSheet').querySelector('.bx-scroll').scrollLeft;renderBox();$('boxSheet').querySelector('.bx-scroll').scrollLeft=x}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('boxSheet').hidden)closeBox()});
/* ---------- modo claro / oscuro ---------- */
function setTheme(th,save=true){const r=document.documentElement;if(th==='light')r.dataset.theme='light';else delete r.dataset.theme;
  if(save)try{localStorage.setItem('offcourt-theme',th)}catch(e){}
  const m=document.querySelector('meta[name="theme-color"]');if(m)m.content=th==='light'?'#ffffff':'#070b13';
  $('themeBtn').setAttribute('aria-label',th==='light'?'Cambiar a modo oscuro':'Cambiar a modo claro')}
$('themeBtn').addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='light'?'dark':'light'));
setTheme(document.documentElement.dataset.theme==='light'?'light':'dark',false);
function setHH(){const h=document.querySelector('header.top'),tk=h.querySelector('.ticker'),mob=matchMedia('(max-width:640px)').matches,th=mob&&tk?tk.offsetHeight:0;
  document.documentElement.style.setProperty('--tkh',th+'px');document.documentElement.style.setProperty('--hh',(h.offsetHeight-th)+'px')}
addEventListener('resize',setHH);

/* créditos */
(function(){const NAMES={};Object.values(LG).forEach(l=>{l.periods.forEach(d=>d.games.forEach(g=>g.teams.forEach(t=>t.top.forEach(p=>NAMES[p.pid]=p.n))));l.leaders.forEach(c=>c.ls.forEach(p=>NAMES[p.pid]=p.n))});
  const list=Object.entries(CR).filter(([pid])=>IMG.p[pid]);
  $('crList').innerHTML=list.length?list.sort((a,b)=>(NAMES[a[0]]||'').localeCompare(NAMES[b[0]]||'')).map(([pid,c])=>`<div><b>${esc(NAMES[pid]||'')}</b>: ${esc(c.a)} · <a href="${esc(c.u)}" target="_blank" rel="noopener">${esc(c.l)}</a></div>`).join(''):'<div>Sin fotos todavía.</div>';})();

$('updTxt').textContent=new Date(UPDATED).toLocaleString('es-ES',{timeZone:'Europe/Madrid',day:'numeric',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'});
/* ---------- directo (solo en la web propia: el navegador consulta ESPN y EuroLiga) ---------- */
const LIVE = /*LIVE*/false;
async function liveTick(){
  if(!LIVE||document.hidden) return;
  try{
    if(CUR==='nba'){
      const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',{cache:'no-store'});
      const d=await r.json(); const by={};
      d.events.forEach(e=>by[e.id]=e);
      (LG.nba.upcoming||[]).forEach(u=>u.games.forEach(g=>{const e=by[g.id];if(!e)return;
        const st=e.status.type; g.state=st.state; g.detail=st.shortDetail;
        const c=e.competitions[0].competitors; const sc=ha=>+((c.find(x=>x.homeAway===ha)||{}).score||0);
        g.teams[0].score=sc('away'); g.teams[1].score=sc('home');}));
    } else if(CUR==='el'){
      const rounds=[...new Set((LG.el.upcoming||[]).map(u=>+(u.label.match(/\d+/)||[0])[0]).filter(Boolean))];
      for(const rn of rounds.slice(0,1)){
        const r=await fetch(`https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games?roundNumber=${rn}`,{cache:'no-store'});
        const d=(await r.json()).data; const by={}; d.forEach(x=>by['el'+x.gameCode]=x);
        LG.el.upcoming.forEach(u=>u.games.forEach(g=>{const x=by[g.id];if(!x)return;
          g.teams[0].score=x.road.score||0; g.teams[1].score=x.local.score||0;
          g.state=x.played?'post':((x.road.score||x.local.score)?'in':'pre'); g.detail='';}));
      }
    } else return;
    renderHoy();
  }catch(e){/* sin conexión: se queda con los datos de la última actualización */}
}
if(LIVE){setInterval(liveTick,15000);setTimeout(liveTick,1500);document.addEventListener('visibilitychange',liveTick);}

if(LIVE&&'serviceWorker' in navigator){addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}))}
try{const s=localStorage.getItem('offcourt-league');if(s&&LG[s])CUR=s}catch(e){}
renderAll();
</script>
