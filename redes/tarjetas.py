# Offcourt · tarjetas del día para redes (mismo diseño que el botón Compartir de la web)
# uso: python3 redes/tarjetas.py --liga nba|el|acb [--fecha AAAA-MM-DD] [--max 4]
#  -> redes/salida/<liga>/tarjetas/: 00_resultados_post.png y _historia.png (todos los resultados)
#     y NN_VIS-LOC_post.png / _historia.png de los partidos más interesantes
import os, sys, json, subprocess, argparse, threading, http.server, socketserver, functools, shutil
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--liga', default='nba'); ap.add_argument('--fecha', default=os.environ.get('OFFCOURT_FECHA', ''))
ap.add_argument('--max', type=int, default=4); a = ap.parse_args()
out = os.path.join(R, 'redes', 'salida', a.liga, 'tarjetas'); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(Q, directory=R)
srv = socketserver.TCPServer(('127.0.0.1', 0), H); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
js = os.path.join(R, 'redes', 'tarjetas.js')
r = subprocess.run(['node', js, f'http://127.0.0.1:{port}/', a.liga, a.fecha, str(a.max), out], capture_output=True, text=True)
srv.shutdown(); print(r.stdout.strip()); 
if r.returncode: sys.exit(r.stderr.strip() or 'error')
