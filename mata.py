"""
Navratri Day 6 - Maa Katyayani | Realistic Divine Ember Assembly
-----------------------------------------------------------------
Same idea as your original code, but with a cinematic, realistic look:

  * Real physics: embers drift on a swirling wind, then are pulled in by a
    spring + damper (inertia, slight overshoot, settling) - not a straight lerp
  * Warm gold / orange ember colours; real image colours appear only as each
    ember lands on its spot
  * Assembly sweeps from the centre outwards, like light spreading
  * Depth of field: big soft out-of-focus bokeh embers floating in front
  * Volumetric god-rays, drifting smoke, divine light flash during the reveal
  * Flickering diya light, handheld camera shake, slow push-in
  * Vignette + film grain, no cyber HUD

Keys:  ESC = quit    SPACE = skip to the end
"""

import math
import os
import time

import cv2
import numpy as np

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
IMG_PATH = "katyayani.png"
W, H = 1280, 720
CX, CY = W // 2, H // 2
TOTAL = 400            # frames (last ~100 are a calm hold on the finished image)
TRIGGER = 45           # frame when the pull towards the image begins
N_EDGE, N_FILL = 6000, 8000
N_AMBIENT = 650        # soft bokeh embers that keep floating in front
FPS = 30
SAVE_VIDEO = False     # True -> saves katyayani_day6_real.mp4
DIYAS = [(250, 618), (1030, 618)]     # flame positions (for the flicker light)
TITLE = "|| Durga Mata ki Jai! ||"

FONT = cv2.FONT_HERSHEY_DUPLEX
WINDOW = "Navratri Day 6 - Maa Katyayani | Divine Embers"


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------
# Image targets
# ----------------------------------------------------------------------------
def load_image():
    img = cv2.imread(IMG_PATH)
    if img is None and os.path.exists("make_durga.py"):
        print(f"'{IMG_PATH}' not found - generating it with make_durga.py ...")
        import make_durga
        make_durga.main()
        img = cv2.imread(IMG_PATH)
    if img is None:
        raise SystemExit(f"Couldn't find '{IMG_PATH}'. Put it next to this script "
                         f"(or run make_durga.py first).")
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)


def build_targets(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 120)
    ey, ex = np.nonzero(edges)
    pick = np.random.permutation(len(ex))[:N_EDGE]
    ex, ey = ex[pick], ey[pick]
    fy, fx = np.nonzero(img.max(axis=2) > 45)
    pick = np.random.permutation(len(fx))[:N_FILL]
    fx, fy = fx[pick], fy[pick]
    xs, ys = np.concatenate([ex, fx]), np.concatenate([ey, fy])
    col = np.clip(img[ys, xs].astype(np.float32) * 1.25 + 15, 0, 255)
    return xs.astype(np.float32), ys.astype(np.float32), col


# ----------------------------------------------------------------------------
# Wind field (shared by all embers)
# ----------------------------------------------------------------------------
def wind(x, y, t, phase):
    wx = np.sin(y * 0.011 + t * 0.021 + phase) * 0.10 + np.cos(x * 0.007 - t * 0.013) * 0.05
    wy = np.cos(x * 0.012 + t * 0.017 + phase * 0.5) * 0.07 - 0.02      # slight buoyancy
    return np.stack([wx, wy], 1).astype(np.float32) * 0.8


