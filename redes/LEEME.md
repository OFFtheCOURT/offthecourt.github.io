# FORMATO DE LOS VÍDEOS — NBA, EUROLIGA Y ACB (manda sobre el resto de este documento; se narran TODOS los partidos disputados)

Es el mismo formato para las tres ligas; cada una tiene su color (NBA azul/rojo, EuroLiga naranja, ACB verde),
que pone `montar` solo. **Voz: `es-ES-AlvaroNeural:r`** (la del vídeo de EuroLiga que eligió el usuario), a velocidad `+6%` y tono `-2Hz` (los valores por defecto; no subas la velocidad: suena robótica), con los nombres adaptados de
`redes/pronunciacion.json` y las siglas `{NBA|enebeá}`, `{Euroliga|Eurolíga}`, `{ACB|acebé}`.
**NBA — portada de SALA DE CINE**: una pantalla por partido con su resultado, público de figuritas y letrero.
La intro dice **3 o 4 ganchos** en una sola frase (8 palabras o más) y el segmento `intro` lleva `"focos"`: uno por
gancho, en orden, `{"clave": palabra del texto, "partido": "VIS-LOC", "etiqueta": "PALIZA +32"}` (etiqueta corta,
unas 16 letras como mucho). En cada foco la cámara vuela a esa pantalla; al final entra en la del PRIMER foco, así
que el primer resumen debe ser ese partido. Ejemplo de intro: "Paliza de los {Knicks|Niks}, treinta y seis de
{Paul George|Pol Yorch}, el récord de {Franz Wagner|Frants Váguener}, y {Portland|Pórtland} tumba al {Thunder|Zánder}."
Después, un mini resumen de **TODOS los partidos disputados** (una tarjeta cada uno; si hay muchos, una sola frase corta por partido) y el cierre
nombra 1-2 partidos de esta noche (`resaltar`) y termina con "Esto es {OFFCOURT|Ófkort}.".

Duración: lo justo para contar **todos los partidos**; como referencia, 60 s hasta 6 partidos y hasta ~90 s en noches de 10 o más (`montar` avisa si pasa de 95 s). Vertical 9:16 con zona segura: todo el contenido va reducido
al 86 % y subido, para que ni los bordes ni los subtítulos queden tapados por la interfaz de TikTok/Reels/Shorts.

1. **Intro (~3-4 s): pantalla de resultados + UN gancho.** Tarjetas con TODOS los partidos de la jornada (1 o 2
   columnas según cuántos haya, se adapta sola), local a la izquierda y visitante a la derecha, marcador que sube,
   ganador iluminado, etiqueta FINAL/PRÓRROGA. La voz NO va partido por partido ni lee lo que ya se ve: UNA sola
   frase con lo más llamativo de la jornada (canasta ganadora, remontada, paliza, récord) y entra directa al
   resumen de cada partido, empezando por el del gancho.
2. **Un resumen por partido destacado**, dinámico y sin relleno, con marcador en directo, pantallazos con la cifra
   del jugador (tarjetas) y detalle breve (último cuarto decisivo, mejores jugadores, balance). Reparto del tiempo
   según cuántos haya: 2 partidos → ~9 s cada uno; 3 → ~8 s; 4-6 → ~6 s (una frase y una tarjeta);
   7 o más → ~4-5 s cada uno (UNA frase de 8-14 palabras con el resultado y el protagonista). Se narran TODOS,
   ordenados de más a menos interesante (el primero, el del primer gancho).
3. **Final de partido decidido en el último tiro** (solo si el dato es seguro o lo indica el usuario): añade
   `"hero": true` al segmento de ese partido y la palabra clave "Hifi"/"canasta" en el texto; se anima la canasta ganadora.
4. **Cierre (~7 s):** próximos partidos de esa liga, destacando uno o dos (`resaltar`), y la frase final
   "Esto es {OFFCOURT|Ófkort}.", que dispara la tarjeta final con el logo.

# Vídeos resumen diarios de Offcourt (NBA, EuroLiga y ACB)

Un vídeo por cada liga que haya jugado: **NBA** cada mañana (la noche anterior), **EuroLiga**
y **ACB** por la noche, con los partidos de ese día. Todos los comandos aceptan `--liga nba|el|acb`
(por defecto `nba`) y trabajan en `redes/salida/<liga>/` (`noche.json`, `borrador.json`, el MP4…).
En EuroLiga y ACB los jugadores llevan también `valoracion`; úsala en las tarjetas (`28 PTS · 39 VAL`).
Para probar con un día pasado de EuroLiga/ACB: `OFFCOURT_FECHA=AAAA-MM-DD` delante de cada comando.

