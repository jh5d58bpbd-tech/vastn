"""森川ビル リフォーム — scene for the Cycles converter (blender/kyuke_cycles.py, SCENE=morikawa).

Design follows the client's reference perse (refs/morikawa/): exposed concrete walls & ceiling
(formwork joints + tie holes on the TV wall), rich walnut/acacia flooring, walnut trims,
dropped beams with black track spots, lit niche, monstera, black-leg stools.

Units: metres. x = east, y = up, z = south. Origin = north-west corner of the plan's overall
dimension box (the room's west wall is x=0, north wall z=0). Plan: refs/morikawa/01_平面図.pdf
"""
import math
import random

import numpy as np


def srgb(r, g, b):
    f = lambda c: (c/255)/12.92 if c/255 <= 0.04045 else ((c/255+0.055)/1.055)**2.4
    return (f(r), f(g), f(b))


MATS, NAMES = [], {}
def mat(name, rgb, typ=0, tex=0, ks=0.0, ex=50, emit=(0, 0, 0), bump=0.0, axis=-1, lin=False):
    c = rgb if lin else srgb(*rgb)
    NAMES[name] = len(MATS)
    MATS.append((c, typ, tex, ks, ex, emit, bump, axis))

# tex 9 = exposed concrete (bump>0: formwork panel joints + tie holes), tex 10 = walnut/acacia flooring
mat('conc', (150, 149, 143), tex=9, ks=0.02, ex=20)
mat('conc_p', (150, 149, 143), tex=9, ks=0.02, ex=20, bump=1.0)    # formwork panel wall (TV wall)
mat('conc_c', (156, 154, 146), tex=9, ks=0.01, ex=15)              # ceiling slab
mat('floor', (150, 100, 62), tex=10, ks=0.16, ex=600, axis=0)      # flooring along x (toward the window)
mat('floor_z', (150, 100, 62), tex=10, ks=0.16, ex=600, axis=2)
mat('walnut', (96, 62, 40), tex=4, ks=0.06, ex=90)
mat('walnut_h', (104, 68, 44), tex=4, ks=0.06, ex=90, axis=0)
mat('walnut_v', (104, 68, 44), tex=4, ks=0.06, ex=90, axis=1)
mat('walnut_z', (104, 68, 44), tex=4, ks=0.06, ex=90, axis=2)
mat('black', (24, 24, 24), ks=0.06, ex=120)
mat('blackmatte', (30, 30, 30), ks=0.02, ex=20)
mat('steel', (170, 170, 168), typ=4, ex=200)
mat('stainless', (190, 190, 186), typ=4, ex=90)
mat('alu', (176, 176, 172), typ=4, ex=140)
mat('glass', (232, 240, 238), typ=2)
mat('mirror', (236, 236, 232), typ=1)
mat('white', (238, 236, 232), ks=0.05, ex=120)
mat('ceramic', (244, 243, 240), ks=0.10, ex=900)
mat('mortar', (122, 120, 116), tex=3, bump=1.2, ks=0.02, ex=20)   # 玄関 土間
mat('tile', (92, 90, 86), tex=3, bump=0.6, ks=0.05, ex=80)       # トイレ・脱衣所 床
mat('screen', (12, 13, 16), ks=0.25, ex=900)
mat('tvimg', (255, 255, 255), tex=11)                              # TV picture (warm landscape)
mat('ac', (238, 237, 234), ks=0.04, ex=60)
mat('steeldoor', (70, 70, 68), ks=0.05, ex=80)
mat('led', (255, 255, 255), emit=(5.0, 3.7, 2.1))                  # 2700K-ish indirect strip
mat('spot_lens', (255, 255, 255), emit=(14.0, 11.5, 8.0))
mat('sky', (255, 255, 255), emit=(4.0, 4.15, 4.4))
mat('bldg', (214, 214, 212), ks=0.02, ex=20)
mat('bldg2', (196, 198, 200), ks=0.02, ex=20)
mat('parapet', (226, 226, 222), ks=0.02, ex=20)
mat('frosted', (220, 228, 230), typ=3)
mat('leaf1', (26, 58, 30), ks=0.14, ex=120)
mat('leaf2', (34, 70, 36), ks=0.14, ex=120)
mat('stem', (70, 96, 52))
mat('pot', (58, 58, 58), ks=0.05, ex=60)
mat('potc', (128, 124, 118), tex=3, bump=1.5, ks=0.02, ex=30)
mat('soil', (40, 32, 26))
mat('book1', (186, 176, 158), tex=8)
mat('book2', (82, 92, 90), tex=8)
mat('book3', (140, 104, 76), tex=8)
mat('vase', (236, 232, 224), ks=0.12, ex=500)
mat('fabric', (196, 186, 170), tex=8)
mat('towel', (226, 222, 214), tex=8)
mat('basket', (160, 128, 90), tex=8)
mat('kitchen_d', (104, 68, 44), tex=4, ks=0.06, ex=90, axis=0)    # kitchen doors walnut
mat('wash', (240, 240, 238), ks=0.10, ex=300)
mat('fridge', (92, 90, 86), ks=0.10, ex=200)

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
WARM = (1.0, 0.80, 0.60)      # ~2700K
NEUT = (1.0, 0.90, 0.78)      # ~3500K
DAY = (0.92, 0.96, 1.0)
def light(p, I, d=(0, -1, 0), inner=22, outer=48, rad=0.03, up=0.0, col=WARM):
    LIGHTS.append((GROUP[0], tuple(p), tuple(d), (I*col[0], I*col[1], I*col[2]), inner, outer, rad, up))


