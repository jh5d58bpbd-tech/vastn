"""洗面脱衣所 クロス×床 の組み合わせ提案（現況写真 refs/senmen/01_現況.jpg から寸法を推定）.

VARIANT=1..4 で仕上げだけ切り替える（洗面台・洗濯機・浴室扉・配置は現況のまま）.
Units m. x = right (east) looking from the entrance, z = toward the entrance (south), y = up.
Back wall (washer alcove) z = 0, entrance z = D.
"""
import math
import os

import numpy as np


def srgb(r, g, b):
    f = lambda c: (c/255)/12.92 if c/255 <= 0.04045 else ((c/255+0.055)/1.055)**2.4
    return (f(r), f(g), f(b))


MATS, NAMES = [], {}
def mat(name, rgb, typ=0, tex=0, ks=0.0, ex=50, emit=(0, 0, 0), bump=0.0, axis=-1, lin=False):
    c = rgb if lin else srgb(*rgb)
    NAMES[name] = len(MATS)
    MATS.append((c, typ, tex, ks, ex, emit, bump, axis))

V = os.environ.get('VARIANT', '1')

# --- finishes per proposal ---------------------------------------------------------------
# tex 3 = 塗り壁調クロス, tex 8 = 織物調クロス, tex 4 = 木目, tex 1 = フローリング(オーク),
# tex 9 = モルタル/コンクリート, tex 12 = 大判タイル石目 (bump = tile size m), tex 13 = テラゾー
if V == '1':      # ホテルライク・グレージュ
    mat('floor', (150, 147, 142), tex=12, ks=0.04, ex=60, bump=0.45)
    mat('wall', (214, 207, 197), tex=3, bump=0.5)
    mat('accent', (146, 134, 122), tex=3, bump=0.5)
    mat('frame', (70, 48, 36), tex=4, ks=0.06, ex=80, axis=1)
    ACCENT = 'washer'
elif V == '2':    # テラゾー × くすみグリーン
    mat('floor', (232, 226, 216), tex=13, ks=0.05, ex=80)
    mat('wall', (240, 236, 228), tex=8)
    mat('accent', (150, 164, 146), tex=8)
    mat('frame', (236, 232, 224), ks=0.05, ex=80)
    ACCENT = 'washer'
elif V == '3':    # モルタル × 木目
    mat('floor', (140, 138, 134), tex=9, ks=0.03, ex=30)
    mat('wall', (238, 236, 232), tex=3, bump=0.6)
    mat('accent', (170, 124, 82), tex=4, ks=0.03, ex=40, axis=1)
    mat('frame', (70, 48, 36), tex=4, ks=0.06, ex=80, axis=1)
    ACCENT = 'washer'
else:             # ナチュラル木目
    mat('floor', (198, 152, 104), tex=1, ks=0.05, ex=120, axis=2)
    mat('wall', (242, 236, 224), tex=3, bump=0.5)
    mat('accent', (150, 166, 176), tex=3, bump=0.5)
    mat('frame', (192, 148, 102), tex=4, ks=0.05, ex=80, axis=1)
    ACCENT = 'washer'

mat('ceiling', (244, 243, 240), tex=3, bump=0.2)
mat('base', (90, 86, 80), ks=0.03, ex=40)
mat('white', (240, 239, 236), ks=0.08, ex=200)
mat('vanity', (238, 236, 232), ks=0.10, ex=300)
mat('ceramic', (246, 245, 242), ks=0.12, ex=900)
mat('chrome', (205, 205, 203), typ=4, ex=1500)
mat('mirror', (236, 236, 232), typ=1)
mat('glass_f', (226, 230, 230), ks=0.10, ex=300)     # 浴室折れ戸のパネル（すりガラス調）
mat('door_g', (214, 214, 210), ks=0.05, ex=100)
mat('washer', (230, 231, 232), ks=0.10, ex=300)
mat('washer_d', (60, 62, 66), ks=0.20, ex=600)
mat('pan', (226, 222, 214), ks=0.05, ex=80)
mat('oak', (186, 140, 92), tex=4, ks=0.05, ex=80, axis=0)
mat('towel1', (208, 202, 194), tex=8)
mat('towel2', (150, 156, 150), tex=8)
mat('basket', (170, 136, 92), tex=8)
mat('bottle', (226, 222, 214), ks=0.15, ex=400)
mat('bottle2', (120, 100, 80), ks=0.2, ex=400)
mat('leaf', (40, 80, 44), ks=0.1, ex=90)
mat('lamp', (255, 255, 255), emit=(9.0, 8.4, 7.4))
mat('grille', (200, 198, 192))