Vídeo vertical 9:16 (Reels, TikTok, Shorts) con un mini resumen de cada partido de la noche:
marcador, recreación animada con figuritas en los colores de cada equipo, tarjetas de los
jugadores destacados, voz natural en español y subtítulos palabra a palabra.

Todo sale de los datos que la web ya guarda en `index.html` (los actualiza el bot cada 15 min
de madrugada). La voz se genera en GitHub Actions (`.github/workflows/voz.yml`, voces
neuronales de Microsoft vía edge-tts) y se descarga desde la rama `redes-voz`.

## Pasos (los sigue la tarea programada cada mañana)

Desde la raíz del repo, con `main` al día (`git pull`):

0. **¿Ha acabado la noche?** `python3 redes/video.py estado` devuelve una línea JSON:
   - `HECHO`: el vídeo de esta noche ya se envió → no hagas nada más (termina sin avisar).
   - `SIN_PARTIDOS`: no hubo NBA → avisa en una línea y termina.
   - `ESPERANDO`: ejecuta `python3 redes/video.py esperar` (fuerza la actualización de la web cada
     ~4 min, hasta 9 min por llamada) y repítelo hasta que salga `LISTO`, como mucho 100 minutos.
   - `LISTO`: todos los partidos terminados y con estadísticas → sigue.

1. **Borrador**: `python3 redes/video.py borrador`
   Escribe `redes/salida/<liga>/borrador.json` con la noche más reciente: partidos (ordenados por
   interés), estadísticas, jugadores (con `pid` y si tienen foto), crónica de ESPN, partidos
   de esta noche con hora española y las pronunciaciones ya conocidas.
   - Comprueba que `fecha` es la noche de ayer (hora España) y que los partidos están
     terminados. Si la web no está al día o no hubo partidos, no hagas vídeo y avisa.

2. **Guion**: escribe `redes/salida/<liga>/noche.json` (formato abajo). Criterio editorial:
   - **Ritmo de redes**: nada de "Buenos días" ni presentaciones. La intro es UNA frase de impacto
     con el dato más fuerte de la noche ("¡Remontada en París y 33 de Payne!"). Cada partido: 15–25
     palabras, empezando por lo más llamativo (paliza, final apretado, récord, quién la rompió).
     Frases cortas, verbos de acción, sin relleno. El cierre, una sola frase.
   - Español de España, tono de narrador deportivo con chispa, frases cortas. Nada de inventar:
     solo datos del borrador (la crónica de ESPN sirve para el contexto, p. ej. rachas o lesiones).
   - Intro de una o dos frases ("Buenos días. Esto es Offcourt…"), un segmento por partido
     (25–40 palabras, ~10–13 s) y un cierre con 2–3 partidos de esta noche.
   - Máximo 7 partidos narrados; si hay más, elige los más interesantes (la intro ya enseña
     todos los resultados). Empieza por el más llamativo.
   - Siglas: NBA → `{NBA|enebeá}`, ACB → `{ACB|acebé}`, EuroLiga → `{Euroliga|Eurolíga}` (elegidas por el usuario; no cambiarlas).
   - Cifras en dígitos ("117 a 85"); balances en palabras ("nueve y dos").
   - **Todo nombre en inglés** (jugadores, equipos, ciudades, pabellones) va como
     `{Original|Pronunciación}`: la voz lee la pronunciación y los subtítulos muestran el original.
     Usa las de `redes/pronunciacion.json` si existen; para nombres nuevos escribe cómo lo diría
     un narrador español ("Shai Gilgeous-Alexander" → "Shei Gílyus Alexánder"). `montar` guarda
     las nuevas en el diccionario: haz commit del diccionario al terminar.
   - Tarjetas: 1–3 por partido, cada una ligada a una palabra del guion (`clave` = el
     original tal cual aparece entre llaves). La figurita de ese jugador se ilumina y tira
     cuando la voz lo nombra; los tiradores (3+ triples) tiran de tres, los pívots juegan al
     poste o machacan.