# ============================================================================ plan
CH = 2.45            # exposed slab ceiling
T = 0.20             # outer wall thickness
DH = 2.00            # door height
X_W, Z_S = 6.98, 4.435
DZ1, DZ2 = 3.10, 3.95       # entrance door on the east wall (not on the plan; assumed)
# outer walls (inner faces) ---------------------------------------------------
setg('shell')
box(-T, -T, -T, X_W+T, 0, 2.71, 'floor')                        # floor (north of the genkan line)
box(-T, -T, 2.71, 5.88, 0, Z_S+T, 'floor')                      # floor (kitchen / hall)
box(5.88, -T-0.3, 2.71, X_W+T, -0.30, Z_S+T, 'mortar')         # genkan slab (lowered)
box(-T, CH, -T, X_W+T, CH+T, Z_S+T, 'conc_c')                   # ceiling slab
NX1, NX2, NY1, NY2, ND = 2.95, 3.65, 1.00, 1.62, 0.16          # lit niche in the north wall (alcove)
box(0.37, 0, -T, NX1, CH, 0, 'conc')                            # north wall, carved around the niche
box(NX2, 0, -T, 5.595, CH, 0, 'conc')
box(NX1, 0, -T, NX2, NY1, 0, 'conc'); box(NX1, NY2, -T, NX2, CH, 0, 'conc')
box(NX1, NY1, -T, NX2, NY2, -ND, 'conc')                        # niche back
box(5.595, 0, -T, 5.81+T, CH, 0.28, 'conc')                     # PS notch top
box(5.81, 0, 0.28, 5.81+T, CH, 1.0, 'conc')                    # east of washer nook
box(5.595, 0, 0.28, 5.81, CH, 1.0, 'conc')                      # PS (closes the slit by the washer nook)
box(5.81, 0, 1.0, X_W+T, CH, 1.20, 'conc')                      # north wall of 脱衣所 east part
box(X_W, 0, 1.0, X_W+T, CH, 2.71, 'conc')                       # east wall (脱衣所)
box(X_W, -0.30, 2.71, X_W+T, CH, DZ1, 'conc'); box(X_W, -0.30, DZ2, X_W+T, CH, Z_S+T, 'conc')   # east wall (玄関, door cut)
box(0.37, -0.30, Z_S, X_W+T, CH, Z_S+T, 'conc')                 # south wall (kitchen + 玄関)
box(-T, 0, -T, 0.37, CH, 0.37, 'conc')                          # NW column
box(-T, 0, 4.065, 0.37, CH, Z_S+T, 'conc')                      # SW column
# west wall with the balcony sliding window (z 1.61-3.395, h 2.10)
WZ1, WZ2, WH = 1.61, 3.395, 2.10
box(-T, 0, 0.37, 0, CH, WZ1, 'conc')
box(-T, 0, WZ2, 0, CH, 4.065, 'conc')
box(-T, WH, WZ1, 0, CH, WZ2, 'conc')

