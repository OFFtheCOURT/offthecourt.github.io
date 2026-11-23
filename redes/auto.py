# Offcourt · vídeos automáticos (los lanza GitHub Actions cada 10 minutos, sin depender de Claude)
#
#   python3 redes/auto.py            -> para cada liga: si sus partidos han acabado y aún no hay vídeo,
#                                       escribe el guion, genera la voz, monta, renderiza y deja el MP4
#                                       en redes/salida/<liga>/ y el registro en redes/videos.json
#   python3 redes/auto.py guion el   -> solo escribe el guion (noche.json) a partir del borrador, para probar
#
# El guion sigue el formato de LEEME.md: portada de cine con 3-4 titulares, una frase por partido
# (todos los disputados), próximos partidos y "Esto es Offcourt". Máximo 60 s: si se pasa, se acorta y se repite.
import os, sys, json, re, random, subprocess, datetime

R = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(R)
REG = os.path.join(R, 'videos.json')
PRON = json.load(open(os.path.join(R, 'pronunciacion.json'), encoding='utf-8'))
SIGLA = {'nba': '{NBA|enebeá}', 'el': '{Euroliga|Eurolíga}', 'acb': '{ACB|acebé}'}


def sh(*a, env=None, check=True):
    e = dict(os.environ, OFFCOURT_TTS_LOCAL='1', OFFCOURT_IGNORA_HECHO='1', **(env or {}))
    r = subprocess.run([sys.executable, os.path.join(R, 'video.py'), *a], env=e, capture_output=True, text=True)
    if check and r.returncode: raise RuntimeError(f"{' '.join(a)}: {(r.stderr or r.stdout)[-800:]}")
    return r.stdout


# ---------------------------------------------------------------- nombres con su pronunciación
def pr(nombre, solo_apellido=True):
    """'{Original|Pronunciación}' si lo sabemos; si no, el nombre tal cual"""
    if not nombre: return ''
    partes = nombre.split()
    ap = ' '.join(partes[1:]) if len(partes) > 1 else nombre
    ap = re.sub(r'\s+(Jr\.?|Sr\.?|II|III|IV)$', '', ap)
    if solo_apellido and ap in PRON: return '{%s|%s}' % (ap, PRON[ap])
    if nombre in PRON:
        if solo_apellido and len(partes) > 1:      # del nombre completo nos quedamos con la parte del apellido
            r = PRON[nombre].split()
            if len(r) == len(partes): return '{%s|%s}' % (ap, ' '.join(r[1:]))
        return '{%s|%s}' % (nombre, PRON[nombre])
    return ap if solo_apellido else nombre


def eq(t):
    """nombre corto del equipo, con pronunciación si la hay"""
    c = t['corto']
    return '{%s|%s}' % (c, PRON[c]) if c in PRON and PRON[c] != c else c


SINGULAR_NBA = {'Magic', 'Jazz', 'Heat', 'Thunder'}
GRANDES = {'Barça', 'Real Madrid'}
LIGA_ACT = 'nba'


def _art(c):
    if LIGA_ACT == 'nba': return 'el' if c in SINGULAR_NBA else 'los'
    return '' if c.startswith(('La ', 'El ')) else 'el'


def S(t, cap=False):
    """'los Celtics' / 'el Real Madrid' (con pronunciación)"""
    a = _art(t['corto']); r = (a + ' ' if a else '') + eq(t)
    return r[0].upper() + r[1:] if cap else r


def de(t):
    a = _art(t['corto']); return {'el': 'del ', 'los': 'de los ', '': 'de '}[a] + eq(t)


def al(t):
    a = _art(t['corto']); return {'el': 'al ', 'los': 'a los ', '': 'a '}[a] + eq(t)


def vb(t, sg, pl):
    return pl if _art(t['corto']) == 'los' else sg


def clave(txt):
    """la palabra que dispara la tarjeta/el foco: el original dentro de las llaves o la última palabra"""
    m = re.search(r'\{([^|}]*)\|', txt)
    return m.group(1) if m else txt.split()[-1]