PRIMS, LIGHTS = [], []
GROUP = ['shell']
def setg(g): GROUP[0] = g
def flags(noshadow=False):
    return (1 if noshadow else 0) | (2 if GROUP[0] == 'shell' else 0)
def box(x1, y1, z1, x2, y2, z2, m, noshadow=False):
    x1, x2 = min(x1, x2), max(x1, x2); y1, y2 = min(y1, y2), max(y1, y2); z1, z2 = min(z1, z2), max(z1, z2)
    c = ((x1+x2)/2, (y1+y2)/2, (z1+z2)/2); h = ((x2-x1)/2, (y2-y1)/2, (z2-z1)/2)
    PRIMS.append((GROUP[0], 'box', c, h, np.eye(3), NAMES[m], flags(noshadow)))
def rr(c, h, m, r=0.03, noshadow=False):
    PRIMS.append((GROUP[0], 'rbx', tuple(c), tuple(h), np.eye(3), NAMES[m], flags(noshadow), r))
def cyl(p0, p1, r, m, noshadow=False):
    PRIMS.append((GROUP[0], 'cyl', tuple(p0), tuple(p1), r, NAMES[m], flags(noshadow)))
def ell(c, radii, R, m, noshadow=False):
    M = np.diag([1/radii[0], 1/radii[1], 1/radii[2]]) @ np.array(R).T
    PRIMS.append((GROUP[0], 'ell', tuple(c), M, max(radii), NAMES[m], flags(noshadow)))
NEUT = (1.0, 0.92, 0.82)
def light(p, I, d=(0, -1, 0), inner=30, outer=70, rad=0.08, up=0.0, col=NEUT):
    LIGHTS.append((GROUP[0], tuple(p), tuple(d), (I*col[0], I*col[1], I*col[2]), inner, outer, rad, up))

# ---------------------------------------------------------------------------- plan (estimated)
CH, T = 2.30, 0.15
W, D = 1.65, 3.00          # wide part (vanity side)
XC, ZS = 1.00, 1.40        # narrow corridor (x 0-1.0) toward the washer alcove, steps out at z 1.40
wall_r = 'accent' if ACCENT == 'vanity' else 'wall'
wall_b = 'accent' if ACCENT == 'washer' else 'wall'
setg('shell')
box(-0.60, -T, -T, W+T, 0, D+0.6, 'floor')
box(-0.60, CH, -T, W+T, CH+T, D+0.6, 'ceiling')
box(-T, 0, -T, W+T, CH, 0, wall_b)                     # back wall (washer)
box(-T, 0, 0, 0, CH, 2.15, 'wall')                     # left wall (door), niche cut further front
box(-T, 0, 2.95, 0, CH, D+T, 'wall')
box(-0.40-T, 0, 2.15, -0.40, CH, 2.95, 'wall')         # back of the left shelf niche
box(-0.40, 0, 2.10, 0, CH, 2.15, 'wall'); box(-0.40, 0, 2.95, 0, CH, 3.0, 'wall')
box(XC, 0, 0, W+T, CH, ZS, 'wall')                     # bathroom block (right of the corridor)
box(W, 0, ZS, W+T, CH, D+T, wall_r)                    # right wall behind the vanity
box(-T, 0, D, 0.25, CH, D+T, 'wall'); box(1.10, 0, D, W+T, CH, D+T, 'wall'); box(0.25, 2.0, D, 1.10, CH, D+T, 'wall')
# entrance jambs (dark, existing / or per proposal) seen at the frame edges like the photo
box(0.20, 0, D-0.01, 0.25, 2.04, D+T+0.01, 'frame'); box(1.10, 0, D-0.01, 1.15, 2.04, D+T+0.01, 'frame'); box(0.20, 2.0, D-0.01, 1.15, 2.04, D+T+0.01, 'frame')
box(0.25, -T, D, 1.10, 0.0, D+0.6, 'floor')
# baseboards
for (x1, z1, x2, z2) in ((0, 0, XC, 0.012), (0, 0, 0.012, 2.10), (XC-0.012, 0, XC, ZS), (XC, ZS-0.012, W, ZS)):
    box(x1, 0, z1, x2, 0.06, z2, 'base')
