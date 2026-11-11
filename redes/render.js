// uso: node render.js frames "i:t,i:t,..."   -> prueba_i_t.jpg
//      node render.js scene i out.mp4        -> vídeo de la escena i (30 fps, sin audio)
let chromium; for (const m of ['playwright', '/opt/npm-tools/node_modules/playwright', '/opt/node-tools/node_modules/playwright-core', 'playwright-core']) { try { chromium = require(m).chromium; break } catch (e) {} }
const CHROME = ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => require('fs').existsSync(p));
const { spawn } = require('child_process');
const fs = require('fs');
(async () => {
  const [mode, a, b] = process.argv.slice(2);
  const br = await chromium.launch({ executablePath: CHROME, args: ['--allow-file-access-from-files', '--disable-web-security'] });
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pg.on('pageerror', e => console.error('PAGEERR', e.message));
  pg.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()) });
  await pg.goto('file://' + __dirname + '/anim.html');
  await pg.evaluate(() => window.ready);
  const shot = () => pg.screenshot({ type: 'jpeg', quality: 92 });
  if (mode === 'frames') {
    for (const it of a.split(',')) {
      const [i, t] = it.split(':').map(Number);
      await pg.evaluate(([i, t]) => window.draw(i, t), [i, t]);
      fs.writeFileSync(`${__dirname}/salida/prueba_${i}_${t}.jpg`, await shot());
    }
  } else {
    const i = Number(a), out = b, tmp = out.replace(/\.mp4$/, '.tmp.mp4');
    const dur = await pg.evaluate(i => window.DATA.scenes[i].dur, i);
    const n = Math.round(dur * 30);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < n; f++) {
      await pg.evaluate(t => window.draw(window.__i, t), f / 30).catch(() => {});
      if (f === 0) { await pg.evaluate(i => { window.__i = i }, i); await pg.evaluate(t => window.draw(window.__i, t), 0) }
      const buf = await shot();
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code === 0) fs.renameSync(tmp, out); else { console.error('ffmpeg', code); process.exit(1) }
    console.log('ok', out, n);
  }
  await br.close();
})();
