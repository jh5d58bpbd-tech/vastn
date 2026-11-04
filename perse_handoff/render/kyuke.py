"""Staff break room (1F reform plan) - wood-based cafe style. Units: metres.
x = east (0..5.4), z = south (0..11.8), y = up. North wall z=0 (entrance / hand-wash side), west wall x=0 (work area side).
"""
import math, random, sys
import numpy as np

def srgb(r, g, b):
    f = lambda c: (c/255)/12.92 if c/255 <= 0.04045 else ((c/255+0.055)/1.055)**2.4
    return (f(r), f(g), f(b))

MATS, NAMES = [], {}
def mat(name, rgb, typ=0, tex=0, ks=0.0, ex=50, emit=(0, 0, 0), bump=0.0, axis=-1, lin=False):
    c = rgb if lin else srgb(*rgb)
    NAMES[name] = len(MATS)
    MATS.append((c, typ, tex, ks, ex, emit, bump, axis))

# --- materials
mat('plaster', (240, 238, 234), tex=3, bump=1.0)
mat('ceiling', (242, 240, 236), tex=3)
mat('floor', (168, 116, 70), tex=1, ks=0.08, ex=220, axis=2)
mat('woodceil', (236, 234, 230), tex=3)
mat('gyptone', (202, 202, 200), tex=3, bump=0.5)
mat('seam', (205, 204, 200))
mat('woodcloth', (172, 122, 78), tex=4, ks=0.02, ex=30, axis=1)
mat('vinyl_b', (120, 112, 104), ks=0.03, ex=40)
mat('oak', (196, 140, 86), tex=4, ks=0.05, ex=80)
mat('oak_h', (196, 140, 86), tex=4, ks=0.05, ex=80, axis=0)
mat('oak_hz', (196, 140, 86), tex=4, ks=0.05, ex=80, axis=2)
mat('oak_v', (196, 140, 86), tex=4, ks=0.05, ex=80, axis=1)
mat('walnut', (184, 128, 76), tex=4, ks=0.07, ex=150)
mat('walnut_h', (184, 128, 76), tex=4, ks=0.10, ex=300, axis=0)
mat('walnut_v', (112, 106, 100), tex=3, bump=0.3, ks=0.04, ex=60)
mat('louver', (138, 120, 102), tex=4, ks=0.03, ex=40, axis=1)
mat('door', (214, 206, 192), ks=0.04, ex=80)
mat('white', (238, 236, 231), ks=0.04, ex=120)
mat('ceramic', (242, 241, 238), ks=0.06, ex=600)
mat('black', (28, 27, 26), ks=0.06, ex=120)
mat('blackmatte', (32, 31, 30), ks=0.02, ex=20)
mat('steel_blk', (40, 40, 40), ks=0.10, ex=150)
mat('greycab', (52, 70, 60), tex=3, bump=0.3, ks=0.06, ex=90)
mat('stone', (214, 206, 190), tex=3, bump=1.4, ks=0.05, ex=120)
mat('top', (40, 40, 40), ks=0.10, ex=300)
mat('chrome', (200, 200, 198), typ=4, ex=1500)
mat('steel', (170, 170, 168), typ=4, ex=180)
mat('brass', (205, 160, 95), typ=4, ex=400)
mat('glass', (232, 240, 238), typ=2)
mat('alu', (190, 190, 188), typ=4, ex=120)
mat('fabric_b', (206, 194, 174), tex=8)
mat('fabric_g', (180, 172, 160), tex=8)
mat('fabric_t', (172, 120, 84), tex=8)
mat('cushion', (168, 160, 150), tex=8)
mat('soil', (45, 34, 26))
mat('leaf1', (52, 92, 44), ks=0.06, ex=60)
mat('leaf2', (70, 108, 52), ks=0.06, ex=60)
mat('leaf3', (40, 74, 38), ks=0.06, ex=60)
mat('stem', (90, 70, 50))
mat('pot', (226, 222, 214), ks=0.05, ex=80)
mat('potstone', (190, 184, 174), tex=3, bump=2.0, ks=0.03, ex=40)
mat('basket', (170, 136, 92), tex=8)
mat('downlight', (255, 255, 255), emit=(12.0, 10.5, 8.4))
mat('globe', (255, 255, 255), emit=(4.6, 2.9, 1.3))
mat('shade_in', (255, 250, 240), emit=(6.0, 5.0, 3.6))
mat('ledstrip', (255, 255, 255), emit=(10.0, 8.6, 6.6))
mat('screen', (14, 16, 20), ks=0.2, ex=800)
mat('vend', (226, 226, 222), ks=0.05, ex=150)
mat('vendlit', (255, 255, 255), emit=(2.4, 2.4, 2.3))
mat('book1', (190, 180, 160), tex=8)
mat('book2', (90, 100, 95), tex=8)
mat('book3', (150, 120, 90), tex=8)
mat('mug', (236, 232, 224), ks=0.08, ex=300)
mat('amber', (120, 66, 26), ks=0.08, ex=400)
mat('picture', (255, 255, 255), tex=5, ks=0.02, ex=60)
mat('rug', (150, 144, 136), tex=8)
mat('ac', (236, 235, 232), ks=0.03, ex=40)
mat('grille', (150, 150, 148))
mat('dinoc', (160, 112, 68), tex=4, ks=0.09, ex=140, axis=1)
mat('melamine', (96, 96, 94), ks=0.06, ex=90)
mat('mel_top', (70, 70, 69), tex=3, bump=0.4, ks=0.07, ex=120)
mat('ih', (16, 16, 18), ks=0.25, ex=1200)
mat('chairwood', (34, 28, 24), tex=4, ks=0.07, ex=90)
mat('cognac', (194, 186, 172), tex=8)
mat('mustard', (180, 172, 160), tex=8)
mat('wains', (150, 106, 66), tex=4, ks=0.05, ex=70, axis=1)
mat('wains_h', (150, 106, 66), tex=4, ks=0.05, ex=70, axis=0)
mat('wains_z', (150, 106, 66), tex=4, ks=0.05, ex=70, axis=2)
mat('gilt', (196, 150, 80), typ=4, ex=250)
mat('sky', (255, 255, 255), emit=(1.35, 1.40, 1.45))
mat('hedge1', (70, 110, 56), ks=0.04, ex=40)
mat('hedge2', (92, 128, 66), ks=0.04, ex=40)