# ============================================================================ LDK
# storage (収納) x 0-2.4, z 0-1.1 ; TV wall z 1.10-1.175 (formwork concrete, south face)
setg('shell')
box(0.37, 0, 0.37, 2.40, CH, 1.10, 'conc')                      # storage mass (interior hidden)
box(0, 0, 1.10, 2.475, CH, 1.175, 'conc_p')                     # TV wall
# storage opening on its east side (z 0.20-0.98), walnut-framed, lit shelves inside
box(2.40, 0, 0.0, 2.475, CH, 0.20, 'conc'); box(2.40, 0, 0.98, 2.475, CH, 1.10, 'conc'); box(2.40, DH, 0.20, 2.475, CH, 0.98, 'conc')
setg('storage')
box(1.70, 0, 0.12, 2.40, CH, 1.10, 'blackmatte')                # dark void behind (keeps storage interior simple)
box(1.75, 0, 0.20, 2.40, DH, 0.98, 'conc')                      # back/side box of the lit closet
for y in (0.45, 0.85, 1.25, 1.65):
    box(1.95, y, 0.20, 2.40, y+0.025, 0.98, 'walnut_z')
    box(2.36, y-0.012, 0.20, 2.37, y-0.002, 0.98, 'led', noshadow=True)
for (y, z, m) in ((0.475, 0.35, 'basket'), (0.875, 0.70, 'book1'), (1.275, 0.40, 'vase'), (1.675, 0.75, 'basket')):
    if m == 'vase':
        cyl((2.15, y, z), (2.15, y+0.22, z), 0.06, 'vase')
    else:
        box(2.0, y, z-0.15, 2.32, y+0.18, z+0.15, m)
light((2.10, 2.05, 0.6), 0.35, d=(0, -1, 0), inner=50, outer=80, rad=0.15)
setg('trim')
box(2.475, 0, 0.17, 2.50, DH+0.03, 0.20, 'walnut_v'); box(2.475, 0, 0.98, 2.50, DH+0.03, 1.01, 'walnut_v')
box(2.475, DH, 0.17, 2.50, DH+0.03, 1.01, 'walnut_z')

# TV + floating walnut shelf (two tiers)
setg('tv')
TVX = 1.24
box(TVX-0.62, 0.95, 1.175, TVX+0.62, 1.66, 1.205, 'black')
box(TVX-0.605, 0.965, 1.205, TVX+0.605, 1.645, 1.207, 'tvimg', noshadow=True)
box(TVX-0.95, 0.40, 1.175, TVX+0.95, 0.44, 1.52, 'walnut_h')
box(TVX-0.95, 0.12, 1.175, TVX+0.95, 0.16, 1.52, 'walnut_h')
box(TVX-0.95, 0.12, 1.48, TVX-0.91, 0.44, 1.52, 'walnut_v'); box(TVX+0.91, 0.12, 1.48, TVX+0.95, 0.44, 1.52, 'walnut_v')
box(TVX+0.30, 0.16, 1.25, TVX+0.62, 0.22, 1.45, 'black')       # small player
cyl((TVX-0.6, 0.44, 1.35), (TVX-0.6, 0.66, 1.35), 0.07, 'vase')
for i in range(5):
    box(TVX-0.35+i*0.04, 0.44, 1.22, TVX-0.32+i*0.04, 0.68+0.03*(i % 2), 1.40, ['book1', 'book2', 'book3'][i % 3])

# north alcove x 2.475-4.12: lit niche in the north wall, walnut frame
setg('shell')
setg('niche')
box(NX1, NY1, -ND, NX2, NY1+0.02, 0.0, 'walnut_h')
box(NX1-0.03, NY1-0.03, 0.0, NX2+0.03, NY1, 0.025, 'walnut_h'); box(NX1-0.03, NY2, 0.0, NX2+0.03, NY2+0.03, 0.025, 'walnut_h')
box(NX1-0.03, NY1, 0.0, NX1, NY2, 0.025, 'walnut_v'); box(NX2, NY1, 0.0, NX2+0.03, NY2, 0.025, 'walnut_v')
box(NX1+0.02, NY2-0.025, -0.06, NX2-0.02, NY2-0.015, -0.01, 'led', noshadow=True)
light(((NX1+NX2)/2, NY2-0.04, -0.06), 0.7, d=(0, -1, 0.05), inner=55, outer=88, rad=0.12)
cyl((3.15, NY1+0.02, -0.08), (3.15, NY1+0.26, -0.08), 0.06, 'vase')
box(3.35, NY1+0.02, -0.12, 3.55, NY1+0.06, -0.03, 'book2')

