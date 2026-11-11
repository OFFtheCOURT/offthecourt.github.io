# Offcourt · voz en off natural con Kokoro (modelo libre, licencia Apache 2.0)
# - Texto en español; lo marcado entre ⟦ ⟧ se pronuncia con fonética inglesa (nombres de la NBA).
# - Devuelve la duración y el momento aproximado de cada palabra (para los subtítulos).
import os, re, wave
import numpy as np
from kokoro_onnx import Kokoro
D = os.environ.get('OFFCOURT_KOKORO', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz', 'kokoro'))
VOICE = os.environ.get('OFFCOURT_VOICE_NAME', 'em_alex')
_K = None
def _k():
    global _K
    if _K is None:
        vp = os.path.join(D, 'voices.bin')
        if not os.path.exists(vp):
            vs = {v[:-4]: np.fromfile(os.path.join(D, v), dtype=np.float32).reshape(-1, 1, 256) for v in os.listdir(D) if v.endswith('.bin') and v != 'voices.bin'}
            np.savez(os.path.join(D, 'voices.npz'), **vs); os.replace(os.path.join(D, 'voices.npz'), vp)
        _K = Kokoro(os.path.join(D, 'model.onnx'), vp)
    return _K

def _tokens(text):
    out = []
    for m in re.finditer(r'⟦([^⟧]*)⟧([^\s⟦]*)|(\S+)', text):
        if m.group(1) is not None:
            ws = m.group(1).split()
            for q, w in enumerate(ws): out.append((w + (m.group(2) if q == len(ws) - 1 else ''), True))
        else: out.append((m.group(3), False))
    return out
def _es(w):  # nombres balcánicos: Dončić -> Dónchich
    w = re.sub(r'[ćč]', 'ch', w); w = re.sub(r'ic\b', 'ich', w); return w.replace('š', 'sh').replace('ž', 'y')

def synth(text, path, speed=1.12):
    """Sintetiza frase a frase (cortando en la puntuación): así se sabe exactamente cuándo empieza cada una."""
    k = _k(); tz = k.tokenizer
    toks = _tokens(text); phs = []
    for w, en in toks:
        core = re.sub(r'^[¡¿"(]+|[.,:;!?")]+$', '', w); lead = re.findall(r'^[¡¿]+', w); tail = re.findall(r'[.,:;!?]+$', w)
        p = tz.phonemize(core, 'en-us') if en else tz.phonemize(_es(core) if re.search(r'ic$|[ćčšž]', core) else core, 'es')
        phs.append((lead[0] if lead else '') + p.strip().rstrip('.,;:!?') + (tail[0] if tail else ''))
    segs = [[]]
    for q, (w, _) in enumerate(toks):
        segs[-1].append(q)
        if re.search(r'[.,:;!?]$', w) and q < len(toks) - 1: segs.append([])
    parts = []; words = []; t = 0.0; sr = 24000
    for sg in segs:
        ph = ' '.join(phs[q] for q in sg)
        a, sr = k.create(ph, voice=VOICE, speed=speed, lang='es', is_phonemes=True, trim=True)
        hop = int(sr * 0.01); rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, max(1, len(a) - hop), hop)])
        on = np.where(rms > max(0.01, rms.max() * 0.05))[0]
        a0, a1 = (on[0] * hop, min(len(a), (on[-1] + 2) * hop)) if len(on) else (0, len(a))
        a = a[a0:a1]; d = len(a) / sr
        wts = [max(1, len(re.sub(r'[ˈˌː¡¿.,:;!?]', '', phs[q]))) for q in sg]; tot = sum(wts); x = t
        for q, wt in zip(sg, wts):
            e = x + d * wt / tot; words.append({'w': re.sub(r'[⟦⟧]', '', toks[q][0]), 's': round(x, 3), 'e': round(e, 3)}); x = e
        last = toks[sg[-1]][0]
        gap = 0.28 if re.search(r'[.!?]$', last) else (0.14 if re.search(r'[,:;]$', last) else 0.05)
        parts += [a, np.zeros(int(sr * gap), np.float32)]; t += d + gap
    audio = np.concatenate(parts[:-1]) if parts else np.zeros(1, np.float32)
    audio = audio / max(1e-6, float(np.max(np.abs(audio)))) * 0.95
    with wave.open(path, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    return len(audio) / sr, words, sr