PRIMS, LIGHTS = [], []
GROUP = ['shell']
def setg(g): GROUP[0] = g
def Ry(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
def Rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def Rx(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def flags(noshadow=False):
    return (1 if noshadow else 0) | (2 if GROUP[0] == 'shell' else 0)
def box(x1, y1, z1, x2, y2, z2, m, noshadow=False):
    x1, x2 = min(x1, x2), max(x1, x2); y1, y2 = min(y1, y2), max(y1, y2); z1, z2 = min(z1, z2), max(z1, z2)
    c = ((x1+x2)/2, (y1+y2)/2, (z1+z2)/2); h = ((x2-x1)/2, (y2-y1)/2, (z2-z1)/2)
    PRIMS.append((GROUP[0], 'box', c, h, np.eye(3), NAMES[m], flags(noshadow)))
def obox(c, h, R, m, noshadow=False):
    PRIMS.append((GROUP[0], 'box', tuple(c), tuple(h), np.array(R), NAMES[m], flags(noshadow)))
def rr(c, h, m, r=0.03, R=None, noshadow=False):
    PRIMS.append((GROUP[0], 'rbx', tuple(c), tuple(h), np.eye(3) if R is None else np.array(R), NAMES[m], flags(noshadow), r))
def cyl(p0, p1, r, m, noshadow=False):
    PRIMS.append((GROUP[0], 'cyl', tuple(p0), tuple(p1), r, NAMES[m], flags(noshadow)))
def ell(c, radii, R, m, noshadow=False):
    M = np.diag([1/radii[0], 1/radii[1], 1/radii[2]]) @ np.array(R).T
    PRIMS.append((GROUP[0], 'ell', tuple(c), M, max(radii), NAMES[m], flags(noshadow)))
WARM = (1.0, 0.85, 0.68)
DAY = (0.92, 0.96, 1.0)
def light(p, I, d=(0, -1, 0), inner=22, outer=48, rad=0.035, up=0.0, col=WARM):
    LIGHTS.append((GROUP[0], p, d, (I*col[0], I*col[1], I*col[2]), inner, outer, rad, up))

W, D, H = 5.4, 11.8, 2.7
WN, ZE = 5.9, 5.35          # north part reaches the stair/PS side; toilet wall starts at z=5.35
T = 0.15
# ============================== shell =====================================
setg('shell')
box(-T, -T, -T, WN+T, 0, D+1.5, 'floor')
box(-T, H, -T, WN+T, H+T, D+T, 'gyptone')
box(-T, 0, -T, WN+T, H, 0, 'plaster')                      # north
box(-T, 0, 0, 0, H, D+T, 'plaster')                        # west
box(W, 0, ZE, W+T, H, D+T, 'plaster')                      # east (toilet wall)
box(WN, 0, 0, WN+T, H, ZE, 'plaster')                      # east (stair side)
box(W, 0, ZE, WN+T, H, ZE+T, 'plaster')                    # return
box(4.85, 0, 0, WN, H, 0.65, 'plaster')                    # PS
# south wall with window AW14 (x 1.37-4.10, y 0.75-2.30) and door AD3 (x 0.45-1.28)
WX1, WX2, WY1, WY2 = 1.37, 4.10, 0.70, 2.30
box(-T, 0, D, 0.45, H, D+T, 'plaster')
box(1.28, 0, D, WX1, H, D+T, 'plaster')
box(0.45, 2.10, D, 1.28, H, D+T, 'plaster')
box(WX1, 0, D, WX2, WY1, D+T, 'plaster')
box(WX1, WY2, D, WX2, H, D+T, 'plaster')
box(WX2, 0, D, W+T, H, D+T, 'plaster')
# window frame + mullions
setg('window')
for (x1, x2) in ((WX1, WX1+0.04), (WX2-0.04, WX2), (2.725, 2.755)):
    box(x1, WY1, D+0.04, x2, WY2, D+0.10, 'alu')
box(WX1, WY1, D+0.04, WX2, WY1+0.04, D+0.10, 'alu')
box(WX1, WY2-0.04, D+0.04, WX2, WY2, D+0.10, 'alu')
box(WX1, WY1-0.02, D-0.03, WX2, WY1, D+0.04, 'white')      # sill
# planting strip outside (植栽帯)
# door AD3 (leaf closed, wood)
setg('door_s')
box(0.45, 0, D+0.002, 1.28, 2.10, D+0.04, 'door')
box(0.45, 0, D-0.003, 1.28, 2.10, D+0.002, 'dinoc')
box(0.42, 0, D-0.02, 0.45, 2.13, D+0.02, 'oak_v'); box(1.28, 0, D-0.02, 1.31, 2.13, D+0.02, 'oak_v')
box(0.42, 2.10, D-0.02, 1.31, 2.13, D+0.02, 'oak_h')
cyl((1.15, 1.0, D-0.005), (1.15, 1.0, D-0.06), 0.011, 'black'); cyl((1.15, 1.0, D-0.06), (1.03, 1.0, D-0.06), 0.011, 'black')

# baseboards (巾木 貼り直し)
setg('shell')
for (x1, z1, x2, z2) in ((0, 0, 4.85, 0.012), (0, 0, 0.012, D), (W-0.012, ZE, W, D), (WN-0.012, 0.65, WN, ZE),
                         (0, D-0.012, 0.45, D), (1.28, D-0.012, W, D), (W, ZE, WN, ZE+0.012), (4.85, 0.65, WN, 0.662), (4.838, 0, 4.85, 0.65)):
    box(x1, 0, z1, x2, 0.06, z2, 'vinyl_b')
# PS inspection panel (existing) + stair door AD7 on the east wall of the front room
setg('door_n')
box(5.02, 0.40, 0.65, 5.42, 1.62, 0.665, 'door')
cyl((5.36, 0.95, 0.665), (5.36, 0.95, 0.69), 0.012, 'steel')
box(WN-0.035, 0, 0.78, WN, 2.05, 1.58, 'door')
box(WN-0.05, 0, 0.75, WN, 2.08, 0.78, 'white'); box(WN-0.05, 0, 1.58, WN, 2.08, 1.61, 'white'); box(WN-0.05, 2.05, 0.75, WN, 2.08, 1.61, 'white')
cyl((WN-0.035, 1.0, 1.48), (WN-0.09, 1.0, 1.48), 0.011, 'steel'); cyl((WN-0.09, 1.0, 1.48), (WN-0.09, 1.0, 1.36), 0.011, 'steel')

rnd = random.Random(7)
def leaves(cx, cy, cz, n, spread, height, size=0.07, droop=0.0, seed=0, mats=('leaf1', 'leaf2', 'leaf3')):
    r = random.Random(seed)
    for i in range(n):
        a = r.random()*2*math.pi; rad = spread*math.sqrt(r.random())
        y = cy + r.random()*height - droop*rad
        R = Ry(r.random()*2*math.pi) @ Rz(r.uniform(-0.9, 0.9)) @ Rx(r.uniform(-0.6, 0.6))
        s = size*r.uniform(0.7, 1.25)
        ell((cx+math.cos(a)*rad, y, cz+math.sin(a)*rad), (s, 0.006, s*0.45), R, r.choice(mats))

def plant(x, z, h=1.6, seed=1, pot='potstone', pr=0.2):
    cyl((x, 0, z), (x, 0.42, z), pr, pot)
    cyl((x, 0.40, z), (x, 0.425, z), pr-0.02, 'soil')
    cyl((x, 0.42, z), (x+0.03, h*0.75, z), 0.016, 'stem')
    cyl((x+0.03, h*0.6, z), (x-0.12, h*0.95, z+0.05), 0.01, 'stem')
    leaves(x, 0.8, z, int(190*h/1.6), 0.36, h-0.8, size=0.065, seed=seed)


# ============================== ceiling ===================================
def downlight(x, z, I=6.0, inner=20, outer=50, yc=None):
    yc = H if yc is None else yc
    cyl((x, yc-0.004, z), (x, yc, z), 0.055, 'white', noshadow=True)
    cyl((x, yc-0.006, z), (x, yc-0.003, z), 0.038, 'downlight', noshadow=True)
    light((x, yc-0.03, z), I, inner=inner, outer=outer)

setg('ceiling')
# 天井: クロス仕上げ（薄いグレー）— no board seams
for x in (1.15, 2.65, 4.15):
    for z in (2.75, 4.55, 6.35, 8.15, 9.95, 11.2):
        if not (x == 2.65 and z in (4.55, 9.95)):
            downlight(x, z, I=4.6, inner=18, outer=50)
for x in (1.0, 2.6):
    downlight(x, 1.0, I=4.6)
downlight(4.6, 1.1, I=4.0)       # 前室用 ダウンライト x1
downlight(5.5, 3.25, I=3.0)
for z in (6.4, 8.55, 10.6):
    downlight(4.95, z, I=3.6, outer=44)
# ceiling cassette ACs (existing, reuse)
for zc in (4.55, 9.95):
    box(2.23, H-0.035, zc-0.42, 3.07, H, zc+0.42, 'ac')
    box(2.41, H-0.037, zc-0.24, 2.89, H-0.035, zc+0.24, 'grille')

# ============================== kitchen: Estetico compact kitchen W1200 D600 H850 (smoky grey) ===
setg('kitchen')
KZ1, KZ2, KD, KH = 0.85, 2.05, 0.60, 0.85
# NOTE: this block is authored at z 0.85-2.05 and the whole 'kitchen' group is shifted by -0.28 further down
#       (see the loop before the louver section), so the actual kitchen sits at z 0.57-1.77 as in the plan.
box(0.0, 0.0, KZ1, KD-0.04, 0.07, KZ2, 'blackmatte')
rr((KD/2, 0.07+(KH-0.07-0.03)/2, (KZ1+KZ2)/2), (KD/2, (KH-0.07-0.03)/2, (KZ2-KZ1)/2), 'melamine', r=0.003)
box(KD-0.001, 0.445, KZ1+0.004, KD+0.001, 0.465, KZ2-0.004, 'blackmatte')
box(KD-0.001, KH-0.065, KZ1+0.004, KD+0.001, KH-0.05, KZ2-0.004, 'blackmatte')
rr((KD/2, KH-0.015, (KZ1+KZ2)/2), (KD/2, 0.015, (KZ2-KZ1)/2), 'mel_top', r=0.002)
box(0.10, KH-0.012, 1.45, 0.50, KH+0.0005, 1.98, 'steel')
cyl((0.07, KH, 1.70), (0.07, KH+0.34, 1.70), 0.014, 'chrome')
cyl((0.07, KH+0.34, 1.70), (0.25, KH+0.34, 1.70), 0.013, 'chrome')
cyl((0.25, KH+0.34, 1.70), (0.25, KH+0.26, 1.70), 0.012, 'chrome')
cyl((0.07, KH+0.12, 1.70), (0.13, KH+0.15, 1.70), 0.008, 'chrome')
box(0.07, KH, 0.93, 0.55, KH+0.004, 1.38, 'ih')
for zc in (1.04, 1.27):
    cyl((0.31, KH+0.004, zc), (0.31, KH+0.0045, zc), 0.09, 'steel_blk', noshadow=True)
cyl((0.30, KH+0.004, 1.04), (0.30, KH+0.17, 1.04), 0.07, 'black')
cyl((0.30, KH+0.17, 1.04), (0.30, KH+0.19, 1.04), 0.025, 'black')
box(0, KH, KZ1-0.05, 0.012, 1.60, KZ2+0.05, 'stone')
for y in (1.62, 2.02):
    box(0, y, KZ1-0.05, 0.30, y+0.012, KZ2+0.05, 'steel_blk')
    box(0.29, y-0.04, KZ1-0.05, 0.30, y+0.012, KZ2+0.05, 'steel_blk')
r = random.Random(5)
for zc in np.arange(KZ1+0.05, KZ2, 0.16):
    k = r.random()
    if k < 0.45:
        cyl((0.15, 1.632, zc), (0.15, 1.632+r.uniform(0.10, 0.17), zc), 0.045, r.choice(['glass', 'mug', 'amber']))
    elif k < 0.75:
        cyl((0.15, 2.032, zc), (0.15, 2.032+r.uniform(0.08, 0.14), zc), 0.05, r.choice(['mug', 'potstone']))
cyl((0.15, 2.032, 1.0), (0.15, 2.12, 1.0), 0.07, 'potstone')
leaves(0.15, 2.04, 1.0, 30, 0.12, 0.12, size=0.04, droop=0.6, seed=11)
downlight(0.45, 1.45, I=4.0, inner=20, outer=50)

for i, p in enumerate(PRIMS):
    if p[0] != 'kitchen': continue
    q = list(p)
    if p[1] in ('box', 'rbx', 'ell'):
        c = list(q[2]); c[2] -= 0.28; q[2] = tuple(c)
    elif p[1] == 'cyl':
        a = list(q[2]); b = list(q[3]); a[2] -= 0.28; b[2] -= 0.28; q[2] = tuple(a); q[3] = tuple(b)
    PRIMS[i] = tuple(q)
for i, l in enumerate(LIGHTS):
    if l[0] != 'kitchen': continue
    q = list(l); pp = list(q[1]); pp[2] -= 0.28; q[1] = tuple(pp); LIGHTS[i] = tuple(q)
# ============================== counter + shelf in the dashed boxes right of the star (前室) ===
setg('ncounter')
# counter (rect A): x 1.60-2.35, z 0.0-0.92, front facing east into the front room
CX1, CX2, CZ2, CH = 1.60, 2.35, 0.92, 0.90
box(CX1+0.04, 0, 0.0, CX2-0.05, 0.07, CZ2-0.02, 'blackmatte')
rr(((CX1+CX2)/2, 0.07+(CH-0.07-0.035)/2, CZ2/2), ((CX2-CX1)/2, (CH-0.07-0.035)/2, CZ2/2), 'oak', r=0.004)
box(CX2-0.001, 0.08, CZ2/2-0.003, CX2+0.001, CH-0.04, CZ2/2+0.003, 'blackmatte')
rr(((CX1+CX2)/2, CH-0.017, CZ2/2), ((CX2-CX1)/2+0.015, 0.017, CZ2/2+0.01), 'walnut_h', r=0.003)
rr((1.85, CH+0.17, 0.25), (0.15, 0.17, 0.13), 'black', r=0.02)          # coffee machine
for zc in (0.55, 0.64, 0.73):
    cyl((2.05, CH, zc), (2.05, CH+0.09, zc), 0.04, 'mug')
box(1.70, CH, 0.55, 1.95, CH+0.10, 0.82, 'basket')
# shelf (rect B): x 1.60-2.20, z 0.92-1.85, open cubbies facing east, height 1.20
SX1, SX2, SZ1, SZ2, SH = 1.60, 2.20, 0.94, 1.85, 1.20
box(SX1, 0, SZ1, SX2, 0.04, SZ2, 'oak_hz')
for y in (0.40, 0.80):
    box(SX1, y, SZ1, SX2, y+0.025, SZ2, 'oak_hz')
box(SX1, SH-0.03, SZ1, SX2, SH, SZ2, 'walnut_h')
box(SX1, 0, SZ1, SX1+0.02, SH-0.03, SZ2, 'oak_v')                        # back
box(SX1, 0, SZ1, SX2, SH-0.03, SZ1+0.025, 'oak_v'); box(SX1, 0, SZ2-0.025, SX2, SH-0.03, SZ2, 'oak_v')
box(SX1, 0.04, (SZ1+SZ2)/2-0.012, SX2, SH-0.03, (SZ1+SZ2)/2+0.012, 'oak_v')
r = random.Random(9)
for (y0, zc) in ((0.825, 1.15), (0.825, 1.62), (0.425, 1.16), (0.425, 1.62), (0.04, 1.15), (0.04, 1.62)):
    k = r.random()
    if k < 0.35:
        box(1.66, y0, zc-0.16, 1.98, y0+0.14, zc+0.16, 'basket')
    elif k < 0.7:
        for j in range(5):
            cyl((1.78, y0, zc-0.12+j*0.06), (1.78, y0+0.10+0.03*(j % 2), zc-0.12+j*0.06), 0.03, ['glass', 'amber', 'mug'][j % 3])
    else:
        for j in range(6):
            box(1.64, y0, zc-0.15+j*0.05, 1.90, y0+0.24+0.03*(j % 3), zc-0.11+j*0.05, ['book1', 'book2', 'book3'][j % 3])
cyl((1.90, SH, 1.62), (1.90, SH+0.11, 1.62), 0.07, 'potstone')
leaves(1.90, SH+0.11, 1.62, 40, 0.13, 0.15, size=0.045, droop=0.4, seed=33)
downlight(2.0, 0.5, I=3.2, inner=20, outer=50)

# ============================== front room louver (▼ new wall) ===========
setg('louver')
LX1, LZ = 3.73, 1.60
x = LX1
while x < WN - 0.02:
    box(x, 0, LZ-0.06, x+0.035, H, LZ+0.06, 'louver')
    x += 0.09
box(LX1, 0, LZ-0.06, WN, 0.05, LZ+0.06, 'walnut_h')
# north door SD2 (existing reuse) + frame
setg('door_n')
box(3.92, 0, 0, 4.78, 2.10, 0.035, 'door')
box(4.38, 1.15, 0.035, 4.50, 1.80, 0.038, 'glass')
box(4.40, 2.0, 0.035, 4.72, 2.05, 0.08, 'steel')
box(3.89, 0, 0, 3.92, 2.13, 0.05, 'oak_v'); box(4.78, 0, 0, 4.81, 2.13, 0.05, 'oak_v')
box(3.89, 2.10, 0, 4.81, 2.13, 0.05, 'oak_h')
cyl((4.68, 1.0, 0.035), (4.68, 1.0, 0.09), 0.011, 'black'); cyl((4.68, 1.0, 0.09), (4.56, 1.0, 0.09), 0.011, 'black')

# ============================== vending machines (east recess, per plan) ====
setg('vending')
VZ1, VZ2 = 2.50, 4.00
for (z1, z2) in ((VZ1, VZ1+0.74), (VZ1+0.78, VZ2)):
    rr((5.52, 0.92, (z1+z2)/2), (0.34, 0.92, (z2-z1)/2), 'vend', r=0.015)
    box(5.17, 1.05, z1+0.06, 5.18, 1.75, z2-0.06, 'vendlit')
    box(5.17, 0.18, z1+0.15, 5.18, 0.32, z2-0.15, 'black')

# ============================== diagonal high counter =====================
setg('counter')
ang = math.radians(-32)
Rc = Ry(ang)
cc = np.array([1.45, 0.0, 3.55])
L2 = 1.15
top = cc + np.array([0, 1.0, 0])
obox(top, (L2, 0.025, 0.30), Rc, 'walnut_h')
# walnut base panel + steel legs
obox(cc + np.array([0, 0.5, 0]), (L2-0.12, 0.48, 0.05), Rc, 'walnut_h')
for s in (-1, 1):
    p = cc + Rc @ np.array([s*(L2-0.08), 0, 0])
    obox(p + np.array([0, 0.49, 0]), (0.02, 0.49, 0.26), Rc, 'steel_blk')
def stool(x, z):
    cyl((x, 0.70, z), (x, 0.74, z), 0.18, 'walnut')
    for k in range(4):
        a = k*math.pi/2 + 0.4
        cyl((x+0.09*math.cos(a), 0.70, z+0.09*math.sin(a)), (x+0.20*math.cos(a), 0, z+0.20*math.sin(a)), 0.012, 'steel_blk')
    for k in range(4):
        a1, a2 = k*math.pi/2 + 0.4, (k+1)*math.pi/2 + 0.4
        cyl((x+0.165*math.cos(a1), 0.26, z+0.165*math.sin(a1)), (x+0.165*math.cos(a2), 0.26, z+0.165*math.sin(a2)), 0.008, 'steel_blk')
for t in (-0.75, 0.0, 0.75):
    for side in (-1, 1):
        p = cc + Rc @ np.array([t, 0, side*0.55])
        stool(p[0], p[2])
# pendants over the counter
def pendant(x, z, y=1.85, kind='dome'):
    cyl((x, H-0.06, z), (x, y+0.16, z), 0.003, 'black', noshadow=True)
    if kind == 'dome':
        ell((x, y+0.10, z), (0.16, 0.12, 0.16), np.eye(3), 'brass', noshadow=True)
        cyl((x, y+0.04, z), (x, y+0.045, z), 0.12, 'shade_in', noshadow=True)
        light((x, y+0.02, z), 3.0, inner=30, outer=70, rad=0.05, up=0.0)
    else:
        ell((x, y, z), (0.11, 0.11, 0.11), np.eye(3), 'globe', noshadow=True)
        cyl((x, y+0.10, z), (x, y+0.14, z), 0.03, 'brass', noshadow=True)
        light((x, y-0.13, z), 1.6, inner=60, outer=90, rad=0.08, up=0.35)


# ============================== round tables ==============================
setg('tables')
def cafechair(x, z, face):
    """Antique bentwood chair. face: yaw the sitter looks toward (0 = -z, pi/2 = +x)."""
    R = Ry(face)
    loc = lambda v: np.array([x, 0, z]) + R @ np.array(v)
    legs = ((-0.19, -0.18), (0.19, -0.18), (-0.18, 0.17), (0.18, 0.17))
    for (dx, dz) in legs:
        cyl(loc((dx, 0.43, dz)), loc((dx*1.10, 0, dz*1.12)), 0.016, 'chairwood')
    ring = [loc((0.205*math.cos(t), 0.20, 0.195*math.sin(t))) for t in np.linspace(0, 2*math.pi, 13)]
    for p, q in zip(ring[:-1], ring[1:]):
        cyl(p, q, 0.008, 'chairwood')
    rr(loc((0, 0.425, 0)), (0.22, 0.02, 0.21), 'chairwood', r=0.015, R=R)
    rr(loc((0, 0.465, -0.01)), (0.205, 0.028, 0.19), 'cognac', r=0.028, R=R)
    # rear posts and curved back rails
    arc = lambda y, n=9: [loc((0.19*math.sin(a), y, 0.13 + 0.07*math.cos(a))) for a in np.linspace(-math.pi/2, math.pi/2, n)]
    for dx in (-0.18, 0.18):
        cyl(loc((dx, 0.43, 0.17)), loc((dx*1.05, 0.86, 0.14)), 0.015, 'chairwood')
    for y, r0 in ((0.86, 0.022), (0.64, 0.011)):
        a = arc(y)
        for p, q in zip(a[:-1], a[1:]):
            cyl(p, q, r0, 'chairwood')
    for k in (-0.6, -0.2, 0.2, 0.6):
        cyl(loc((0.19*math.sin(k), 0.49, 0.13+0.07*math.cos(k))), loc((0.19*math.sin(k), 0.86, 0.13+0.07*math.cos(k))), 0.007, 'chairwood')
def roundtable(x, z, r=0.45):
    cyl((x, 0.70, z), (x, 0.73, z), r, 'walnut')
    cyl((x, 0.69, z), (x, 0.70, z), r-0.02, 'walnut')
    cyl((x, 0.05, z), (x, 0.69, z), 0.035, 'steel_blk')
    for k in range(4):
        a = k*math.pi/2 + math.pi/4
        obox((x+0.17*math.cos(a), 0.02, z+0.17*math.sin(a)), (0.19, 0.02, 0.025), Ry(-a), 'steel_blk')
for (tx, tz) in ((1.9, 6.8), (1.9, 10.3)):
    roundtable(tx, tz)
    for k in range(4):
        a = k*math.pi/2 + math.pi/4
        cx, cz = tx + 0.72*math.sin(a), tz + 0.72*math.cos(a)
        cafechair(cx, cz, math.atan2(tx-cx, -(tz-cz)))
    cyl((tx+0.12, 0.73, tz-0.05), (tx+0.12, 0.82, tz-0.05), 0.04, 'mug')
    cyl((tx-0.15, 0.73, tz+0.1), (tx-0.15, 0.80, tz+0.1), 0.045, 'potstone')
    leaves(tx-0.15, 0.80, tz+0.1, 18, 0.06, 0.08, size=0.03, seed=int(tz*10))
# soft rug under round tables
box(1.0, 0.0, 5.9, 2.8, 0.006, 11.2, 'rug')

# ============================== bench seating (east wall) ================
setg('bench')
BZ1, BZ2 = 5.45, 11.55
# vertical wood slat feature wall behind the bench
# accent wall: wood-grain wallcovering behind the sofa (east wall, full height)
box(W-0.004, 0.06, ZE+0.012, W, H, D, 'woodcloth')
# bench body (walnut) + seat & back cushions
box(4.78, 0.0, BZ1, W, 0.40, BZ2, 'walnut_h')
box(4.80, 0.0, BZ1+0.02, W-0.07, 0.06, BZ2-0.02, 'blackmatte')
nseg = 4
seg = (BZ2-BZ1)/nseg
for i in range(nseg):
    z1 = BZ1 + i*seg + 0.01; z2 = z1 + seg - 0.02
    rr((5.06, 0.46, (z1+z2)/2), (0.28, 0.06, (z2-z1)/2), 'fabric_g', r=0.04)
    rr((W-0.09, 0.75, (z1+z2)/2), (0.07, 0.22, (z2-z1)/2), 'fabric_g', r=0.05, R=Rz(math.radians(-8)))
for (tz, k) in ((6.5, 0), (8.55, 1), (10.6, 2)):
    rr((4.15, 0.72, tz), (0.36, 0.018, 0.36), 'walnut', r=0.008)
    cyl((4.15, 0.05, tz), (4.15, 0.70, tz), 0.035, 'steel_blk')
    box(3.93, 0, tz-0.22, 4.37, 0.02, tz+0.22, 'steel_blk')
    cafechair(3.45, tz, math.pi/2)
    cyl((4.05, 0.738, tz+0.1), (4.05, 0.83, tz+0.1), 0.04, 'mug')
    if k == 1:
        box(4.12, 0.738, tz-0.18, 4.40, 0.75, tz+0.02, 'book1')
    for zz in (tz-0.55, tz+0.55):
        rr((5.0, 0.60, zz), (0.06, 0.15, 0.15), 'cushion' if zz < tz else 'mustard', r=0.05, R=Rz(math.radians(-15)))

# ============================== west wall: monitor wall (▼ new fukashi) ==
setg('monitor')
MZ1, MZ2 = 7.55, 10.05
box(0, 0, MZ1, 0.12, H, MZ2, 'walnut_v')
rr((0.15, 1.55, 8.8), (0.03, 0.40, 0.70), 'black', r=0.01)
box(0.181, 1.17, 8.12, 0.183, 1.93, 9.48, 'screen')
box(0.12, 0.0, MZ1, 0.45, 0.45, MZ2, 'oak_hz')     # low credenza
for zc in (8.0, 8.8, 9.6):
    box(0.45, 0.06, zc-0.38, 0.452, 0.42, zc+0.38, 'oak_hz')
for i, zc in enumerate(np.arange(7.7, 8.2, 0.045)):
    box(0.16, 0.45, zc, 0.36, 0.45+0.22+0.04*((i*7) % 3), zc+0.04, ['book1', 'book2', 'book3'][i % 3])
cyl((0.28, 0.45, 9.7), (0.28, 0.65, 9.7), 0.08, 'potstone')
leaves(0.28, 0.65, 9.7, 40, 0.12, 0.20, size=0.05, seed=21)
# wall art on west wall between counter and monitor
box(0.0, 1.15, 5.0, 0.035, 1.95, 6.2, 'gilt')
box(0.03, 1.19, 5.04, 0.035, 1.91, 6.16, 'picture')

# ============================== plants =====================================
setg('plant_se')
plant(4.75, 11.35, h=1.8, seed=3)
setg('plants')
plant(0.45, 11.0, h=1.6, seed=4, pot='basket', pr=0.18)
setg('plant_n')
plant(4.30, 2.20, h=1.5, seed=5)
setg('plants')
plant(0.35, 4.8, h=1.3, seed=6, pot='pot', pr=0.16)

# ============================== exterior: planting strip + bright backdrop ====
setg('outside')
box(-2, -1, D+4.0, W+2, H+3, D+4.2, 'sky', noshadow=True)
box(-2, H+0.6, D+0.3, W+2, H+0.8, D+4.0, 'sky', noshadow=True)
for i, x in enumerate(np.linspace(1.0, 4.5, 8)):
    leaves(x, 0.2, D+0.9, 70, 0.5, 0.9+0.4*((i*3) % 2), size=0.09, seed=60+i, mats=('hedge1', 'hedge2', 'leaf2'))
light((2.7, H+0.5, D+1.2), 14.0, d=(0, -1, 0.0), inner=60, outer=88, rad=0.6, col=(1.0, 0.97, 0.92))
# ============================== daylight from the south window ==============
setg('shell')
for xx in (1.9, 2.75, 3.6):
    light((xx, 1.6, D-0.15), 6.5, d=(0, -0.35, -1), inner=40, outer=88, rad=0.5, col=DAY)

# ============================== export ====================================
def yaw_to(cx, cz, tx, tz):
    return math.atan2(tx - cx, -(tz - cz))
def view(cx, cz, tx, tz, fov, drop=(), cy=1.3, sy=-0.05):
    return dict(cam=(cx, cy, cz, yaw_to(cx, cz, tx, tz), fov, 0.0, sy), drop=set(drop))

VIEWS = {
    # from the entrance side (behind the counter) looking toward the window
    'south': view(3.45, 2.25, 2.3, 11.8, 80),
    # from the window corner looking back toward the kitchen and louver
    'north': view(3.95, 11.50, 0.9, 0.0, 80, drop={'plant_se'}),
    # toward the Estetico kitchen and the front-room louver
    'kitchen': view(3.55, 2.85, 0.5, 0.75, 80, drop={'plant_n'}, cy=1.35),
}
ENV = (1.35, 1.40, 1.45)

def export(vname, Wd, Hh, spp, path):
    v = VIEWS[vname]
    out = []
    for m in MATS:
        c, typ, tex, ks, ex, emit, bump, axis = m
        out.append('mat %f %f %f %d %d %f %f %f %f %f %f %d' % (c[0], c[1], c[2], typ, tex, ks, ex, emit[0], emit[1], emit[2], bump, axis))
    for p in PRIMS:
        if p[0] in v['drop']:
            continue
        if p[1] == 'box':
            _, _, c, h, R, mi, fl = p
            out.append('box %f %f %f %f %f %f %s %d %d' % (*c, *h, ' '.join('%f' % x for x in np.array(R).reshape(-1)), mi, fl))
        elif p[1] == 'rbx':
            _, _, c, h, R, mi, fl, r = p
            out.append('rbx %f %f %f %f %f %f %f %s %d %d' % (*c, *h, r, ' '.join('%f' % x for x in np.array(R).reshape(-1)), mi, fl))
        elif p[1] == 'cyl':
            _, _, p0, p1, r, mi, fl = p
            out.append('cyl %f %f %f %f %f %f %f %d %d' % (*p0, *p1, r, mi, fl))
        else:
            _, _, c, M, rad, mi, fl = p
            out.append('ell %f %f %f %s %f %d %d' % (*c, ' '.join('%f' % x for x in np.array(M).reshape(-1)), rad, mi, fl))
    for l in LIGHTS:
        if l[0] in v['drop']:
            continue
        _, p, d, I, inner, outer, rad, up = l
        out.append('light %f %f %f %f %f %f %f %f %f %f %f %f %f' % (*p, *d, *I, inner, outer, rad, up))
    cx, cy, cz, yaw, fov, sx, sy = v['cam']
    out.append('cam %f %f %f %f %f %f %f %d %d %d' % (cx, cy, cz, yaw, fov, sx, sy, Wd, Hh, spp))
    out.append('env %f %f %f' % ENV)
    open(path, 'w').write('\n'.join(out) + '\n')

if __name__ == '__main__':
    vname, Wd, Hh, spp, path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    export(vname, Wd, Hh, spp, path)
    print(len(PRIMS), 'prims', len(LIGHTS), 'lights')