3. **Voz**: `python3 redes/video.py voz` (lanza el workflow, espera ~1 min y la descarga).

4. **Montar**: `python3 redes/video.py montar`

5. **Revisar**: `python3 redes/video.py fotogramas 1:6,2:9,3:4` (escena:segundo) y mira
   `redes/salida/prueba_*.jpg`: tarjetas, subtítulos, etiquetas de nombre.

6. **Render**: `python3 redes/video.py render` (~3 min) → `redes/salida/<liga>/offcourt_…_FECHA.mp4`
   y `redes/salida/<liga>/control.jpg` (un fotograma por escena). Míralo antes de enviar.

7. **Entregar**: envía el MP4 al usuario con una línea de resumen y, aparte, el texto del guion
   sin llaves por si lo quiere usar como descripción del post.
8. **Marcar como hecho**: `python3 redes/video.py hecho` y haz commit + push de
   `redes/hecho.json` y `redes/pronunciacion.json` (con `git pull --rebase` antes; el bot de la
   web también sube cambios). `redes/salida/` no se sube. Así las pasadas siguientes del día no repiten.

## Formato de `noche.json`

```json
{
 "fecha": "2026-11-10",
 "voz": "es-ES-AlvaroNeural:r",
 "segmentos": [
  {"id": "intro", "t": "Buenos días. Esto es Offcourt, y esto es lo que pasó anoche en la {NBA|enebeá}. Seis partidos. Vamos allá."},
  {"id": "BOS", "partido": "BOS-PHI",
   "t": "Exhibición de {Paul George|Pol Yorch} en {Philadelphia|Filadelfia}: 36 puntos…",
   "tarjetas": [
     {"clave": "Paul George", "pid": "4251", "linea": "36 PTS · 6 TRIPLES"},
     {"clave": "Suns", "equipo": "PHX", "stat": "triples"}
   ]},
  {"id": "outro", "t": "Esta noche, más: {Cleveland|Clívland} contra los {Knicks|Niks}…",
   "resaltar": {"CLE-NY": "Cleveland"}}
 ]
}
```

- `partido` = `VISITANTE-LOCAL` con las abreviaturas del borrador.
- Tarjeta de jugador: `pid` del borrador; opcional `nombre` (nombre completo si en el guion
  se usa uno corto, p. ej. "Giannis") y `etiqueta` (texto sobre la figurita).
- Tarjeta de equipo: `"stat": "triples"` (usa los triples del partido) o
  `"valor"`, `"titulo"`, `"linea"` a mano.
- `resaltar` del cierre: partido de esta noche → palabra del guion que lo ilumina.
- `voz`: `es-ES-AlvaroNeural:r` (por defecto). Otras probadas:
  `es-ES-ElviraNeural:r`, `en-US-AndrewMultilingualNeural:o` (nombres en inglés tal cual).

## Animaciones, gráficos y efectos (`redes/fx.js`)

`anim.html` carga las librerías de `redes/lib/` (sin conexión) y `redes/fx.js`:
GSAP 3.13 (curvas `oc.punch`, `oc.swoosh`, `oc.bounce`, MotionPath, Physics2D, ScrambleText), D3 7.9
(gráficos en el canvas), Lottie 5.12 (animaciones vectoriales) y PixiJS 7.4 + pixi-filters (post-procesado WebGL).
Todo depende solo del tiempo `t`, así que cada fotograma sale siempre igual.

- Acabado automático en cada fotograma (`fxPost` al final de `draw`): brillo (bloom) y viñeta;
  zoom blur al entrar en cada escena y onda de choque + separación de color cuando aparece cada tarjeta.
  Para desactivarlo: `"fx": false` en `noche.json`; grano de película opcional con `"grano": 0.02`
  (sube mucho el peso del MP4).
- Utilidades para nuevas escenas: `FX.p(t, t0, dur, 'back.out(2)')`, `FX.count(...)`, `FX.shake(...)`,
  `FX.text.reveal(...)` (letras una a una), `FX.text.scramble(...)`, `FX.path.at(FX.path.arc(...), p)` (trayectoria
  del balón), `FX.chart.bars / line / ring / versus` y `FX.lottie.load/draw`.
- Demo con todo: `node redes/fx_demo.js` → `redes/salida/fx_demo.mp4`.
- El renderizado con efectos es unas 4–5 veces más lento (WebGL por software): ~8 min para 60 s.
