// Renderiza la demo de FX: node redes/fx_demo.js [salida.mp4]  (30 fps, 1080x1920)
let chromium; for (const m of ['playwright', '/opt/npm-tools/node_modules/playwright', '/opt/node-tools/node_modules/playwright-core', 'playwright-core']) { try { chromium = require(m).chromium; break } catch (e) {} }
const { spawn } = require('child_process'), fs = require('fs');
(async () => {
  const out = process.argv[2] || __dirname + '/salida/fx_demo.mp4'; fs.mkdirSync(require('path').dirname(out), { recursive: true });
  const br = await chromium.launch({ args: ['--allow-file-access-from-files', '--use-gl=angle', '--use-angle=swiftshader'] });
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('pageerror', e => console.error('PAGEERR', e.message));
  await pg.goto('file://' + __dirname + '/fx_demo.html'); await pg.evaluate(() => window.ready);
  const n = Math.round(await pg.evaluate(() => window.DUR) * 30), t0 = Date.now();
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < n; f++) {
    await pg.evaluate(t => window.draw(t), f / 30);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (process.argv[3] === 'frames' && f % 30 === 15) fs.writeFileSync(out.replace('.mp4', `_${f}.jpg`), buf);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('ok', out, n, 'fotogramas ·', ((Date.now() - t0) / n).toFixed(0), 'ms por fotograma');
  await br.close();
})();
