// lo usa redes/tarjetas.py: abre la web y dibuja las tarjetas con sus propias funciones (shDraw, shDrawDay)
let chromium; for (const m of ['playwright', '/opt/npm-tools/node_modules/playwright', 'playwright-core']) { try { chromium = require(m).chromium; break } catch (e) {} }
const fs = require('fs'), path = require('path');
(async () => {
  const [url, lg, fecha, max, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.route(/goatcounter|gc\.zgo\.at|espn\.com|euroleague\.net|acb\.com/, r => r.abort());
  await p.addInitScript(l => { localStorage.setItem('offcourt-league', l) }, lg);
  await p.goto(url); await p.waitForFunction(() => typeof shDraw === 'function' && typeof L !== 'undefined');
  const r = await p.evaluate(async ([fecha, max]) => {
    // partidos del día: NBA = la noche (clave del periodo); Europa = partidos cuya fecha en España es ese día
    const md = u => new Date(u).toLocaleDateString('en-CA', { timeZone: 'Europe/Madrid' });
    let games = [], label = '';
    if (CUR === 'nba') { const per = fecha ? L.periods.find(p => p.key === fecha) : L.periods[0]; if (per) { games = per.games; label = new Date(per.key + 'T12:00Z').toLocaleDateString('es-ES', { day: 'numeric', month: 'long', timeZone: 'UTC' }) } }
    else { const all = L.periods.flatMap(p => p.games.map(g => ({ g, p }))); const day = fecha || (all.length ? all.map(x => md(x.g.utc)).sort().pop() : ''); games = all.filter(x => md(x.g.utc) === day).map(x => x.g); label = day ? new Date(day + 'T12:00Z').toLocaleDateString('es-ES', { day: 'numeric', month: 'long', timeZone: 'UTC' }) : '' }
    if (!games.length) return { n: 0 };
    const score = g => { const [A, H] = g.teams, d = Math.abs(A.score - H.score), m = shMvp(g); return (A.ls.length > 4 ? 30 : 0) + (d <= 5 ? 20 : 0) + (d >= 25 ? 12 : 0) + ((m && m.pts) || 0) };
    const top = [...games].sort((a, b) => score(b) - score(a)).slice(0, max);
    const files = [], url = c => c.toDataURL('image/png');
    const t = (CUR === 'nba' ? 'NBA · ' : CUR === 'el' ? 'EuroLiga · ' : 'ACB · ') + label;
    for (const fmt of ['post', 'story']) files.push(['00_resultados_' + (fmt === 'story' ? 'historia' : 'post') + '.png', url(await shDrawDay(games, t, fmt))]);
    let i = 1; for (const g of top) { const gg = findGame(g.id); for (const fmt of ['post', 'story']) files.push([String(i).padStart(2, '0') + '_' + g.teams.map(x => x.abbr).join('-').replace(/[^\w-]/g, '') + '_' + (fmt === 'story' ? 'historia' : 'post') + '.png', url(await shDraw(gg, fmt))]); i++ }
    return { n: games.length, files, top: top.map(g => g.teams.map(x => x.abbr + ' ' + x.score).join(' - ')) };
  }, [fecha, Number(max)]);
  if (!r.n) { console.log('SIN_PARTIDOS'); await b.close(); return }
  for (const [f, d] of r.files) fs.writeFileSync(path.join(out, f), Buffer.from(d.split(',')[1], 'base64'));
  console.log(`tarjetas: ${r.files.length} en ${out} · partidos del día ${r.n} · destacados: ${r.top.join(' | ')}`);
  await b.close();
})();