box(W-0.012, 0, 2.35, W, 0.06, D, 'base')

# left wall door (existing, to the corridor) z 0.30-1.05
setg('door_l')
box(0.0, 0.0, 0.30, 0.03, 2.0, 1.05, 'frame')
box(0.0, 0.0, 0.26, 0.05, 2.04, 0.30, 'frame'); box(0.0, 0.0, 1.05, 0.05, 2.04, 1.09, 'frame'); box(0.0, 2.0, 0.26, 0.05, 2.04, 1.09, 'frame')
cyl((0.03, 1.0, 0.95), (0.08, 1.0, 0.95), 0.01, 'chrome')
# bathroom door on the corridor's right wall (x = XC) z 0.25-1.05
setg('door_b')
box(XC-0.05, 0.0, 0.21, XC, 2.04, 0.25, 'frame'); box(XC-0.05, 0.0, 1.05, XC, 2.04, 1.09, 'frame'); box(XC-0.05, 2.0, 0.21, XC, 2.04, 1.09, 'frame')
box(XC-0.03, 0.02, 0.25, XC, 2.0, 1.05, 'door_g')
box(XC-0.035, 0.30, 0.32, XC-0.03, 1.85, 0.62, 'glass_f'); box(XC-0.035, 0.30, 0.68, XC-0.03, 1.85, 0.98, 'glass_f')
box(XC-0.05, 0.95, 0.63, XC-0.03, 1.15, 0.67, 'chrome')

# washer alcove: pan + washer + shelf above
setg('washer')
box(0.18, 0.0, 0.03, 0.82, 0.06, 0.67, 'pan')
rr((0.50, 0.53, 0.33), (0.30, 0.47, 0.30), 'washer', r=0.03)
box(0.24, 0.95, 0.03, 0.76, 1.02, 0.18, 'washer')                # control panel
box(0.30, 1.00, 0.36, 0.70, 1.001, 0.60, 'washer_d')             # glass lid
box(0.0, 1.55, 0.0, XC, 1.58, 0.32, 'oak')
box(0.0, 1.95, 0.0, XC, 1.98, 0.32, 'oak')
for i, x in enumerate((0.15, 0.40, 0.65, 0.85)):
    if i % 2 == 0:
        box(x-0.10, 1.58, 0.05, x+0.10, 1.76, 0.28, 'basket')
    else:
        cyl((x, 1.58, 0.16), (x, 1.80, 0.16), 0.04, 'bottle' if i == 1 else 'bottle2')

# vanity (existing white W750, 3-sided mirror cabinet) on the right wall z 1.55-2.30
setg('vanity')
VZ1, VZ2 = 1.55, 2.30
box(W-0.55, 0.0, VZ1, W, 0.78, VZ2, 'vanity')
for zz in (VZ1+0.375,):
    box(W-0.551, 0.08, zz-0.002, W-0.55, 0.74, zz+0.002, 'base')
