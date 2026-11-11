# Offcourt · recorte de fotos centrado en la cara (para cromos 200x146 y avatares redondos)
# 1) YuNet (detector de caras con IA de OpenCV), 2) Haar frontal/perfil, 3) estimación por la forma de la foto.
import os
import numpy as np
from PIL import Image
try:
    import cv2
except Exception:
    cv2 = None
YUNET = os.environ.get('OFFCOURT_YUNET', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz', 'yunet.onnx'))
_det = None

def _faces(rgb):
    """Devuelve [(x, y, w, h, score)] en píxeles de la imagen."""
    if cv2 is None: return []
    h, w = rgb.shape[:2]; out = []
    global _det
    if os.path.exists(YUNET) and hasattr(cv2, 'FaceDetectorYN'):
        if _det is None: _det = cv2.FaceDetectorYN.create(YUNET, '', (w, h), 0.6, 0.3, 50)
        _det.setInputSize((w, h))
        _, f = _det.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        if f is not None: out = [(float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[14])) for r in f]
    if not out:
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); g = cv2.equalizeHist(g)
        for name, flip in (('haarcascade_frontalface_default.xml', False), ('haarcascade_frontalface_alt2.xml', False), ('haarcascade_profileface.xml', False), ('haarcascade_profileface.xml', True)):
            c = cv2.CascadeClassifier(cv2.data.haarcascades + name); img = cv2.flip(g, 1) if flip else g
            for (x, y, fw, fh) in c.detectMultiScale(img, 1.06, 5, minSize=(int(w * .05), int(w * .05))):
                if flip: x = w - x - fw
                out.append((float(x), float(y), float(fw), float(fh), 0.5))
            if out: break
    # caras plausibles: no minúsculas y en la mitad superior de la foto
    return [f for f in out if f[3] > h * 0.04 and f[1] + f[3] / 2 < h * 0.75]

def crop(im, W=200, H=146):
    im = im.convert('RGB'); w, h = im.size
    s = 640 / max(w, h); small = im.resize((max(1, int(w * s)), max(1, int(h * s)))) if s < 1 else im; s = min(s, 1)
    fs = _faces(np.array(small))
    if fs:
        x, y, fw, fh, _ = max(fs, key=lambda f: f[2] * f[3] * (0.5 + f[4]))
        x, y, fw, fh = x / s, y / s, fw / s, fh / s
        ch = fh * 3.0; cw = ch * W / H
        cx, cy = x + fw / 2, y + fh / 2
        top = cy - ch * 0.40
    else:
        if h > w * 1.15:          # foto vertical (cuerpo entero): la cara suele estar arriba
            ch = h * 0.38; cw = ch * W / H; cx = w / 2; top = h * 0.02
        else:                     # foto horizontal: tercio superior centrado
            ch = h * 0.75; cw = ch * W / H; cx = w / 2; top = 0
    if cw > w: cw = w; ch = cw * H / W
    if ch > h: ch = h; cw = ch * W / H
    l = max(0, min(w - cw, cx - cw / 2)); t = max(0, min(h - ch, top))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((W, H), Image.LANCZOS), bool(fs)