# toilet wall (x 4.12-4.20, z 0-0.955) with door (z 0.05-0.64) + walnut door
setg('shell')
box(4.12, 0, 0.64, 4.20, CH, 1.03, 'conc')
box(4.12, DH, 0.0, 4.20, CH, 0.64, 'conc')
box(4.12, 0, 0.955, 5.595, CH, 1.03, 'conc')                    # toilet south wall
setg('door_t')
box(4.11, 0, 0.03, 4.13, DH, 0.62, 'walnut_v')                  # door leaf (closed), LDK face
box(4.09, 0, 0.0, 4.12, DH+0.03, 0.03, 'walnut_v'); box(4.09, 0, 0.62, 4.12, DH+0.03, 0.65, 'walnut_v')
box(4.09, DH, 0.0, 4.12, DH+0.03, 0.65, 'walnut_z')
cyl((4.11, 1.0, 0.12), (4.06, 1.0, 0.12), 0.01, 'black'); cyl((4.06, 1.0, 0.12), (4.06, 1.0, 0.24), 0.01, 'black')

# 脱衣所 west wall (x 4.835-4.91, z 1.03-2.635) with 700 sliding door (z 1.69-2.39)
setg('shell')
box(4.835, 0, 1.03, 4.91, CH, 1.69, 'conc')
box(4.835, 0, 2.39, 4.91, CH, 2.71, 'conc')
box(4.835, DH, 1.69, 4.91, CH, 2.39, 'conc')
box(4.835, 0, 2.635, X_W, CH, 2.71, 'conc')                     # wall 脱衣所 | 玄関・hall
setg('door_d')
box(4.80, 0, 1.66, 4.825, DH-0.01, 2.40, 'walnut_v')            # sliding leaf on the LDK side (closed)
box(4.80, DH-0.01, 1.60, 4.835, DH+0.03, 2.45, 'black')         # top rail
box(4.78, 1.0, 1.70, 4.80, 1.30, 1.72, 'black')                  # bar pull

# kitchen: 180 partition (x 2.39-2.57), counter wall (腰壁) + walnut bar top
setg('shell')
box(2.39, 0, 2.636, 2.57, CH, Z_S, 'conc')
setg('counter')
box(2.57, 0, 2.636, 4.169, 0.98, 2.818, 'conc')                  # 腰壁 H980
box(2.57, 0.98, 2.336, 4.20, 1.02, 2.84, 'walnut_h')             # bar counter top (overhang 300 to the LDK)
def stool(x, z):
    cyl((x, 0.66, z), (x, 0.69, z), 0.165, 'walnut')
    for k in range(4):
        a = k*math.pi/2 + math.pi/4
        cyl((x+0.10*math.cos(a), 0.66, z+0.10*math.sin(a)), (x+0.19*math.cos(a), 0, z+0.19*math.sin(a)), 0.011, 'black')
    for k in range(4):
        a1, a2 = k*math.pi/2 + math.pi/4, (k+1)*math.pi/2 + math.pi/4
        cyl((x+0.165*math.cos(a1), 0.26, z+0.165*math.sin(a1)), (x+0.165*math.cos(a2), 0.26, z+0.165*math.sin(a2)), 0.008, 'black')
setg('stools')
for x in (2.95, 3.40, 3.85):
    stool(x, 2.10)
box(3.62, 1.02, 2.50, 3.84, 1.03, 2.66, 'book2'); cyl((3.35, 1.02, 2.52), (3.35, 1.10, 2.52), 0.04, 'vase')
cyl((2.80, 1.02, 2.55), (2.80, 1.24, 2.55), 0.055, 'vase')