# ---------------------------------------------------------------- guion
def guion(lg, nivel=0):
    b = json.load(open(os.path.join(R, 'salida', lg, 'borrador.json'), encoding='utf-8'))
    G = [g for g in b['partidos'] if g.get('terminado', True)]
    if not G: raise RuntimeError('sin partidos terminados')
    global LIGA_ACT; LIGA_ACT = lg
    rnd = random.Random(b['fecha'] + lg + str(nivel)); eu = lg != 'nba'
    info = []
    for g in G:
        V, Lc = g['visitante'], g['local']; W, Ls = (V, Lc) if V['puntos'] > Lc['puntos'] else (Lc, V)
        ot = max(0, len(V.get('cuartos') or []) - 4); m = W['puntos'] - Ls['puntos']
        todos = [(p, W) for p in W['jugadores']] or [(p, s) for s in (V, Lc) for p in s['jugadores']]
        tp, ts = max(todos, key=lambda x: (x[0].get('valoracion') or 0) * (1 if eu else 0) + x[0]['pts'])
        td = sum(1 for k in ('pts', 'reb', 'ast') if (tp.get(k) or 0) >= 10) >= 3
        hooks = []; P_ = pr(tp['nombre']); AP = re.sub(r'\s+(Jr\.?|Sr\.?|II|III|IV)$', '', tp['nombre']).split()[-1].upper(); pts = tp['pts']
        Wv_ = lambda sg, pl: vb(W, sg, pl)
        # cada tipo de titular tiene varias formas de decirse: cambia cada día y no se repite dentro del mismo vídeo
        if pts >= (25 if eu else 38): hooks.append((pts * (2.2 if eu else 1.5), 'pts', [(f"{pts} de {P_}", f"{pts} DE {AP}"), (f"{P_} se va a {pts}", f"{pts} DE {AP}"),
                                                                                    (f"exhibición de {P_}: {pts} puntos", f"{AP}: {pts} PTS"), (f"{P_} anota {pts}", f"{pts} DE {AP}"),
                                                                                    (f"{P_} enciende la noche con {pts}", f"{pts} DE {AP}"), (f"{pts} puntos de {P_}, imparable", f"{AP} IMPARABLE"),
                                                                                    (f"{P_} no falla: {pts} puntos", f"{pts} DE {AP}")]))
        if td: hooks.append((70, 'td', [(f"triple-doble de {P_}", 'TRIPLE-DOBLE'), (f"{P_} firma un triple-doble", 'TRIPLE-DOBLE'), (f"{P_} lo hace todo: triple-doble", 'TRIPLE-DOBLE'), (f"{P_} se sale con un triple-doble", 'TRIPLE-DOBLE')]))
        if ot:
            pr_ = 'la prórroga' if ot == 1 else str(ot) + ' prórrogas'; tg_ = 'PRÓRROGA' if ot == 1 else f'{ot} PRÓRROGAS'
            hooks.append((62 + 8 * ot, 'ot', [(f"{S(W)} {Wv_('gana', 'ganan')} en {pr_}", tg_), (f"{S(W)} {Wv_('sobrevive', 'sobreviven')} a {pr_}", tg_), (f"{'prórroga' if ot == 1 else pr_} y victoria {de(W)}", tg_), (f"{S(W)} {Wv_('resiste', 'resisten')} hasta {pr_}", tg_), (f"hasta {pr_}: {S(W)} {Wv_('se lo lleva', 'se lo llevan')}", tg_)]))
        if m >= 20: hooks.append((40 + m, 'paliza', [(f"paliza {de(W)}", f'PALIZA +{m}'), (f"{S(W)} {Wv_('arrasa', 'arrasan')} {al(Ls)}", f'+{m}'),
                                                     (f"{S(W)} {Wv_('pasa', 'pasan')} por encima {de(Ls)}", f'PALIZA +{m}'), (f"exhibición {de(W)}: más {m}", 'EXHIBICIÓN'), (f"{S(W)} no {Wv_('tiene', 'tienen')} piedad", f'PALIZA +{m}'),
                                                     (f"repaso {de(W)} {al(Ls)}", f'+{m}'), (f"{S(W)} {Wv_('humilla', 'humillan')} {al(Ls)}", f'PALIZA +{m}')]))
        if m <= 3 and not ot: hooks.append((58, 'ajustado', [(f"final de infarto entre {S(V)} y {S(Lc)}", 'FINAL DE INFARTO'), (f"{S(W)} {Wv_('gana', 'ganan')} por la mínima", 'POR LA MÍNIMA'),
                                                              (f"{S(W)} {Wv_('sufre', 'sufren')} hasta el final", 'AL LÍMITE'), (f"infarto: {S(W)} {Wv_('gana', 'ganan')} de {m}", f'+{m} AL FINAL'), (f"{S(W)} lo {Wv_('salva', 'salvan')} en el último segundo", 'AL LÍMITE'),
                                                              (f"agonía y victoria {de(W)}", 'FINAL DE INFARTO'), (f"partidazo hasta el final entre {S(V)} y {S(Lc)}", 'FINAL DE INFARTO')]))
        if eu and Ls['corto'] in GRANDES:   # en España lo que más interesa: cae un grande
            hooks.append((78, 'grande', [(f"{S(W)} {Wv_('tumba', 'tumban')} {al(Ls)}", f"CAE EL {Ls['corto'].upper()}"), (f"golpe {de(W)} {al(Ls)}", f"CAE EL {Ls['corto'].upper()}"),
                                         (f"{S(Ls)} cae ante {S(W)}", f"CAE EL {Ls['corto'].upper()}"), (f"bombazo: {S(W)} {Wv_('gana', 'ganan')} {al(Ls)}", f"CAE EL {Ls['corto'].upper()}"),
                                         (f"sorpresa: {S(Ls)} pierde con {S(W)}", f"CAE EL {Ls['corto'].upper()}")]))
        if not hooks and pts >= (18 if eu else 25): hooks.append((pts, 'pts', [(f"{pts} de {P_}", f"{pts} DE {AP}"), (f"{P_} se va a {pts}", f"{pts} DE {AP}")]))
        hooks.sort(key=lambda h: -h[0])
        info.append(dict(g=g, W=W, L=Ls, ot=ot, m=m, p=tp, ps=ts, td=td, hook=hooks[0] if hooks else None, score=(hooks[0][0] if hooks else 0) + g.get('interes', 0) / 10))
    info.sort(key=lambda x: -x['score'])
    con = [x for x in info if x['hook']][: (4 if nivel == 0 else 3)]
    if not con: con = info[:1]; con[0]['hook'] = (1, 'v', [(f"{eq(con[0]['W'])} gana {con[0]['W']['puntos']} a {con[0]['L']['puntos']}", 'VICTORIA')])
    usados = {}
    for x in con:   # (puntos, tipo, opciones) -> (puntos, frase, etiqueta), sin repetir forma dentro del mismo tipo
        sc_, tipo, ops_ = x['hook']; libres = [o for k, o in enumerate(ops_) if k not in usados.get(tipo, set())] or ops_
        o = rnd.choice(libres); usados.setdefault(tipo, set()).add(ops_.index(o)); x['hook'] = (sc_, o[0], o[1])
    frases = [x['hook'][1] for x in con]
    cap_ = lambda x: re.sub(r'^(\{?)(\w)', lambda m_: m_.group(1) + m_.group(2).upper(), x)
    intro = ' '.join('¡' + cap_(f) + '!' for f in frases)   # un titular por frase: deja respirar cada entrada
    # a veces, un arranque corto que sube la tensión antes de los titulares (cambia cada día)
    ARR = {'nba': ['¡Qué nochecita en la NBA!', '¡Locura anoche en la NBA!', '¡Atención a lo de anoche!', '¡Nochón de NBA!', '¡Vaya noche!'],
           'el': ['¡Qué jornada de Euroliga!', '¡Locura en la Euroliga!', '¡Atención a la Euroliga!', '¡Nochón europeo!'],
           'acb': ['¡Qué jornada en la ACB!', '¡Locura en la Liga Endesa!', '¡Atención a la ACB!', '¡Vaya jornada!']}
    if rnd.random() < .5: intro = rnd.choice(ARR.get(lg, ARR['nba'])) + ' ' + intro
    if len(intro.split()) < 8: intro = intro[:-1] + f', en la {SIGLA[lg]}!'
    primera = lambda h: re.sub(r'[{}|¡!]', ' ', h).split()[0]   # el titular entra con la primera palabra de su frase
    seg = [{'id': 'intro', 't': intro, 'velocidad': '+18%', 'tono': '+6Hz', 'focos': [{'clave': primera(x['hook'][1]), 'partido': x['g']['partido'], 'etiqueta': x['hook'][2][:18]} for x in con]}]
    orden = con + [x for x in info if x not in con]
    corto = nivel >= 1 or len(orden) >= 8
    usadas = set()
    for i, x in enumerate(orden):
        W, Ls, p = x['W'], x['L'], x['p']; w, l = W['puntos'], Ls['puntos']; P = pr(p['nombre'])
        Wv = lambda sg, pl: vb(W, sg, pl)
        if nivel >= 3 and i >= (6 if nivel == 3 else 4):      # noches largas: los partidos menores, en una frase mínima
            ops = [f"Ganan {S(W)} {al(Ls)}, {w} a {l}."] if nivel == 3 else [f"{w} a {l} para {S(W)}."]
        elif corto:
            ops = [f"{S(W, 1)} {Wv('gana', 'ganan')} {al(Ls)}, {w} a {l}, con {p['pts']} de {P}.",
                   f"{P} mete {p['pts']} y {S(W)} {Wv('gana', 'ganan')} {al(Ls)}, {w} a {l}.",
                   f"{S(W, 1)} {Wv('vence', 'vencen')} {al(Ls)}, {w} a {l}; {P} suma {p['pts']}.",
                   f"{w} a {l}: {S(W)} {Wv('puede', 'pueden')} con {S(Ls)} gracias a los {p['pts']} de {P}."]
        elif x['ot']:
            ops = [f"{S(W, 1)} {Wv('se lleva', 'se llevan')} el partidazo {al(Ls)} en la prórroga, {w} a {l}, con {p['pts']} de {P}.",
                   f"Hizo falta prórroga: {S(W)} {Wv('gana', 'ganan')} {al(Ls)}, {w} a {l}, y {P} firma {p['pts']}.",
                   f"Tiempo extra y triunfo {de(W)} ante {S(Ls)}, {w} a {l}, con {p['pts']} de {P}."]
        elif x['m'] >= 20:
            ops = [f"{S(W, 1)} {Wv('arrasa', 'arrasan')} {al(Ls)}, {w} a {l}, con {p['pts']} puntos de {P}.",
                   f"Paliza {de(W)} {al(Ls)}, {w} a {l}; {P} se va a {p['pts']}.",
                   f"Sin historia: {S(W)} {Wv('golea', 'golean')} {al(Ls)}, {w} a {l}, con {p['pts']} de {P}.",
                   f"{S(W, 1)} {Wv('pasa', 'pasan')} por encima {de(Ls)}, {w} a {l}, y {P} anota {p['pts']}."]
        elif x['m'] <= 3:
            ops = [f"{S(W, 1)} {Wv('gana', 'ganan')} por la mínima {al(Ls)}, {w} a {l}, y {P} firma {p['pts']}.",
                   f"Final apretado: {S(W)} {w}, {S(Ls)} {l}, con {p['pts']} de {P}.",
                   f"Sufrimiento hasta el final: {S(W)} {Wv('gana', 'ganan')} {al(Ls)}, {w} a {l}, con {p['pts']} de {P}.",
                   f"Se decidió en el último minuto: {w} a {l} para {S(W)}, con {p['pts']} de {P}."]
        else:
            ops = [f"{S(W, 1)} {Wv('gana', 'ganan')} {al(Ls)}, {w} a {l}, con {p['pts']} de {P}.",
                   f"{P} mete {p['pts']} y {S(W)} {Wv('supera', 'superan')} {al(Ls)}, {w} a {l}.",
                   f"Victoria {de(W)} ante {S(Ls)}, {w} a {l}, con {p['pts']} puntos de {P}.",
                   f"{S(W, 1)} {Wv('vence', 'vencen')} {al(Ls)}, {w} a {l}, y {P} se va a {p['pts']}.",
                   f"{w} a {l} para {S(W)} ante {S(Ls)}, con {p['pts']} de {P} como líder."]
        cat = 'corto' if corto else 'ot' if x['ot'] else 'paliza' if x['m'] >= 20 else 'ajustado' if x['m'] <= 3 else 'normal'
        libres = [k for k in range(len(ops)) if (cat, k) not in usadas] or list(range(len(ops)))   # no repetir la misma frase en el vídeo
        k = rnd.choice(libres); usadas.add((cat, k)); t = ops[k]
        if x['td'] and not corto: t = t + " ¡Con triple-doble incluido!"
        linea = f"{p['pts']} PTS · {p.get('valoracion')} VAL" if eu and p.get('valoracion') is not None else f"{p['pts']} PTS · {p['reb']} REB · {p['ast']} AST"
        ck = (clave(P) if '{' in P else P.split()[-1]) if P in t else clave(S(W))
        seg.append({'id': f'p{i}', 'partido': x['g']['partido'], 't': t, 'tarjetas': [{'clave': ck, 'pid': p['pid'], 'linea': linea}]})
    prox = b.get('esta_noche') or []
    def nom(c):
        a_ = _art(c); q = '{%s|%s}' % (c, PRON[c]) if c in PRON and PRON[c] != c else c
        return (a_ + ' ' if a_ else '') + q
    cuando = 'Esta noche' if lg == 'nba' else 'Próximamente'
    if lg != 'nba' and b.get('proximo_dia'):
        d0 = datetime.date.fromisoformat(b['fecha']); d1 = datetime.date.fromisoformat(b['proximo_dia'])
        dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        cuando = 'Mañana' if (d1 - d0).days == 1 else (f"El {dias[d1.weekday()]}" if 1 < (d1 - d0).days < 7 else f"El {d1.day} de {['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][d1.month - 1]}")
    if prox:
        dos = prox[:1] if nivel >= 1 else prox[:2]
        ps = [f"{nom(x.get('visitante_corto') or x['visitante'])} contra {nom(x.get('local_corto') or x['local'])}" for x in dos]
        preg = rnd.choice(["¿Quién dará la sorpresa? ", "¿Quién se lo lleva? Déjalo en comentarios. ", "¿Tu pronóstico? Te leemos en comentarios. ", "¿Quién gana? Mójate en comentarios. "])
        out = f"{cuando}, {' y '.join(ps)}. " + ("" if nivel >= 4 else preg) + "Esto es {OFFCOURT|Ófkort}."
        res = {x['partido']: clave(nom(x.get('visitante_corto') or x['visitante'])) for x in dos}
    else:
        out, res = rnd.choice([f"Muy pronto, más baloncesto en la {SIGLA[lg]}. ¡No te lo pierdas! ", f"¿Quién ha sido el mejor de la jornada? Te leemos en comentarios. ", f"La {SIGLA[lg]} vuelve pronto. ¿Tu MVP de la jornada? "]) + "Esto es {OFFCOURT|Ófkort}.", {}
    seg.append({'id': 'outro', 't': out, 'resaltar': res, 'velocidad': '+8%', 'tono': '+0Hz'})
    n = {'fecha': b['fecha'], 'auto': True, 'segmentos': seg}
    json.dump(n, open(os.path.join(R, 'salida', lg, 'noche.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


def duracion(out):
    m = re.search(r'total ([\d.]+) s', out); return float(m.group(1)) if m else 0


# ---------------------------------------------------------------- una liga de principio a fin
def video(lg):
    sh('--liga', lg, 'borrador')
    for nivel in range(5):
        n = guion(lg, nivel)
        sh('--liga', lg, 'voz')
        d = duracion(sh('--liga', lg, 'montar'))
        print(lg, 'nivel', nivel, 'duración', d)
        if d <= 61: break
    sh('--liga', lg, 'render')
    out = os.path.join(R, 'salida', lg)
    prueba = bool(os.environ.get('OFFCOURT_HASTA'))
    mp4 = [f for f in os.listdir(out) if f.endswith('.mp4') and n['fecha'] in f and (('prueba' in f) == prueba)][0]
    texto = ' '.join(re.sub(r'\{([^|}]*)\|[^}]*\}', r'\1', s['t']) for s in n['segmentos'])
    return os.path.join(out, mp4), n['fecha'], texto


def main():
    reg = json.load(open(REG)) if os.path.exists(REG) else {}
    hechos = []
    for lg in (sys.argv[1:] or ['nba', 'el', 'acb']):
        try:
            st = json.loads(sh('--liga', lg, 'estado').strip().splitlines()[-1])
        except Exception as e:
            print(lg, 'estado: error', e); continue
        fecha = st.get('noche'); print(lg, st.get('estado'), fecha)
        if st.get('estado') != 'LISTO' or ((reg.get(lg) or {}).get('fecha') == fecha and not os.environ.get('OFFCOURT_FORZAR')): continue
        try:
            mp4, f, texto = video(lg)
        except Exception as e:
            print(lg, 'ERROR', e); reg.setdefault('errores', {})[lg] = {'fecha': fecha, 'error': str(e)[-400:], 'hora': datetime.datetime.utcnow().isoformat()}
            continue
        if os.environ.get('OFFCOURT_PRUEBA'): hechos.append(mp4); continue   # prueba: no se apunta ni se entrega
        reg[lg] = {'fecha': f, 'archivo': os.path.basename(mp4), 'texto': texto, 'hecho': datetime.datetime.utcnow().isoformat() + 'Z', 'entregado': False}
        (reg.get('errores') or {}).pop(lg, None); hechos.append(mp4)
    json.dump(reg, open(REG, 'w'), ensure_ascii=False, indent=1)
    open(os.path.join(R, 'salida', 'nuevos.txt'), 'w').write(''.join(h + '\n' for h in hechos))
    print('vídeos nuevos:', hechos)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'guion':
        sh('--liga', sys.argv[2], 'borrador'); print(json.dumps(guion(sys.argv[2]), ensure_ascii=False, indent=1))
    else:
        main()