# ----------------------------------------------------------------------------
# Embers that form the image (spring-damper physics)
# ----------------------------------------------------------------------------
class Embers:
    def __init__(self, tx, ty, true_col):
        n = len(tx)
        self.n = n
        self.target = np.stack([tx, ty], 1)
        self.true_col = true_col
        self.pos = np.stack([np.random.uniform(-100, W + 100, n),
                             H * np.random.beta(2.2, 1.2, n) + np.random.uniform(0, 150, n)], 1).astype(np.float32)
        self.vel = np.zeros((n, 2), np.float32)
        self.phase = np.random.uniform(0, 2 * np.pi, n).astype(np.float32)

        self.k = np.random.uniform(0.012, 0.022, n).astype(np.float32)           # spring stiffness
        zeta = np.random.uniform(0.55, 0.8, n)                                    # damping ratio (<1 = slight overshoot)
        self.c = (2 * zeta * np.sqrt(self.k)).astype(np.float32)
        dist_c = np.hypot(tx - CX, (ty - CY) * 1.3)
        self.delay = dist_c / (W / 2) * 55 + np.random.uniform(0, 25, n)         # centre-out sweep

        temp = np.random.rand(n, 1).astype(np.float32)                           # ember colour temperature
        self.ember = np.array((20, 80, 255), np.float32) * (1 - temp) + np.array((120, 215, 255), np.float32) * temp
        self.big = np.random.rand(n) < 0.12                                       # a few brighter, larger sparks

    def update(self, frame):
        w = wind(self.pos[:, 0], self.pos[:, 1], frame, self.phase)
        off = self.target - self.pos
        active = (frame - TRIGGER) >= self.delay

        free = self.vel * 0.985 + w
        near = np.clip(np.linalg.norm(off, axis=1) / 200.0, 0, 1)[:, None]
        pull = self.vel + off * self.k[:, None] - self.vel * self.c[:, None] + w * 0.3 * near

        self.vel = np.clip(np.where(active[:, None], pull, free), -25, 25)
        self.pos = self.pos + self.vel

    def colors(self, frame):
        dist = np.linalg.norm(self.target - self.pos, axis=1)
        m = (np.clip(1 - dist / 140.0, 0, 1) ** 1.2)[:, None]       # true colour appears as it lands
        flick = (0.8 + 0.2 * np.sin(frame * 0.35 + self.phase * 3))[:, None]
        appear = float(smoothstep(0, 40, frame))
        return (self.ember * (1 - m) + self.true_col * m) * flick * appear


# ----------------------------------------------------------------------------
# Out-of-focus bokeh embers floating in front of the camera
# ----------------------------------------------------------------------------
class Ambient:
    def __init__(self):
        n = N_AMBIENT
        self.pos = np.stack([np.random.uniform(0, W, n), np.random.uniform(0, H, n)], 1).astype(np.float32)
        self.vel = np.zeros((n, 2), np.float32)
        self.phase = np.random.uniform(0, 2 * np.pi, n).astype(np.float32)
        self.cls = np.arange(n) % 3                                             # three bokeh sizes
        self.col = (np.array((30, 110, 255), np.float32) * np.random.uniform(0.6, 1.0, (n, 1))
                    + np.array((60, 80, 0), np.float32) * np.random.rand(n, 1))

    def update(self, frame):
        w = wind(self.pos[:, 0], self.pos[:, 1], frame, self.phase) * 1.4
        self.vel = self.vel * 0.97 + w
        self.vel[:, 1] -= 0.03
        self.pos += self.vel * (1 + self.cls[:, None] * 0.35)
        self.pos[:, 0] %= W
        low = self.pos[:, 1] < -30
        self.pos[low, 1] = H + 30

    def render(self, frame):
        hw, hh = W // 4, H // 4
        out = np.zeros((hh, hw, 3), np.uint8)
        flick = 0.4 + 0.25 * np.sin(frame * 0.12 + self.phase * 2)
        for cls, r in enumerate((1, 2, 3)):
            m = self.cls == cls
            xi = (self.pos[m, 0] / 4).astype(np.int32)
            yi = (self.pos[m, 1] / 4).astype(np.int32)
            ok = (xi >= 0) & (xi < hw) & (yi >= 0) & (yi < hh)
            layer = np.zeros_like(out)
            layer[yi[ok], xi[ok]] = np.clip(self.col[m][ok] * flick[m][ok][:, None], 0, 255).astype(np.uint8)
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
            layer = cv2.GaussianBlur(cv2.dilate(layer, k), (0, 0), r / 2.0 + 0.5)
            out = cv2.add(out, layer)
        return cv2.resize(out, (W, H), interpolation=cv2.INTER_LINEAR)


# ----------------------------------------------------------------------------
# Atmosphere helpers
# ----------------------------------------------------------------------------
def make_background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - CX, (yy - 330) * 1.1) / 520.0
    glow = np.exp(-d * d * 2.0)[..., None]
    bg = np.array([10, 6, 14], np.float32) * (1 - glow) + np.array([22, 42, 88], np.float32) * glow
    return np.clip(bg, 0, 255).astype(np.uint8)