# kitchen run along the south wall (z 3.835-4.435, x 2.57-5.62)
setg('kitchen')
KZ, KH = 3.835, 0.85
box(2.57, 0, KZ+0.06, 4.37, 0.08, Z_S, 'blackmatte')             # plinth
box(2.57, 0.08, KZ, 4.37, KH-0.03, Z_S, 'kitchen_d')
for xs in (2.57, 3.17, 3.77):
    box(xs+0.002, 0.08, KZ-0.002, xs+0.003, KH-0.03, KZ, 'black')
box(2.57, KH-0.03, KZ-0.02, 4.37, KH, Z_S, 'stainless')           # stainless top
box(3.40, KH-0.18, KZ+0.08, 4.10, KH, 4.30, 'stainless')          # sink bowl (reads as a recess)
box(3.42, KH-0.001, KZ+0.10, 4.08, KH+0.0005, 4.28, 'steel', noshadow=True)
cyl((3.75, KH, 4.36), (3.75, KH+0.32, 4.36), 0.013, 'black'); cyl((3.75, KH+0.32, 4.36), (3.75, KH+0.32, 4.16), 0.012, 'black')
box(2.62, KH, KZ+0.06, 3.12, KH+0.006, 4.36, 'screen')            # IH hob
box(2.57, 1.55, 4.10, 3.17, 1.80, Z_S, 'black')                   # slim range hood
box(2.57, KH, Z_S-0.012, 4.37, 1.55, Z_S, 'walnut_h')             # walnut back panel
# レンジ台 (x 4.37-5.10) + microwave, fridge (x 5.10-5.62)
box(4.37, 0, KZ, 5.10, 0.90, Z_S, 'kitchen_d')
box(4.37, 0.90, KZ, 5.10, 0.93, Z_S, 'walnut_h')
rr((4.73, 1.10, 4.10), (0.24, 0.17, 0.19), 'black', r=0.01)
box(4.37, 1.50, KZ+0.15, 5.10, 1.53, Z_S, 'walnut_h')             # open shelf
cyl((4.55, 1.53, 4.2), (4.55, 1.68, 4.2), 0.05, 'vase')
rr((5.36, 0.91, 4.12), (0.255, 0.91, 0.30), 'fridge', r=0.01)      # fridge (black)
cyl((5.13, 1.10, KZ+0.17), (5.13, 1.55, KZ+0.17), 0.008, 'steel')
# hall shoe cabinet (x 5.035-5.74, z 2.71-3.06), floating with under-light
setg('shoe')
box(5.035, 0.20, 2.71, 5.74, 1.05, 3.06, 'walnut_h')
cyl((5.25, 1.05, 2.88), (5.25, 1.30, 2.88), 0.05, 'vase')

# 玄関 (x 5.88-6.98, z 2.71-4.435): 土間 150 lower, walnut 框, steel entrance door on the east wall
setg('shell')
box(5.88, -0.30, 2.71, X_W, -0.15, Z_S, 'mortar')                # 土間 (150 below the floor)
box(5.88, -0.30, 2.635, X_W, 0.0, 2.71, 'conc')                   # wall base down to the 土間
setg('genkan')
box(5.86, -0.15, 2.71, 5.90, 0.003, Z_S, 'walnut_z')              # 上がり框
setg('shell')
box(X_W, DH-0.15, DZ1, X_W+T, CH, DZ2, 'conc')
box(X_W+0.04, -0.30, DZ1, X_W+T, DH-0.15, DZ2, 'blackmatte')   # behind the door
setg('door_e')
box(X_W-0.02, -0.15, DZ1, X_W+0.02, DH-0.15, DZ2, 'steeldoor')
cyl((X_W-0.02, 0.85, DZ1+0.08), (X_W-0.09, 0.85, DZ1+0.08), 0.012, 'steel')
cyl((X_W-0.09, 0.85, DZ1+0.08), (X_W-0.09, 0.85, DZ1+0.22), 0.012, 'steel')
box(X_W-0.04, DH-0.18, DZ1-0.03, X_W, DH-0.12, DZ2+0.03, 'black')
# 玄関 cut the floor slab: lower the genkan floor box region by covering slab top
# (the floor slab top at y=0 is hidden under the mortar block, so leave it)
box(6.20, 0.45, Z_S-0.025, 6.70, 1.95, Z_S, 'walnut_v')          # tall mirror, walnut frame
box(6.23, 0.48, Z_S-0.03, 6.67, 1.92, Z_S-0.025, 'mirror')
setg('genkan_plant')