rr((W-0.28, 0.80, (VZ1+VZ2)/2), (0.28, 0.03, 0.38), 'ceramic', r=0.02)
ell((W-0.30, 0.80, (VZ1+VZ2)/2), (0.18, 0.06, 0.25), np.eye(3), 'white')
cyl((W-0.10, 0.83, (VZ1+VZ2)/2), (W-0.10, 1.05, (VZ1+VZ2)/2), 0.014, 'chrome')
cyl((W-0.10, 1.05, (VZ1+VZ2)/2), (W-0.22, 1.02, (VZ1+VZ2)/2), 0.012, 'chrome')
box(W-0.16, 1.15, VZ1, W, 1.95, VZ2, 'white')                     # mirror cabinet body
box(W-0.162, 1.18, VZ1+0.03, W-0.16, 1.92, VZ2-0.03, 'mirror')
box(W-0.20, 1.95, VZ1, W, 2.03, VZ2, 'white')
box(W-0.201, 1.96, VZ1+0.05, W-0.20, 2.02, VZ2-0.05, 'lamp', noshadow=True)
box(W-0.32, 1.25, ZS, W, 1.95, ZS+0.12, 'white')                  # small wall cabinet on the step wall
cyl((W-0.06, 0.83, VZ1+0.08), (W-0.06, 1.0, VZ1+0.08), 0.03, 'bottle')
# open shelf niche on the left (existing), towels
setg('shelf')
for y in (0.0, 0.85, 1.35, 1.85):
    box(-0.40, y, 2.15, 0.0, y+0.025, 2.95, 'white')
for (y, z, m) in ((0.875, 2.35, 'towel1'), (0.875, 2.70, 'towel2'), (1.375, 2.45, 'towel1'), (1.375, 2.75, 'basket')):
    box(-0.36, y, z-0.13, -0.05, y+0.24, z+0.13, m)
cyl((-0.20, 1.875, 2.40), (-0.20, 2.00, 2.40), 0.05, 'basket')
for k in range(9):
    a = k*0.7
    ell((-0.20+0.06*math.cos(a), 2.05+0.02*(k % 3), 2.40+0.06*math.sin(a)), (0.05, 0.004, 0.025),
        np.array([[math.cos(a), 0, -math.sin(a)], [0, 1, 0], [math.sin(a), 0, math.cos(a)]]), 'leaf')
box(-0.38, 0.03, 2.20, -0.02, 0.82, 2.90, 'white')               # drawer chest
for y in (0.30, 0.56):
    box(-0.021, y, 2.22, -0.02, y+0.004, 2.88, 'base')

# ceiling: round light + vent (existing)
setg('ceiling')
cyl((0.50, CH-0.01, 1.05), (0.50, CH, 1.05), 0.14, 'white', noshadow=True)
cyl((0.50, CH-0.012, 1.05), (0.50, CH-0.009, 1.05), 0.10, 'lamp', noshadow=True)
light((0.50, CH-0.05, 1.05), 6.0, inner=45, outer=85, rad=0.10)
box(0.42, CH-0.005, 0.50, 0.62, CH, 0.62, 'grille', noshadow=True)
cyl((0.80, CH-0.01, 2.30), (0.80, CH, 2.30), 0.14, 'white', noshadow=True)
cyl((0.80, CH-0.012, 2.30), (0.80, CH-0.009, 2.30), 0.10, 'lamp', noshadow=True)
light((0.80, CH-0.05, 2.30), 6.0, inner=45, outer=85, rad=0.10)
light((W-0.25, 1.98, (VZ1+VZ2)/2), 1.5, d=(-0.3, -1, 0), inner=40, outer=80, rad=0.15)


def yaw_to(cx, cz, tx, tz):
    return math.atan2(tx - cx, -(tz - cz))
def view(cx, cz, tx, tz, fov, drop=(), cy=1.45, sy=-0.30):
    return dict(cam=(cx, cy, cz, yaw_to(cx, cz, tx, tz), fov, 0.0, sy), drop=set(drop))

VIEWS = {
    'main': view(0.66, 3.25, 0.60, 0.0, 90, sy=-0.60),          # same viewpoint as the site photo (from the entrance)
}
ENV = (0.01, 0.01, 0.01)
