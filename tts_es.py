# Offcourt · voz en off en español con nombres en inglés pronunciados a la inglesa (Piper TTS)
# Marca entre ⟦ ⟧ lo que debe leerse con fonética inglesa.
import os, re, wave
import numpy as np
# ================= voz (Piper) con fonética inglesa para nombres =================
from piper import PiperVoice
from piper.phonemize_espeak import EspeakPhonemizer
V = PiperVoice.load(os.environ.get('OFFCOURT_VOICE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz', 'es_ES-davefx-align.onnx'))); EPH = EspeakPhonemizer(V.espeak_data_dir); PMAP = V.config.phoneme_id_map
EN2ES = {'ɚ': ['e', 'ɾ'], 'ɝ': ['e', 'ɾ'], 'ɹ': ['ɾ'], 'æ': ['a'], 'ɪ': ['i'], 'ʊ': ['u'], 'ə': ['e'], 'ɐ': ['a'], 'ɑ': ['a'], 'ɔ': ['o'], 'ɒ': ['o'],
         'ʌ': ['a'], 'ɜ': ['e'], 'ᵻ': ['i'], 'ː': [], 'ʲ': [], 'θ': ['t'], 'ð': ['d'], 'z': ['s'], 'v': ['b'], 'h': ['x'], 'ʒ': ['ʝ'], 'ɫ': ['l'], 'ʔ': [], 'ɾ': ['ɾ']}
def en_phon(word):
    raw = sum(EPH.phonemize('en-us', word), [])
    out = []; k = 0
    while k < len(raw):
        a = raw[k]; b = raw[k + 1] if k + 1 < len(raw) else ''
        if a == 'e' and b == 'ɪ': out.append('eɪ'); k += 2; continue
        if a in 'aoɔ' and b in ('ɪ', 'ʊ'): out += ['o' if a in 'oɔ' else 'a', 'i' if b == 'ɪ' else 'u']; k += 2; continue
        if a == 'd' and b == 'ʒ': out.append('ʝ'); k += 2; continue
        out += EN2ES.get(a, [a]); k += 1
    return [p for p in out if p in PMAP]
def es_spell(word):
    w = word
    w = re.sub(r'[ćč]', 'ch', w); w = re.sub(r'ic\b', 'ich', w); w = w.replace('š', 'sh').replace('ž', 'y').replace('đ', 'd')
    if re.match(r'^J[aeiou]', w) and w.endswith('ch'): w = 'Y' + w[1:]
    return w
def es_phon(word): return [p for p in sum(V.phonemize(word), []) if p in PMAP]
def tokens(text):
    out = []
    for m_ in re.finditer(r'⟦([^⟧]*)⟧([^\s⟦]*)|(\S+)', text):
        if m_.group(1) is not None:
            ws = m_.group(1).split()
            for q, w in enumerate(ws):
                out.append((w + (m_.group(2) if q == len(ws) - 1 else ''), True))
        else: out.append((m_.group(3), False))
    return out
def synth(text, path, speed=0.83):
    toks = tokens(text); phon = []; spans = []
    for q, (w, en) in enumerate(toks):
        core = re.sub(r'[^\wÀ-ÿ\-ćčšžđ]', '', w); punct = re.findall(r'[.,:;!?¡¿]+$', w)
        ph = (en_phon(core) if en else es_phon(es_spell(core) if (re.search(r'ic$', core) or any(ord(c) > 127 and c not in 'áéíóúñü' for c in core)) else core)) if core else []
        if punct: ph += [c for c in punct[0] if c in PMAP and c not in '¡¿']
        if q: phon.append(' ')
        spans.append((w, len(phon), len(phon) + len(ph))); phon += ph
    ids = V.phonemes_to_ids(phon)
    from piper.config import SynthesisConfig
    audio, align = V.phoneme_ids_to_audio(ids, SynthesisConfig(length_scale=speed, noise_scale=0.6, noise_w_scale=0.7), include_alignments=True)
    audio = np.clip(audio / max(1e-6, np.max(np.abs(audio))) * 0.95, -1, 1)
    sr = V.config.sample_rate
    cum = np.concatenate([[0], np.cumsum(align)]) / sr
    pidx = lambda k: 2 + 2 * k                      # BOS, PAD, (fonema, PAD)...
    words = [{'w': re.sub(r'[⟦⟧]', '', w), 's': float(cum[min(pidx(a), len(cum) - 1)]), 'e': float(cum[min(pidx(b), len(cum) - 1)])} for w, a, b in spans]
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, 'wb') as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())
    return len(audio) / sr, words, sr