# 脱衣所 + washer nook: tile floor, washer, walnut shelf, towels, bath door (east)
setg('wet')
box(4.91, 0.0, 0.955, 5.81, 0.004, 1.20, 'tile'); box(4.91, 0.0, 1.20, X_W, 0.004, 2.635, 'tile')
box(4.20, 0.0, 0.0, 5.595, 0.004, 0.955, 'tile')
rr((5.35, 0.43, 1.32), (0.30, 0.43, 0.30), 'wash', r=0.02)      # washer
cyl((5.35, 0.70, 1.62), (5.35, 0.70, 1.625), 0.15, 'glass', noshadow=True)
box(4.91, 1.25, 1.00, 5.81, 1.28, 1.40, 'walnut_h')
box(4.91, 1.70, 1.00, 5.81, 1.73, 1.40, 'walnut_h')
for i, x in enumerate((5.05, 5.30, 5.55)):
    box(x-0.10, 1.28, 1.08, x+0.10, 1.44, 1.32, 'towel' if i != 1 else 'basket')
# vanity on the east wall (x 6.38-6.98, z 1.35-2.25) — not on the plan, standard for a 脱衣所
box(6.43, 0.25, 1.35, X_W, 0.80, 2.25, 'walnut_z')
box(6.40, 0.80, 1.33, X_W, 0.84, 2.27, 'walnut_z')
ell((6.70, 0.86, 1.80), (0.18, 0.04, 0.24), np.eye(3), 'ceramic')
cyl((6.93, 0.84, 1.80), (6.93, 1.10, 1.80), 0.012, 'black'); cyl((6.93, 1.10, 1.80), (6.80, 1.10, 1.80), 0.011, 'black')
box(X_W-0.02, 1.05, 1.45, X_W, 1.85, 2.15, 'mirror')               # mirror (glass over dark)
# towel bar on the south wall
cyl((5.40, 1.20, 2.62), (6.10, 1.20, 2.62), 0.01, 'black')
box(5.55, 0.80, 2.60, 5.95, 1.21, 2.625, 'towel')

# toilet (x 4.20-5.595, z 0-0.955): walnut accent on the east wall, tankless toilet facing west
setg('toilet')
box(5.575, 0.0, 0.0, 5.595, CH, 0.955, 'walnut_v')
rr((5.33, 0.20, 0.48), (0.24, 0.20, 0.19), 'ceramic', r=0.06)
ell((5.20, 0.40, 0.48), (0.30, 0.04, 0.20), np.eye(3), 'ceramic')
rr((5.48, 0.55, 0.48), (0.09, 0.15, 0.19), 'ceramic', r=0.04)
box(4.70, 0.95, 0.0, 5.575, 0.98, 0.18, 'walnut_h')              # walnut shelf on the north wall
cyl((5.00, 0.98, 0.09), (5.00, 1.15, 0.09), 0.04, 'vase')
box(5.20, 0.98, 0.04, 5.40, 1.16, 0.14, 'book2')
cyl((4.95, 0.70, 0.94), (5.08, 0.70, 0.94), 0.055, 'towel')       # paper holder roll
box(4.92, 0.76, 0.93, 5.11, 0.77, 0.955, 'black')

# window: aluminium sliding frame + glass, walnut casing (balcony beyond)
setg('window')
for (z1, z2) in ((WZ1, WZ1+0.05), (WZ2-0.05, WZ2), ((WZ1+WZ2)/2-0.025, (WZ1+WZ2)/2+0.025)):
    box(-0.10, 0, z1, -0.02, WH, z2, 'alu')
