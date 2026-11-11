# Vídeo resumen diario de Offcourt ("La noche NBA")

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
   - `ESPERANDO` con `minutos_restantes`: si son más de 55, termina sin avisar (la siguiente
     pasada lo volverá a mirar). Si son 55 o menos, ejecuta `python3 redes/video.py esperar`
     (fuerza la actualización de la web cada ~4 min, hasta 9 min por llamada) y repítelo hasta
     que salga `LISTO`. Si tras ~70 min sigue sin acabar, termina sin avisar.
   - `LISTO`: todos los partidos terminados y con estadísticas → sigue.

1. **Borrador**: `python3 redes/video.py borrador`
   Escribe `redes/salida/borrador.json` con la noche más reciente: partidos (ordenados por
   interés), estadísticas, jugadores (con `pid` y si tienen foto), crónica de ESPN, partidos
   de esta noche con hora española y las pronunciaciones ya conocidas.
   - Comprueba que `fecha` es la noche de ayer (hora España) y que los partidos están
     terminados. Si la web no está al día o no hubo partidos, no hagas vídeo y avisa.

2. **Guion**: escribe `redes/salida/noche.json` (formato abajo). Criterio editorial:
   - Español de España, tono de narrador deportivo con chispa, frases cortas. Nada de inventar:
     solo datos del borrador (la crónica de ESPN sirve para el contexto, p. ej. rachas o lesiones).
   - Intro de una o dos frases ("Buenos días. Esto es Offcourt…"), un segmento por partido
     (25–40 palabras, ~10–13 s) y un cierre con 2–3 partidos de esta noche.
   - Máximo 7 partidos narrados; si hay más, elige los más interesantes (la intro ya enseña
     todos los resultados). Empieza por el más llamativo.
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

6. **Render**: `python3 redes/video.py render` (~3 min) → `redes/salida/offcourt_noche_nba_FECHA.mp4`
   y `redes/salida/control.jpg` (un fotograma por escena). Míralo antes de enviar.

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
  {"id": "intro", "t": "Buenos días. Esto es Offcourt, y esto es lo que pasó anoche en la {NBA|ene be a}. Seis partidos. Vamos allá."},
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
- `voz`: `es-ES-AlvaroNeural:r` (por defecto, nombres adaptados). Otras probadas:
  `es-ES-ElviraNeural:r`, `en-US-AndrewMultilingualNeural:o` (nombres en inglés tal cual).
