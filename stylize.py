# Offcourt · "mismo patrón" para las fotos de jugadores:
# se quita el fondo (BiRefNet, licencia MIT), se coloca sobre un fondo con los colores del equipo,
# mismo encuadre (cabeza y hombros), mismo retoque y el dorsal detrás.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import facecrop
MODEL = os.environ.get('OFFCOURT_BIREFNET', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz', 'birefnet.onnx'))
FONT = os.environ.get('OFFCOURT_FONT', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
_sess = None

def _mask(im):
    global _sess
    import onnxruntime as ort
    if _sess is None:
        so = ort.SessionOptions(); so.log_severity_level = 3
        _sess = ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider'])
    x = np.array(im.convert('RGB').resize((1024, 1024), Image.BILINEAR), np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    o = _sess.run(None, {_sess.get_inputs()[0].name: x})[-1][0, 0].astype(np.float32)
    if o.min() < 0 or o.max() > 1: o = 1 / (1 + np.exp(-o))
    return np.array(Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR))

def _main_person(m, cx, cy):
    """Deja solo la silueta que contiene la cara (quita brazos y personas de al lado)."""
    import cv2
    b = (m > 110).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(b, 8)
    if n <= 2: return m
    k = lab[min(max(int(cy), 0), m.shape[0] - 1), min(max(int(cx), 0), m.shape[1] - 1)]
    if k == 0: k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    keep = cv2.dilate((lab == k).astype(np.uint8), np.ones((9, 9), np.uint8))
    return (m * keep).astype(np.uint8)

def _hex(h): return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)

def card(src, color, alt, number='', W=300, H=219):
    """src: foto original (PIL). Devuelve el cromo W x H con el patrón Offcourt."""
    src = src.convert('RGB')
    # 1) recorte amplio alrededor de la cara (cabeza + torso), para que la silueta llegue hasta abajo
    w0, h0 = src.size; sc0 = min(1, 640 / max(w0, h0))
    fs = facecrop._faces(np.array(src.resize((max(1, int(w0 * sc0)), max(1, int(h0 * sc0))))))
    if fs:
        f = max(fs, key=lambda f: f[2] * f[3]); fx, fy, fw, fh = (v / sc0 for v in f[:4])
    else:
        fh = fw = min(w0, h0) * 0.22; fx = w0 / 2 - fw / 2; fy = h0 * 0.12
    side = fh * 6.0; cx0 = fx + fw / 2; top0 = fy - fh * 1.2
    box = (int(cx0 - side / 2), int(top0), int(cx0 + side / 2), int(top0 + side))
    big = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), (0, 0, 0)); big.paste(src.crop((max(0, box[0]), max(0, box[1]), min(w0, box[2]), min(h0, box[3]))), (max(0, -box[0]), max(0, -box[1])))
    valid = Image.new('L', big.size, 0); valid.paste(255, (max(0, -box[0]), max(0, -box[1]), max(0, -box[0]) + min(w0, box[2]) - max(0, box[0]), max(0, -box[1]) + min(h0, box[3]) - max(0, box[1])))
    k = 900 / big.width; big = big.resize((900, 900), Image.LANCZOS); valid = valid.resize((900, 900))
    fx, fy, fw, fh = (fx - box[0]) * k, (fy - box[1]) * k, fw * k, fh * k
    bottom = max(0, min(899, int(((min(h0, box[3]) - box[1]) * k)) - 1))      # última fila con imagen real
    m = _mask(big); m = (m * (np.array(valid) / 255)).astype(np.uint8); m = _main_person(m, fx + fw / 2, fy + fh / 2)
    m = np.array(Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.0)))
    # 2) retoque igual para todos: balance de blancos + contraste
    a = np.array(big, np.float32); a = a * (a.mean() / np.maximum(a.reshape(-1, 3).mean(0), 1e-3))
    a = np.clip((a - 128) * 1.08 + 134, 0, 255).astype(np.uint8)
    # 3) encuadre: la cara ocupa ~38 % de la altura del cromo y queda en el 40 % superior
    scale = (H * 0.38) / fh
    pw, ph = int(900 * scale), int(900 * scale)
    ox = int(W / 2 - (fx + fw / 2) * scale); oy = int(H * 0.40 - (fy + fh / 2) * scale)
    # si la foto original se acaba antes del borde inferior del cromo, se amplía para que el cuerpo llegue abajo
    if oy + bottom * scale < H:
        cyf = fy + fh / 2; need = (H - H * 0.40) / max(1, bottom - cyf); scale = max(scale, need)
        pw, ph = int(900 * scale), int(900 * scale); ox = int(W / 2 - (fx + fw / 2) * scale); oy = int(H * 0.40 - cyf * scale)
    person = Image.fromarray(a).resize((pw, ph), Image.LANCZOS)
    pm = Image.fromarray(m).resize((pw, ph), Image.LANCZOS)
    # 4) fondo del equipo: degradado + rayas + dorsal
    c1 = _hex(color)
    if c1.sum() < 60: c1 = np.array([42, 47, 58], np.float32)
    c2 = tuple(int(v) for v in _hex(alt))
    yy, xx = np.mgrid[0:H, 0:W]; t = np.clip((xx * 0.6 + yy) / (W * 0.6 + H), 0, 1)[..., None]
    bg = Image.fromarray((c1 * (1 - t) + c1 * 0.32 * t).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(bg)
    for k in range(-H, W, 22): d.line([(k, H), (k + H * 0.45, 0)], fill=tuple(min(255, int(v * 1.22)) for v in c1) + (255,), width=3)
    if number:
        try: fnt = ImageFont.truetype(FONT, int(H * 0.62))
        except Exception: fnt = ImageFont.load_default()
        d.text((W - 10, -int(H * 0.06)), str(number), font=fnt, fill=tuple(min(255, int(v * 1.45)) for v in c1) + (255,), anchor='ra')
    # 5) sombra + borde del 2.º color + jugador
    sh = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); sh.putalpha(pm.point(lambda v: int(v * 0.5)))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (ox + 8, oy + 6))
    rim = Image.new('RGBA', (pw, ph), c2 + (0,)); rim.putalpha(pm.filter(ImageFilter.MaxFilter(5)).point(lambda v: int(v * 0.9)))
    bg.alpha_composite(rim, (ox, oy))
    person.putalpha(pm); bg.alpha_composite(person, (ox, oy))
    return bg.convert('RGB')