box(-0.10, WH-0.05, WZ1, -0.02, WH, WZ2, 'alu'); box(-0.10, 0, WZ1, -0.02, 0.04, WZ2, 'alu')
box(-0.07, 0.04, WZ1+0.05, -0.06, WH-0.05, WZ2-0.05, 'glass', noshadow=True)
box(-0.02, 0, WZ1-0.03, 0.01, WH+0.03, WZ1, 'walnut_v'); box(-0.02, 0, WZ2, 0.01, WH+0.03, WZ2+0.03, 'walnut_v')
box(-0.02, WH, WZ1-0.03, 0.01, WH+0.03, WZ2+0.03, 'walnut_z')
setg('outside')
box(-1.6, -0.12, 0.0, -0.1, -0.10, 4.4, 'parapet')               # balcony floor
box(-1.6, -0.12, 0.0, -1.45, 1.10, 4.4, 'parapet')               # balcony wall
box(-1.6, -0.12, 0.0, -0.1, 1.10, 0.15, 'parapet'); box(-1.6, -0.12, 4.25, -0.1, 1.10, 4.4, 'parapet')
box(-14, -6, -6, -13.8, 14, 10, 'sky', noshadow=True)
box(-14, 9, -6, 0.2, 9.2, 10, 'sky', noshadow=True)
for (z1, z2, h, m) in ((-3.0, 1.2, 4.6, 'bldg'), (1.6, 4.0, 6.5, 'bldg2'), (4.4, 8.0, 3.2, 'bldg')):
    box(-11.5, -6, z1, -7.5, h, z2, m, noshadow=True)
light((-6.0, 6.0, 2.5), 26.0, d=(1, -0.55, 0.05), inner=40, outer=75, rad=1.5, col=DAY)

# ceiling beams over the LDK with walnut edge and black track spots (as in the reference)
setg('ceiling')
BD = 0.22
for (z1, z2) in ((1.175, 1.575), (2.236, 2.636)):
    box(0, CH-BD, z1, 4.835 if z1 > 2 else 4.12, CH, z2, 'conc_c')
    box(0, CH-BD-0.012, z1-0.012, 4.835 if z1 > 2 else 4.12, CH-BD, z1, 'walnut_h')
    box(0, CH-BD-0.012, z2, 4.835 if z1 > 2 else 4.12, CH-BD, z2+0.012, 'walnut_h')
    zc = (z1+z2)/2
    box(0.3, CH-BD-0.035, zc-0.018, 4.0, CH-BD, zc+0.018, 'black')
def spot(x, y, z, aim, I=3.2, inner=12, outer=30):
    a = np.array(aim, float) - np.array([x, y, z]); a /= np.linalg.norm(a)
    p0 = np.array([x, y, z]); p1 = p0 + a*0.13
    cyl(tuple(p0 - a*0.0), tuple(p1), 0.032, 'black', noshadow=True)
    cyl(tuple(p1 - a*0.003), tuple(p1 + a*0.001), 0.024, 'spot_lens', noshadow=True)
    light(tuple(p1 + a*0.02), I, d=tuple(a), inner=inner, outer=outer, rad=0.02)
y0 = CH-BD-0.07
for x in (0.7, 1.5, 2.3, 3.1, 3.8):
    spot(x, y0, 1.375, (x, 0.9, 1.20 if x < 2.4 else 0.6))            # wash the TV wall / alcove
for x in (0.7, 1.6):
    spot(x, y0, 2.436, (x-0.2, 0, 3.4))
for x in (2.9, 3.4, 3.9):
    spot(x, y0, 2.436, (x, 1.0, 2.55), I=2.6)                        # onto the bar counter
spot(4.5, y0, 2.436, (4.6, 0, 3.0))
# kitchen + hall + genkan + wet rooms: small downlights
def downlight(x, z, I=3.0, inner=20, outer=50, col=WARM):
    cyl((x, CH-0.004, z), (x, CH, z), 0.05, 'black', noshadow=True)
    cyl((x, CH-0.006, z), (x, CH-0.003, z), 0.033, 'spot_lens', noshadow=True)
    light((x, CH-0.03, z), I, inner=inner, outer=outer, col=col)
downlight(3.10, 3.55, 2.6, col=NEUT); downlight(4.30, 3.55, 2.6, col=NEUT); downlight(5.35, 3.45, 2.2)
downlight(5.30, 3.10, 1.4); downlight(6.43, 3.55, 1.8); downlight(3.05, 0.55, 0.9, outer=38)
downlight(5.95, 1.95, 1.5, col=NEUT); downlight(5.35, 1.25, 1.0, col=NEUT)
downlight(4.80, 0.48, 1.2)
# wall AC on the kitchen partition (LDK side), above the window head line
box(2.17, 2.10, 2.95, 2.39, 2.40, 3.80, 'ac')
box(2.165, 2.12, 3.0, 2.17, 2.16, 3.75, 'black')