def make_smoke():
    rng = np.random.default_rng(11)
    a = cv2.resize(rng.random((5, 20)).astype(np.float32), (W, H // 2), interpolation=cv2.INTER_CUBIC)
    b = cv2.resize(rng.random((8, 30)).astype(np.float32), (W, H // 2), interpolation=cv2.INTER_CUBIC)
    return np.clip(a, 0, 1) ** 2, np.clip(b, 0, 1) ** 2


def smoke_layer(smoke, frame):
    a, b = smoke
    oa, ob = int(frame * 0.3) % (W // 2), int(frame * 0.65) % (W // 2)
    s = np.roll(a, -oa, 1)[:, : W // 2] * 0.6 + np.roll(b, -ob, 1)[:, : W // 2] * 0.4
    small = (s[..., None] * np.array([26, 36, 60], np.float32)).astype(np.uint8)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


def make_rays():
    acc = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(5)
    ox, oy = CX, 250
    for _ in range(38):
        a = rng.uniform(-math.pi, math.pi)
        wdt = rng.uniform(0.015, 0.06)
        tmp = np.zeros((H, W), np.uint8)
        pts = np.array([(ox, oy), (ox + 1800 * math.cos(a - wdt), oy + 1800 * math.sin(a - wdt)),
                        (ox + 1800 * math.cos(a + wdt), oy + 1800 * math.sin(a + wdt))], np.int32)
        cv2.fillPoly(tmp, [pts], int(rng.uniform(70, 255)), cv2.LINE_AA)
        acc += tmp
    acc = cv2.GaussianBlur(acc, (0, 0), 6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    acc *= np.exp(-np.hypot(xx - ox, yy - oy) / 800.0)
    acc = np.clip(acc / 255.0, 0, 1)[..., None]
    return (acc * np.array([55, 135, 255], np.float32)).astype(np.uint8)


def gaussian_sprite(radius, color):
    y, x = np.mgrid[-radius:radius + 1, -radius:radius + 1].astype(np.float32)
    g = np.exp(-(x * x + y * y) / (2 * (radius / 2.6) ** 2))
    return (g[..., None] * np.array(color, np.float32)).astype(np.uint8)


def add_sprite(dst, spr, cx, cy, gain):
    h, w = spr.shape[:2]
    x0, y0 = int(cx) - w // 2, int(cy) - h // 2
    dx0, dy0, dx1, dy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    s = spr[dy0 - y0: dy1 - y0, dx0 - x0: dx1 - x0]
    dst[dy0:dy1, dx0:dx1] = cv2.add(dst[dy0:dy1, dx0:dx1], cv2.convertScaleAbs(s, alpha=gain))


def bloom(img):
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b1 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2.0), (W, H))
    b2 = cv2.resize(cv2.GaussianBlur(small, (0, 0), 7), (W, H))
    return cv2.add(cv2.addWeighted(img, 1.0, b1, 0.7, 0), cv2.convertScaleAbs(b2, alpha=0.6))


def make_title():
    layer = np.zeros((H, W, 3), np.uint8)
    (tw, th), _ = cv2.getTextSize(TITLE, FONT, 1.1, 2)
    org = ((W - tw) // 2, 62)
    cv2.putText(layer, TITLE, org, FONT, 1.1, (120, 215, 255), 2, cv2.LINE_AA)
    glow = cv2.GaussianBlur(layer, (0, 0), 9)
    crisp = np.zeros_like(layer)
    cv2.putText(crisp, TITLE, org, FONT, 1.1, (235, 250, 255), 2, cv2.LINE_AA)
    return glow, crisp


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    img = load_image()
    tx, ty, true_col = build_targets(img)
    embers = Embers(tx, ty, true_col)
    ambient = Ambient()

    bg = make_background()
    smoke = make_smoke()
    rays = make_rays()
    flame = gaussian_sprite(140, (40, 150, 255))
    flash_sprite = gaussian_sprite(460, (70, 175, 255))
    title_glow, title_crisp = make_title()

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1.0 - 0.6 * np.clip(np.hypot((xx - CX) / CX, (yy - CY) / CY) - 0.5, 0, 1)
    vig8 = cv2.merge([(v * 255).astype(np.uint8)] * 3)
    rng = np.random.default_rng(1)
    grain_pos, grain_neg = [], []
    for _ in range(6):
        g = rng.normal(0, 4.0, (H, W)).astype(np.int16)
        grain_pos.append(cv2.merge([np.clip(g, 0, 255).astype(np.uint8)] * 3))
        grain_neg.append(cv2.merge([np.clip(-g, 0, 255).astype(np.uint8)] * 3))

    trail = np.zeros((H, W, 3), np.uint8)
    decay_lut = np.array([max(0, int(v * 0.72) - 2) for v in range(256)], np.uint8)   # fast trail fade
    rays_half = cv2.resize(rays, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    cv2.namedWindow(WINDOW, cv2.WINDOW_AUTOSIZE)

    writer = None
    if SAVE_VIDEO:
        writer = cv2.VideoWriter("katyayani_day6_real.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

    print("Playing Divine Ember Assembly...  ESC = quit | SPACE = skip")
    frame_ms = 1000.0 / FPS

    for frame in range(TOTAL):
        t0 = time.perf_counter()

        # ---- physics ----
        embers.update(frame)
        ambient.update(frame)
        col = embers.colors(frame)

        # ---- draw embers with motion-blur trails ----
        trail = cv2.LUT(trail, decay_lut)
        px, py = embers.pos[:, 0].astype(np.int32), embers.pos[:, 1].astype(np.int32)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        c = np.clip(col, 0, 255).astype(np.uint8)
        trail[py[ok], px[ok]] = np.maximum(trail[py[ok], px[ok]], c[ok])
        bigm = ok & embers.big
        if bigm.any():
            big = np.zeros_like(trail)
            big[py[bigm], px[bigm]] = c[bigm]
            np.maximum(trail, cv2.dilate(big, np.ones((3, 3), np.uint8)), out=trail)

        # ---- reveal state ----
        e = float(smoothstep(150, 260, frame))
        flash = math.exp(-((frame - 215) / 16.0) ** 2)

        # ---- compose ----
        out = cv2.add(bg, smoke_layer(smoke, frame))
        ang = 6.0 * math.sin(frame * 0.01)
        rot = cv2.getRotationMatrix2D((CX / 2, 125), ang, 1.0)
        ray_gain = 0.10 + 0.30 * float(smoothstep(110, 230, frame))
        r_img = cv2.resize(cv2.warpAffine(rays_half, rot, (W // 2, H // 2)), (W, H), interpolation=cv2.INTER_LINEAR)
        out = cv2.add(out, cv2.convertScaleAbs(r_img, alpha=ray_gain))

        parts = cv2.convertScaleAbs(bloom(trail), alpha=1.0 - 0.55 * e)
        out = cv2.add(out, parts)
        out = cv2.add(out, ambient.render(frame))
        if e > 0:
            out = cv2.add(out, cv2.convertScaleAbs(img, alpha=0.95 * e ** 1.3))
        if flash > 0.01:
            add_sprite(out, flash_sprite, CX, 330, flash * 0.6)
        if e > 0.4:                                                           # diya flicker
            for i, (dx, dy) in enumerate(DIYAS):
                inten = 0.55 + 0.25 * math.sin(frame * 0.43 + i) + 0.2 * math.sin(frame * 0.91 + 2 * i) \
                        + np.random.uniform(-0.06, 0.06)
                add_sprite(out, flame, dx, dy, max(0.0, inten) * e * 0.8)

        # ---- title ----
        ta = float(smoothstep(260, 300, frame))
        if ta > 0:
            out = cv2.add(out, cv2.convertScaleAbs(title_glow, alpha=ta * 0.9))
            out = cv2.add(out, cv2.convertScaleAbs(title_crisp, alpha=ta))

        # ---- camera: slow push-in + handheld shake (both settle at the end) ----
        settle = 1.0 - float(smoothstep(230, 330, frame))
        zoom = 1.0 + 0.05 * (1.0 - float(smoothstep(0, 330, frame)))
        sx = settle * (2.5 * math.sin(frame * 0.11) + 1.2 * math.sin(frame * 0.27 + 1.0))
        sy = settle * (2.0 * math.sin(frame * 0.09 + 2.0) + 1.0 * math.sin(frame * 0.31))
        M = cv2.getRotationMatrix2D((CX, CY), 0, zoom)
        M[0, 2] += sx
        M[1, 2] += sy
        out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        # ---- vignette + film grain ----
        out = cv2.multiply(out, vig8, scale=1.0 / 255)
        out = cv2.subtract(cv2.add(out, grain_pos[frame % 6]), grain_neg[frame % 6])

        cv2.imshow(WINDOW, out)
        if writer:
            writer.write(out)

        wait = max(1, int(frame_ms - (time.perf_counter() - t0) * 1000))
        key = cv2.waitKey(wait) & 0xFF
        if key in (27, 32):
            break

    if writer:
        writer.release()
        print("Saved katyayani_day6_real.mp4")
    cv2.waitKey(1500)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()