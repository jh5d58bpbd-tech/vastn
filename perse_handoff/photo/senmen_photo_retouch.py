"""Swap floor + wallpaper in the site photo, keeping the photo's own light and shadows.

python3 photo_retouch.py <variant 1-4> <out.jpg> [--overlay]
"""
import sys
import cv2
import numpy as np

SRC = '/home/user/vastn/perse_handoff/refs/senmen/01_現況.jpg'
im8 = cv2.imread(SRC)
H, W = im8.shape[:2]
rng = np.random.default_rng(11)


def lin(x):
    x = x.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def to8(x):
    x = np.clip(x, 0, 1)
    return (np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255 + 0.5).astype(np.uint8)


def srgb(r, g, b):
    return lin(np.array([[[b, g, r]]], np.uint8))[0, 0]          # BGR linear


def poly(pts):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 255); return m


def noise(shape, cell, octaves=4, seed=0):
    r = np.random.default_rng(seed); out = np.zeros(shape, np.float32); a = 1.0; tot = 0
    for o in range(octaves):
        c = max(2, int(cell / 2 ** o))
        small = r.random((shape[0] // c + 2, shape[1] // c + 2)).astype(np.float32)
        out += a * cv2.resize(small, (shape[1] + c, shape[0] + c), interpolation=cv2.INTER_CUBIC)[:shape[0], :shape[1]]
        tot += a; a *= 0.5
    return out / tot


# ------------------------------------------------------------------ masks
floor = poly([(755, 1555), (1100, 1555), (1112, 1600), (1190, 1815), (1345, 1815), (1600, 2300), (1592, 2576),
              (455, 2576), (487, 2390), (495, 2330), (700, 1742)])
hsv = cv2.cvtColor(im8, cv2.COLOR_BGR2HSV)
hue = hsv[..., 0]
coloured = cv2.dilate(((hsv[..., 1] > 60) & (hsv[..., 2] > 40) & ((hue > 110) | (hue < 6))).astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
floor[coloured > 0] = 0                                                       # purple mat, pink scale
for p in ([(1078, 1930), (1352, 1905), (1606, 2545), (1606, 2576), (1148, 2576)],    # mat + papers on it
          [(1088, 1395), (1228, 1428), (1182, 1858), (1106, 1842)]):                 # leaning board
    floor[poly(p) > 0] = 0
floor = cv2.morphologyEx(floor, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))

wallish = ((hsv[..., 1] < 80) & (hsv[..., 2] > 80)).astype(np.uint8) * 255
left = poly([(150, 0), (382, 0), (592, 462), (700, 1722), (497, 2300)])
left[poly([(388, 903), (467, 903), (467, 1087), (388, 1087)]) > 0] = 0
right = poly([(1272, 345), (1330, 82), (1932, 0), (1932, 1385), (1385, 1385), (1345, 1812), (1200, 1798), (1230, 1000)])
right[poly([(1104, 600), (1182, 560), (1186, 1500), (1110, 1520)]) > 0] = 255        # strip between alcove and bath-door frame
for p in ([(1440, 395), (1932, 395), (1932, 1190), (1440, 1190)],
          [(1385, 1120), (1932, 1120), (1932, 1420), (1385, 1420)]):
    right[poly(p) > 0] = 0
back = poly([(735, 598), (1102, 598), (1102, 1520), (760, 1520), (752, 880), (735, 880)])
for p in ([(728, 618), (1112, 618), (1112, 1002), (728, 1002)], [(780, 1160), (1102, 1160), (1102, 1530), (780, 1530)],
          [(835, 985), (1102, 985), (1102, 1530), (835, 1530)]):
    back[poly(p) > 0] = 0
def clean(m):
    m = cv2.bitwise_and(m, wallish)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
left, right, back = clean(left), clean(right), clean(back)
for m in (left, right, back):
    m[coloured > 0] = 0

if '--overlay' in sys.argv:
    ov = im8.copy()
    for m, c in ((floor, (0, 0, 255)), (left, (0, 255, 0)), (back, (255, 0, 255)), (right, (255, 128, 0))):
        ov[m > 0] = (ov[m > 0] * 0.45 + np.array(c) * 0.55).astype(np.uint8)
    cv2.imwrite(sys.argv[2], cv2.resize(ov, (W // 2, H // 2))); sys.exit()

img = lin(im8)
L = (0.0722 * img[..., 0] + 0.7152 * img[..., 1] + 0.2126 * img[..., 2])


def mblur(x, m, s):
    mf = (m > 0).astype(np.float32)
    return cv2.GaussianBlur(x * mf, (0, 0), s) / np.maximum(cv2.GaussianBlur(mf, (0, 0), s), 1e-4)


# ------------------------------------------------------------------ perspective (homographies)
def homog(img_pts, world_pts, scale, origin):
    """world mm -> canvas px (scale px/mm, origin mm) -> image px"""
    cw = [((x - origin[0]) * scale, (y - origin[1]) * scale) for x, y in world_pts]
    return cv2.getPerspectiveTransform(np.float32(cw), np.float32(img_pts))

FS, FO, FW, FH = 0.5, (-1200, -300), 1800, 2150            # floor canvas: 2 mm / px
Hf = homog([(755, 1555), (1100, 1555), (495, 2330), (1377, 2330)], [(0, 0), (950, 0), (0, 1780), (950, 1780)], FS, FO)
fu = (np.arange(FW) / FS + FO[0])[None, :].repeat(FH, 0)   # world mm across
fv = (np.arange(FH) / FS + FO[1])[:, None].repeat(FW, 1)   # world mm depth (toward the camera)


def line_x(p, q, r, s):
    a1, b1 = q[1] - p[1], p[0] - q[0]; c1 = a1 * p[0] + b1 * p[1]
    a2, b2 = s[1] - r[1], r[0] - s[0]; c2 = a2 * r[0] + b2 * r[1]
    d = a1 * b2 - a2 * b1
    return ((c1 * b2 - c2 * b1) / d, (a1 * c2 - a2 * c1) / d)
near_top = line_x((382, 0), (592, 462), (150, 0), (497, 2300))
WS, WO, WW, WH = 0.5, (-200, -100), 1300, 1250              # left wall canvas: u along wall, v height
Hw = homog([(497, 2300), (700, 1722), (592, 462), near_top], [(0, 60), (2000, 60), (2000, 2300), (0, 2300)], WS, WO)
# image y grows downward while world height grows upward: flip handled by the point order above

# ------------------------------------------------------------------ textures (linear BGR)
def tex_tile(base, size=450):
    t = np.ones((FH, FW, 3), np.float32) * base
    tid = (np.floor(fu / size) * 7 + np.floor(fv / size) * 13) % 17 / 17.0
    mott = noise((FH, FW), 80, 5, 1) * 0.16 + noise((FH, FW), 12, 3, 2) * 0.06 + 0.89
    t *= (mott * (0.96 + 0.08 * tid))[..., None]
    gu = np.minimum(np.mod(fu, size), size - np.mod(fu, size)); gv = np.minimum(np.mod(fv, size), size - np.mod(fv, size))
    g = np.clip((np.minimum(gu, gv) - 1.0) / 2.0, 0, 1)
    return t * (0.55 + 0.45 * g)[..., None]


def tex_terrazzo(base):
    t = (np.ones((FH, FW, 3), np.float32) * base) * (0.97 + 0.06 * noise((FH, FW), 40, 3, 3))[..., None]
    cols = [srgb(170, 166, 160)] * 4 + [srgb(200, 192, 180)] * 4 + [srgb(110, 108, 104)] * 2 + [srgb(250, 248, 244)] * 2 + [srgb(176, 128, 104)]
    r = np.random.default_rng(5)
    for n, rmin, rmax in ((900, 2, 4), (5000, 0.8, 1.6)):
        for _ in range(n):
            x, y = r.integers(0, FW), r.integers(0, FH)
            a, b = r.uniform(rmin, rmax), r.uniform(rmin, rmax)
            pts = cv2.ellipse2Poly((int(x), int(y)), (int(a * 2), int(b * 2)), int(r.uniform(0, 180)), 0, 360, 40)
            jitter = pts.astype(np.int32)
            c = cols[r.integers(0, len(cols))] * r.uniform(0.85, 1.1)
            cv2.fillPoly(t, [jitter], tuple(float(v) for v in c), lineType=cv2.LINE_AA)
    return t


def tex_mortar(base):
    t = np.ones((FH, FW, 3), np.float32) * base
    k = 0.82 + 0.26 * noise((FH, FW), 300, 6, 4) + 0.08 * noise((FH, FW), 25, 3, 5)
    spots = np.clip((noise((FH, FW), 60, 4, 6) - 0.62) * 6, 0, 1)
    return t * (k * (1 - 0.12 * spots))[..., None]


def tex_oak(base, pw=150):
    t = np.zeros((FH, FW, 3), np.float32)
    row = np.floor(fu / pw)
    r = np.random.default_rng(9)
    offs = r.uniform(0, 1800, 400); tones = r.uniform(0.82, 1.15, 4000)
    rr = (row.astype(int) % 400)
    along = fv + offs[rr]
    pid = np.floor(along / 1200).astype(int)
    tone = tones[(rr * 31 + pid * 7) % 4000]
    grain = noise((FH, FW), 6, 3, 7)
    grain = cv2.resize(cv2.resize(grain, (FW // 6, FH)), (FW, FH))            # stretch along the plank (depth)
    k = tone * (0.86 + 0.22 * grain) * (0.94 + 0.08 * np.sin(fu * 0.35 + grain * 6))
    gap = np.minimum(np.minimum(np.mod(fu, pw), pw - np.mod(fu, pw)), np.minimum(np.mod(along, 1200), 1200 - np.mod(along, 1200)))
    k *= 0.6 + 0.4 * np.clip((gap - 0.5) / 1.5, 0, 1)
    return np.ones((FH, FW, 3), np.float32) * base * k[..., None]


def tex_wood_wall(base, bw=160):
    u = (np.arange(WW) / WS + WO[0])[None, :].repeat(WH, 0)
    v = (np.arange(WH) / WS + WO[1])[:, None].repeat(WW, 1)
    board = np.floor(u / bw); tone = 0.85 + 0.3 * ((board * 37) % 11) / 11
    grain = noise((WH, WW), 8, 3, 8)
    grain = cv2.resize(cv2.resize(grain, (WW, WH // 8)), (WW, WH))            # vertical grain
    k = tone * (0.85 + 0.25 * grain) * (0.95 + 0.07 * np.sin(u * 0.3 + grain * 7))
    seam = np.minimum(np.mod(u, bw), bw - np.mod(u, bw))
    k *= 0.7 + 0.3 * np.clip((seam - 0.5) / 1.5, 0, 1)
    return np.ones((WH, WW, 3), np.float32) * base * k[..., None]


def warp(t, Hm):
    return cv2.warpPerspective(t, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def plaster(base, seed, fine=False):
    k = 0.96 + 0.06 * noise((H, W), 220, 4, seed)
    if fine:                                                                    # 織物調: fine weave
        k *= 0.97 + 0.05 * noise((H, W), 3, 2, seed + 1)
    return np.ones((H, W, 3), np.float32) * base * k[..., None]


# ------------------------------------------------------------------ proposals
V = sys.argv[1]
if V == '1':
    ftex = warp(tex_tile(srgb(150, 147, 142)), Hf)
    wl = wr = wb = plaster(srgb(214, 207, 197), 21)
elif V == '2':
    ftex = warp(tex_terrazzo(srgb(232, 226, 216)), Hf)
    wr = wb = plaster(srgb(240, 236, 228), 22, fine=True)
    wl = plaster(srgb(150, 164, 146), 23, fine=True)
elif V == '3':
    ftex = warp(tex_mortar(srgb(140, 138, 134)), Hf)
    wr = wb = plaster(srgb(238, 236, 232), 24)
    wl = warp(tex_wood_wall(srgb(150, 114, 82)), Hw)
else:
    ftex = warp(tex_oak(srgb(190, 150, 108)), Hf)
    wr = wb = plaster(srgb(242, 236, 224), 25)
    wl = plaster(srgb(150, 166, 176), 26)

out = img.copy()
# floor: light from the photo (soft, masked blur so objects don't bleed in)
Sf = mblur(L, floor, 14) / 0.62
Sf = Sf * (1 + 0.25 * (mblur(L, floor, 3) / np.maximum(mblur(L, floor, 14), 1e-4) - 1))   # keep a little contact shadow
fm = cv2.GaussianBlur((floor > 0).astype(np.float32), (0, 0), 1.2)[..., None]
out = out * (1 - fm) + (ftex * Sf[..., None]) * fm
# walls: keep the photo's shading, drop most of the old emboss
for m, t in ((left, wl), (right, wr), (back, wb)):
    Sw = mblur(L, m, 5); Sw = (Sw + 0.25 * (L - Sw)) / 0.74
    a = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 1.2)[..., None]
    out = out * (1 - a) + (t * Sw[..., None]) * a
cv2.imwrite(sys.argv[2], to8(out), [cv2.IMWRITE_JPEG_QUALITY, 94])