# plants (monstera)
def monstera(x, z, h=1.0, seed=1, pr=0.17):
    r = random.Random(seed)
    cyl((x, 0, z), (x, 0.40, z), pr, 'potc')
    cyl((x, 0.39, z), (x, 0.405, z), pr-0.02, 'soil')
    for i in range(12):
        a = r.random()*2*math.pi; rad = r.uniform(0.10, 0.40); hy = 0.40 + r.uniform(0.35, h)
        tip = np.array((x+math.cos(a)*rad, hy, z+math.sin(a)*rad))
        cyl((x, 0.40, z), tuple(tip), 0.007, 'stem')
        s = r.uniform(0.12, 0.18)
        tilt = r.uniform(0.35, 0.9)                     # leaves droop outward
        R = Ry(-a) @ Rz(-tilt) @ Rx(r.uniform(-0.25, 0.25))
        fwd = R @ np.array([1.0, 0, 0]); side = R @ np.array([0, 0, 1.0])
        m = r.choice(('leaf1', 'leaf2'))
        for sg in (-1, 1):                              # two lobes = heart / split-leaf silhouette
            c = tip + fwd*s*0.85 + side*sg*s*0.36
            ell(tuple(c), (s*0.92, 0.005, s*0.52), R @ Ry(sg*0.32), m)
        cyl(tuple(tip), tuple(tip + fwd*s*1.7), 0.004, 'stem')


setg('plant_w')
monstera(0.45, 3.75, h=0.9, seed=3)
setg('plant_n')
monstera(2.20, 1.62, h=0.75, seed=5, pr=0.15)
setg('plant_g')
# (genkan plant removed: leaves crossed into the 脱衣所)


# ============================================================================ views
def yaw_to(cx, cz, tx, tz):
    return math.atan2(tx - cx, -(tz - cz))
def view(cx, cz, tx, tz, fov, drop=(), cy=1.25, sy=-0.05):
    return dict(cam=(cx, cy, cz, yaw_to(cx, cz, tx, tz), fov, 0.0, sy), drop=set(drop))

VIEWS = {
    # LDK
    'ldk_1': view(4.40, 1.90, 0.0, 2.60, 80),                     # toward the balcony window: counter left, TV wall right
    'ldk_2': view(1.35, 3.95, 1.45, 0.0, 80, drop={'plant_w'}),   # TV wall straight on (reference composition)
    'ldk_3': view(0.45, 1.45, 3.9, 3.7, 80, drop={'plant_n'}),    # from the window toward bar counter + kitchen
    'ldk_4': view(3.55, 1.70, 3.45, 4.435, 82, cy=1.50, sy=-0.25),           # kitchen from the hall
    # 脱衣所
    'datsui_1': view(6.25, 2.50, 4.95, 1.05, 96, sy=-0.40),
    'datsui_2': view(5.00, 1.75, 6.98, 2.50, 96, sy=-0.40),
    'datsui_3': view(5.05, 2.48, 6.98, 1.35, 96, sy=-0.40),
    'datsui_4': view(6.30, 1.75, 4.85, 2.70, 92, sy=-0.40),
    # 玄関
    'genkan_1': view(5.20, 3.35, 6.98, 3.55, 84, cy=1.30, sy=-0.35),   # from the hall to the entrance door
    'genkan_2': view(6.80, 3.70, 3.4, 2.4, 84, cy=1.15),               # from the door into the house
    'genkan_3': view(6.75, 4.30, 5.2, 2.75, 88, cy=1.15),              # shoe cabinet + hall
    'genkan_4': view(5.75, 4.30, 6.98, 2.80, 88, cy=1.30, sy=-0.35),   # 框, door and shoe cabinet from the kitchen side
    # トイレ
    'toilet_1': view(4.25, 0.48, 5.60, 0.48, 96, sy=-0.65),
    'toilet_2': view(5.42, 0.85, 4.20, 0.20, 100, sy=-0.45),
    'toilet_3': view(4.30, 0.25, 5.60, 0.95, 100, sy=-0.55),
    'toilet_4': view(5.42, 0.30, 4.20, 0.95, 100, sy=-0.55),
}
ENV = (0.6, 0.62, 0.66)
