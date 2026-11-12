/* Offcourt · FX para los vídeos (redes/anim.html)
   Utilidades de animación y gráficos pensadas para el motor de fotogramas: todo es función del tiempo t
   (en segundos), así que un fotograma siempre sale igual y se puede renderizar a 30 fps sin saltos.

   Librerías (redes/lib, sin conexión):
     GSAP 3.13 (licencia estándar gratuita) · CustomEase, CustomBounce, CustomWiggle, EasePack,
       MotionPathPlugin, Physics2DPlugin, ScrambleTextPlugin
     D3 7.9 (ISC) · escalas, formas, interpolación de colores
     Lottie 5.12 (MIT) · animaciones vectoriales tipo After Effects (renderizador canvas)
     PixiJS 7.4 + pixi-filters 5.3 (MIT) · post-procesado WebGL: bloom, ondas de choque, zoom blur, RGB split...

   Uso rápido (dentro de draw):
     const p = FX.p(t, 0.2, 0.6, 'back.out(2)')      // progreso 0..1 con curva GSAP
     FX.chart.bars(X, {x,y,w,h, values:[...], colors:[...], p})
     FX.chart.line(X, {x,y,w,h, series:[[...],[...]], colors:[...], p})
     FX.chart.ring(X, {cx,cy,r, value:.62, color, p, label:'62%'})
     FX.text.reveal(X, 'PALIZA', x, y, p, {font, size, color})
     FX.path.at('M0,0 C100,-200 300,-200 400,0', p) // {x,y,angle}
     FX.post.frame(MX, t, {bloom:.6, grain:.04, vignette:.35, shock:{t0, x, y}, zoom:{t0, x, y}})
*/
(function () {
  const G = window.gsap;
  if (G) { try { G.registerPlugin(window.CustomEase, window.CustomBounce, window.CustomWiggle, window.MotionPathPlugin, window.Physics2DPlugin, window.ScrambleTextPlugin) } catch (e) {} }
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const EASES = {};
  const ease = spec => { if (typeof spec === 'function') return spec; spec = spec || 'power3.out'; if (!EASES[spec]) EASES[spec] = G ? G.parseEase(spec) : (x => 1 - Math.pow(1 - x, 3)); return EASES[spec] };
  if (G && window.CustomEase) {
    // curvas propias de Offcourt
    CustomEase.create('oc.punch', 'M0,0 C0.12,0.9 0.2,1.12 0.34,1.06 0.5,0.98 0.62,1 1,1');      // entra con golpe y asienta
    CustomEase.create('oc.swoosh', 'M0,0 C0.6,0 0.2,1 1,1');                                      // acelera y frena en seco
    if (window.CustomBounce) CustomBounce.create('oc.bounce', { strength: 0.55, squash: 1.4 });  // bote de balón
  }

  const FX = {
    gsap: G, d3: window.d3,
    ease,
    /** progreso 0..1 entre t0 y t0+dur con la curva indicada */
    p(t, t0, dur, spec) { return ease(spec)(clamp((t - t0) / Math.max(1e-6, dur))) },
    /** interpola un valor (número o color) */
    lerp(a, b, k) { return typeof a === 'string' && window.d3 ? d3.interpolate(a, b)(k) : a + (b - a) * k },
    /** contador que sube con curva (para marcadores) */
    count(t, t0, dur, from, to, spec = 'power2.out') { return Math.round(from + (to - from) * FX.p(t, t0, dur, spec)) },
    /** temblor determinista (para impactos) */
    shake(t, t0, dur = .35, amp = 14, seed = 1) {
      const k = clamp((t - t0) / dur); if (k <= 0 || k >= 1) return { x: 0, y: 0 };
      const d = (1 - k) * (1 - k) * amp, f = 38;
      return { x: Math.sin((t - t0) * f + seed) * d, y: Math.cos((t - t0) * f * 1.3 + seed * 2) * d };
    },
  };

  /* ---------------- texto ---------------- */
  FX.text = {
    /** letras que entran una a una (cada una sube y aparece) */
    reveal(ctx, txt, x, y, p, o = {}) {
      const font = `${o.weight || 900} ${o.size || 80}px ${o.font || 'BigS, sans-serif'}`; ctx.save(); ctx.font = font; ctx.textBaseline = o.baseline || 'alphabetic';
      const chars = [...txt], ws = chars.map(c => ctx.measureText(c).width), total = ws.reduce((a, b) => a + b, 0);
      let cx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x; const n = chars.length, st = o.stagger ?? .55;
      chars.forEach((c, i) => {
        const k = ease(o.ease || 'back.out(2.2)')(clamp((p - i / n * st) / (1 - st)));
        ctx.globalAlpha = clamp(k * 1.4) * (o.alpha ?? 1); ctx.fillStyle = o.color || '#fff';
        ctx.save(); ctx.translate(cx + ws[i] / 2, y + (1 - k) * (o.rise ?? 60)); ctx.scale(.6 + .4 * k, .6 + .4 * k); ctx.textAlign = 'center';
        if (o.stroke) { ctx.lineWidth = o.stroke; ctx.strokeStyle = o.strokeColor || '#000'; ctx.strokeText(c, 0, 0) } ctx.fillText(c, 0, 0); ctx.restore(); cx += ws[i];
      });
      ctx.restore();
    },
    /** texto que se "descifra" (letras aleatorias que se van fijando), determinista */
    scramble(txt, p, chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', seed = 7) {
      const n = txt.length, fixed = Math.floor(clamp(p) * n); let s = seed, out = '';
      for (let i = 0; i < n; i++) { s = (s * 9301 + 49297 + Math.floor(p * 40)) % 233280; out += i < fixed || txt[i] === ' ' ? txt[i] : chars[s % chars.length] }
      return out;
    },
  };

  /* ---------------- trayectorias (MotionPath) ---------------- */
  const RAW = {};
  FX.path = {
    /** punto a lo largo de un path SVG: {x, y, angle} */
    at(d, p) {
      const M = window.MotionPathPlugin; if (!M) return { x: 0, y: 0, angle: 0 };
      if (!RAW[d]) { const r = M.getRawPath(d); M.cacheRawPathMeasurements(r); RAW[d] = r }
      return M.getPositionOnPath(RAW[d], clamp(p), true);
    },
    /** arco de tiro desde (x0,y0) hasta (x1,y1) con altura h */
    arc(x0, y0, x1, y1, h) { const mx = (x0 + x1) / 2; return `M${x0},${y0} Q${mx},${Math.min(y0, y1) - h} ${x1},${y1}` },
  };

  /* ---------------- gráficos (D3 sobre canvas) ---------------- */
  FX.chart = {
    /** barras verticales que crecen; values: números; groups opcional para barras dobles por cuarto */
    bars(ctx, o) {
      const { x, y, w, h } = o, vals = o.values, n = vals.length, max = o.max ?? Math.max(...vals.flat());
      const gap = o.gap ?? .28, bw = w / n * (1 - gap), sy = window.d3 ? d3.scaleLinear([0, max], [0, h]) : (v => v / max * h);
      ctx.save();
      vals.forEach((v, i) => {
        const k = ease(o.ease || 'oc.punch')(clamp((o.p - i * (o.stagger ?? .08)) / .55)), bh = sy(v) * k, bx = x + i * w / n + w / n * gap / 2;
        const col = (o.colors && o.colors[i % o.colors.length]) || '#ff7a1a';
        const g = ctx.createLinearGradient(0, y + h - bh, 0, y + h); g.addColorStop(0, col); g.addColorStop(1, window.d3 ? d3.color(col).darker(1.2) + '' : col);
        ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(bx, y + h - bh, bw, bh, [Math.min(14, bw / 3), Math.min(14, bw / 3), 3, 3]); ctx.fill();
        if (o.labels !== false && k > .6) { ctx.globalAlpha = clamp((k - .6) / .4); ctx.fillStyle = o.labelColor || '#fff'; ctx.font = `900 ${o.labelSize || 40}px ${o.font || 'BigS, sans-serif'}`; ctx.textAlign = 'center'; ctx.fillText(Math.round(v * k), bx + bw / 2, y + h - bh - 12); ctx.globalAlpha = 1 }
      });
      ctx.restore();
    },
    /** líneas que se dibujan de izquierda a derecha (p. ej. diferencia en el marcador minuto a minuto) */
    line(ctx, o) {
      const { x, y, w, h } = o, S = o.series, n = Math.max(...S.map(s => s.length)), all = S.flat();
      const lo = o.min ?? Math.min(...all), hi = o.max ?? Math.max(...all), D = window.d3;
      const sx = i => x + w * i / (n - 1), sy = v => y + h - (v - lo) / ((hi - lo) || 1) * h;
      ctx.save(); ctx.beginPath(); ctx.rect(x - 20, y - 40, w * clamp(o.p) + 40, h + 80); ctx.clip();
      if (o.zero !== undefined) { ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.setLineDash([8, 10]); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, sy(o.zero)); ctx.lineTo(x + w, sy(o.zero)); ctx.stroke(); ctx.setLineDash([]) }
      S.forEach((s, j) => {
        const col = (o.colors && o.colors[j]) || '#fff', pts = s.map((v, i) => [sx(i), sy(v)]);
        if (o.area && D) { const a = D.area().x(d => d[0]).y0(sy(o.zero ?? lo)).y1(d => d[1]).curve(D.curveMonotoneX).context(ctx); ctx.beginPath(); a(pts); const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, D.color(col).copy({ opacity: .45 }) + ''); g.addColorStop(1, D.color(col).copy({ opacity: 0 }) + ''); ctx.fillStyle = g; ctx.fill() }
        ctx.beginPath(); if (D) D.line().curve(D.curveMonotoneX).context(ctx)(pts); else pts.forEach((q, i) => i ? ctx.lineTo(...q) : ctx.moveTo(...q));
        ctx.strokeStyle = col; ctx.lineWidth = o.width || 8; ctx.lineJoin = ctx.lineCap = 'round'; ctx.shadowColor = col; ctx.shadowBlur = o.glow ?? 18; ctx.stroke(); ctx.shadowBlur = 0;
      });
      ctx.restore();
      // punto que va en cabeza
      const i = clamp(o.p) * (n - 1), i0 = Math.floor(i), f = i - i0;
      S.forEach((s, j) => { const v = s[i0] + ((s[Math.min(i0 + 1, s.length - 1)] ?? s[i0]) - s[i0]) * f; ctx.fillStyle = (o.colors && o.colors[j]) || '#fff'; ctx.beginPath(); ctx.arc(sx(i), sy(v), (o.width || 8) * 1.3, 0, 7); ctx.fill() });
    },
    /** anillo de porcentaje (tiros, valoración...) */
    ring(ctx, o) {
      const { cx, cy, r } = o, k = ease(o.ease || 'power3.out')(clamp(o.p)), v = (o.value || 0) * k, lw = o.width || r * .2;
      ctx.save(); ctx.lineCap = 'round'; ctx.lineWidth = lw; ctx.strokeStyle = o.track || 'rgba(255,255,255,.12)'; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = o.color || '#ff7a1a'; ctx.shadowColor = o.color || '#ff7a1a'; ctx.shadowBlur = o.glow ?? 20; ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * v); ctx.stroke(); ctx.shadowBlur = 0;
      if (o.label !== false) { ctx.fillStyle = o.labelColor || '#fff'; ctx.font = `900 ${o.labelSize || r * .62}px ${o.font || 'BigS, sans-serif'}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(o.label ?? Math.round(v * 100) + '%', cx, cy + 2) }
      ctx.restore();
    },
    /** barras horizontales enfrentadas (comparativa de equipos: rebotes, asistencias...) */
    versus(ctx, o) {
      const { x, y, w } = o, rows = o.rows, rh = o.rowH || 70, mid = x + w / 2;
      ctx.save(); ctx.font = `700 ${o.labelSize || 30}px ${o.labelFont || 'BarlowC, sans-serif'}`; ctx.textBaseline = 'middle';
      rows.forEach((r, i) => {
        const k = ease('oc.punch')(clamp((o.p - i * .1) / .5)), yy = y + i * rh, m = Math.max(r.a, r.b) || 1, half = w / 2 - 120;
        ctx.globalAlpha = clamp(k * 2); ctx.fillStyle = 'rgba(255,255,255,.7)'; ctx.textAlign = 'center'; ctx.fillText(r.label.toUpperCase(), mid, yy);
        ctx.fillStyle = o.colorA || '#ff7a1a'; ctx.beginPath(); ctx.roundRect(mid - 110 - half * r.a / m * k, yy + 18, half * r.a / m * k, 14, 7); ctx.fill();
        ctx.fillStyle = o.colorB || '#386eff'; ctx.beginPath(); ctx.roundRect(mid + 110, yy + 18, half * r.b / m * k, 14, 7); ctx.fill();
        ctx.font = `900 ${o.valueSize || 44}px ${o.font || 'BigS, sans-serif'}`; ctx.fillStyle = r.a >= r.b ? '#fff' : 'rgba(255,255,255,.55)'; ctx.textAlign = 'left'; ctx.fillText(Math.round(r.a * k), x, yy + 4);
        ctx.fillStyle = r.b >= r.a ? '#fff' : 'rgba(255,255,255,.55)'; ctx.textAlign = 'right'; ctx.fillText(Math.round(r.b * k), x + w, yy + 4);
        ctx.font = `700 ${o.labelSize || 30}px ${o.labelFont || 'BarlowC, sans-serif'}`;
      });
      ctx.restore();
    },
  };

  /* ---------------- Lottie (animaciones vectoriales) ---------------- */
  const LOT = {};
  FX.lottie = {
    /** registra una animación (objeto JSON de Lottie); devuelve promesa cuando está lista */
    load(name, data) {
      if (!window.lottie) return Promise.resolve(false);
      return new Promise(res => {
        const c = document.createElement('canvas'); c.width = data.w; c.height = data.h;
        const a = lottie.loadAnimation({ renderer: 'canvas', loop: false, autoplay: false, animationData: data, rendererSettings: { context: c.getContext('2d'), clearCanvas: true } });
        a.addEventListener('DOMLoaded', () => { LOT[name] = { a, c, fr: data.fr, op: data.op, ip: data.ip || 0 }; res(true) });
      });
    },
    /** dibuja la animación en el instante `sec` (desde su inicio) */
    draw(ctx, name, sec, x, y, w, h, o = {}) {
      const L = LOT[name]; if (!L) return; const f = L.ip + sec * L.fr; if (f < L.ip || (!o.loop && f > L.op)) return;
      L.a.goToAndStop(o.loop ? L.ip + ((f - L.ip) % (L.op - L.ip)) : f, true); ctx.save(); ctx.globalAlpha = o.alpha ?? 1; ctx.drawImage(L.c, x, y, w ?? L.c.width, h ?? L.c.height); ctx.restore();
    },
  };

  /* ---------------- post-procesado (PixiJS + pixi-filters, WebGL) ---------------- */
  let R = null, SPR = null, TEX = null, F = {};
  FX.post = {
    ok: false,
    init(srcCanvas) {
      if (!window.PIXI || R) return FX.post.ok;
      try {
        R = new PIXI.Renderer({ width: srcCanvas.width, height: srcCanvas.height, preserveDrawingBuffer: true, backgroundAlpha: 1, antialias: false });
        TEX = PIXI.Texture.from(srcCanvas); SPR = new PIXI.Sprite(TEX); const P = PIXI.filters;
        F.bloom = new P.AdvancedBloomFilter({ threshold: .55, bloomScale: .7, brightness: 1, blur: 6, quality: 4 });
        F.shock = new P.ShockwaveFilter([540, 960], { amplitude: 14, wavelength: 150, brightness: 1.1, radius: 460, speed: 1100 });
        F.zoom = new P.ZoomBlurFilter({ strength: .12, center: [540, 960], innerRadius: 120 });
        F.rgb = new P.RGBSplitFilter([-4, 0], [0, 3], [4, 0]);
        F.rays = new P.GodrayFilter({ angle: 25, gain: .45, lacunarity: 2.6, alpha: .5, parallel: true });
        F.noise = new PIXI.NoiseFilter(.04, 1);
        F.vig = new PIXI.Filter(undefined, 'precision mediump float;varying vec2 vTextureCoord;uniform sampler2D uSampler;uniform float amt;void main(){vec4 c=texture2D(uSampler,vTextureCoord);vec2 d=vTextureCoord-.5;float v=1.-dot(d,d)*amt*2.4;gl_FragColor=vec4(c.rgb*clamp(v,0.,1.),c.a);}', { amt: .35 });
        FX.post.ok = true;
      } catch (e) { console.warn('FX.post sin WebGL', e); FX.post.ok = false }
      return FX.post.ok;
    },
    /**
     * Aplica el acabado al canvas final (se llama al final de draw).
     * o: {bloom:0..1, grain:0..0.1, vignette:0..1, rgb:px, rays:0..1,
     *     shock:{t0,x,y,dur}, zoom:{t0,x,y,dur,strength}}
     */
    frame(dstCtx, t, o = {}) {
      const cv = dstCtx.canvas; if (!FX.post.init(cv)) return;
      const list = [];
      if (o.zoom && t >= o.zoom.t0 && t < o.zoom.t0 + (o.zoom.dur || .35)) { const k = 1 - (t - o.zoom.t0) / (o.zoom.dur || .35); F.zoom.center = [o.zoom.x ?? 540, o.zoom.y ?? 960]; F.zoom.strength = (o.zoom.strength || .22) * k * k; list.push(F.zoom) }
      if (o.shock && t >= o.shock.t0 && t < o.shock.t0 + (o.shock.dur || .8)) { F.shock.center = [o.shock.x ?? 540, o.shock.y ?? 960]; F.shock.time = t - o.shock.t0; F.shock.amplitude = o.shock.amp ?? 14; F.shock.radius = o.shock.radius ?? 460; list.push(F.shock) }
      if (o.rays) { F.rays.time = t * .6; F.rays.alpha = o.rays; list.push(F.rays) }
      if (o.bloom) { F.bloom.bloomScale = o.bloom; list.push(F.bloom) }
      if (o.rgb) { const s = o.rgb; F.rgb.red = [-s, 0]; F.rgb.blue = [s, 0]; list.push(F.rgb) }
      if (o.vignette) { F.vig.uniforms.amt = o.vignette; list.push(F.vig) }
      if (o.grain) { F.noise.noise = o.grain; F.noise.seed = (Math.floor(t * 30) * 0.618) % 1; list.push(F.noise) }
      if (!list.length) return;
      TEX.update(); SPR.filters = list; R.render(SPR);
      dstCtx.save(); dstCtx.setTransform(1, 0, 0, 1, 0, 0); dstCtx.globalAlpha = 1; dstCtx.drawImage(R.view, 0, 0); dstCtx.restore();
    },
  };

  window.FX = FX;
})();
