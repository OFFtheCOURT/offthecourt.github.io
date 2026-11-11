#!/usr/bin/env bash
# Offcourt: descarga NBA, EuroLiga y ACB y genera index.html
set -e
cd "$(dirname "$0")"
mkdir -p build/img/t build/img/el build/img/acb build/img/w build/img/p
python3 -c "import PIL" 2>/dev/null || pip install -q pillow
python3 fetch.py      # NBA: resultados de los últimos 11 días
python3 fetch2.py     # NBA: próximos partidos, clasificación, líderes, equipos
python3 el_fetch.py   # EuroLiga
python3 acb_fetch.py  # ACB
python3 season.py     # temporada completa por jugador (fichas de jugador y equipo)
OFFCOURT_LIVE=1 OFFCOURT_OUT=index.html python3 build2.py   # genera index.html
