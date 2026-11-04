"""Builds the salon scene for the path tracer. Units: metres.
x = east (0..7.84), z = south (0..3.5), y = up. North wall at z=0, west wall at x=0.
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

# --- materials (from the finish board: ivory diatomite cloth, oak board wainscot, oak floor tile, oak fittings)
mat('plaster', (236, 229, 214), tex=3, bump=1.0)
mat('ceiling', (240, 237, 231), tex=3)
mat('floor', (166, 128, 92), tex=1, ks=0.035, ex=90)
mat('wains', (146, 108, 76), tex=2, ks=0.03, ex=40)
mat('oak', (160, 120, 84), tex=4, ks=0.035, ex=45)
mat('oak_h', (160, 120, 84), tex=4, ks=0.035, ex=45, axis=0)
mat('oak_hz', (160, 120, 84), tex=4, ks=0.035, ex=45, axis=2)
mat('oak_v', (160, 120, 84), tex=4, ks=0.035, ex=45, axis=1)
mat('darkwood', (104, 74, 52), tex=4, ks=0.04, ex=50, axis=0)
mat('door', (118, 84, 58), tex=4, ks=0.04, ex=50, axis=1)
mat('trim', (92, 64, 44), tex=4, ks=0.04, ex=50)
mat('white', (238, 236, 231), ks=0.04, ex=120)
mat('ceramic', (242, 241, 238), ks=0.06, ex=600)
mat('quartz', (232, 230, 225), ks=0.05, ex=300)
mat('black', (26, 25, 24), ks=0.05, ex=90)
mat('blackmatte', (30, 29, 28), ks=0.02, ex=20)
mat('leather', (48, 36, 31), tex=7, ks=0.05, ex=35)
mat('leather_blk', (30, 27, 26), tex=7, ks=0.05, ex=35)
mat('chrome', (200, 200, 198), typ=4, ex=1500)
mat('steel', (170, 170, 168), typ=4, ex=180)
mat('mirror', (226, 230, 230), typ=1)
mat('glass', (232, 240, 238), typ=2)
mat('frosted', (205, 210, 212), emit=srgb(60, 70, 85), ks=0.04, ex=200)
mat('picture', (255, 255, 255), tex=5, ks=0.02, ex=60)
mat('checker', (255, 255, 255), tex=6, ks=0.06, ex=300)
mat('soil', (45, 34, 26))
mat('leaf1', (52, 92, 44), ks=0.06, ex=60)
mat('leaf2', (70, 108, 52), ks=0.06, ex=60)
mat('leaf3', (40, 74, 38), ks=0.06, ex=60)
mat('stem', (90, 70, 50))
mat('amber', (120, 66, 26), ks=0.08, ex=400)
mat('bottle_w', (230, 228, 222), ks=0.06, ex=200)
mat('bottle_k', (34, 32, 30), ks=0.08, ex=300)
mat('cap', (180, 150, 100), typ=4, ex=300)
mat('book1', (190, 180, 160), tex=8)
mat('book2', (90, 100, 95), tex=8)
mat('book3', (150, 120, 90), tex=8)
mat('downlight', (255, 255, 255), emit=(12.0, 9.0, 6.0), lin=False)
mat('shade', (240, 220, 190), emit=(1.6, 1.05, 0.55))
mat('ac', (236, 235, 232), ks=0.03, ex=40)
mat('grille', (150, 150, 148))
mat('pot', (226, 222, 214), ks=0.05, ex=80)
mat('concrete', (150, 146, 140))

PRIMS, LIGHTS = [], []
GROUP = ['shell']
def setg(g): GROUP[0] = g

def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def flags(noshadow=False):
    return (1 if noshadow else 0) | (2 if GROUP[0] == 'shell' else 0)

def box(x1, y1, z1, x2, y2, z2, m, noshadow=False):
    x1, x2 = min(x1, x2), max(x1, x2); y1, y2 = min(y1, y2), max(y1, y2); z1, z2 = min(z1, z2), max(z1, z2)
    c = ((x1+x2)/2, (y1+y2)/2, (z1+z2)/2); h = ((x2-x1)/2, (y2-y1)/2, (z2-z1)/2)
    PRIMS.append((GROUP[0], 'box', c, h, np.eye(3), NAMES[m], flags(noshadow)))

def rbox(c, h, R, m, noshadow=False):
    PRIMS.append((GROUP[0], 'box', tuple(c), tuple(h), np.array(R), NAMES[m], flags(noshadow)))

def cyl(p0, p1, r, m, noshadow=False):
    PRIMS.append((GROUP[0], 'cyl', tuple(p0), tuple(p1), r, NAMES[m], flags(noshadow)))

def ell(c, radii, R, m, noshadow=False):
    S_inv = np.diag([1/radii[0], 1/radii[1], 1/radii[2]])
    M = S_inv @ np.array(R).T
    PRIMS.append((GROUP[0], 'ell', tuple(c), M, max(radii), NAMES[m], flags(noshadow)))

WARM = (1.0, 0.70, 0.42)
def light(p, I, d=(0, -1, 0), inner=22, outer=48, rad=0.035, up=0.0, col=WARM):
    LIGHTS.append((GROUP[0], p, d, (I*col[0], I*col[1], I*col[2]), inner, outer, rad, up))

H = 2.4
# ============================== shell =====================================
setg('shell')
T = 0.12
box(-T, -T, -T, 7.84+T, 0, 3.5+T, 'floor')
box(-T, H, -T, 7.84+T, H+T, 3.5+T, 'ceiling')
box(-T, 0, -T, 7.84+T, H, 0, 'plaster')               # north
box(-T, 0, 0, 0, H, 3.5+T, 'plaster')                  # west
box(0, 0, 3.5, 6.76+T, H, 3.5+T, 'plaster')            # south
box(6.76, 0, 1.37, 6.76+T, H, 3.5+T, 'plaster')        # east (salon)
box(6.76, 0, 1.37, 7.84+T, H, 1.37+T, 'plaster')       # niche south
box(7.84, 0, -T, 7.84+T, H, 1.37+T, 'plaster')         # niche east

def wainscot_x(x1, x2, z, side):  # wall along x at z; side=+1 means room is +z
    zz = z + side*0.014
    box(x1, 0, z, x2, 0.9, zz, 'wains')
    box(x1, 0.9, z, x2, 0.93, z + side*0.03, 'trim')
    box(x1, 0, z, x2, 0.075, z + side*0.024, 'trim')
def wainscot_z(z1, z2, x, side):
    xx = x + side*0.014
    box(x, 0, z1, xx, 0.9, z2, 'wains')
    box(x, 0.9, z1, x + side*0.03, 0.93, z2, 'trim')
    box(x, 0, z1, x + side*0.024, 0.075, z2, 'trim')

wainscot_x(0, 7.84, 0, +1)
wainscot_z(0, 3.5, 0, +1)
wainscot_x(0, 6.76, 3.5, -1)
wainscot_z(1.37, 3.5, 6.76, -1)
wainscot_x(6.76, 7.84, 1.37, -1)
wainscot_z(0, 1.37, 7.84, -1)

# ceiling downlight trims (geometry only; their light is defined per zone)
def downlight(x, z, I=7.0, inner=20, outer=46, d=(0, -1, 0), grp=None):
    g = GROUP[0]
    if grp: setg(grp)
    cyl((x, H-0.004, z), (x, H, z), 0.055, 'white', noshadow=True)
    cyl((x, H-0.006, z), (x, H-0.003, z), 0.038, 'downlight', noshadow=True)
    light((x, H-0.03, z), I, d=d, inner=inner, outer=outer)
    setg(g)

setg('ceiling')
for x in (1.45, 2.65, 3.9, 5.15, 6.35):
    downlight(x, 0.36, I=6.0, inner=14, outer=36)
downlight(7.52, 0.75, I=4.5)
for z in (1.55, 2.4, 3.2):
    downlight(0.36, z, I=5.5, inner=14, outer=36)
downlight(6.38, 1.95, I=5.0)
downlight(6.38, 3.0, I=4.5)
downlight(2.2, 1.55, I=4.0, outer=55)
downlight(5.2, 1.65, I=4.0, outer=55)
# ceiling cassette air conditioner
box(3.37, H-0.035, 1.44, 4.21, H, 2.28, 'ac')
box(3.55, H-0.037, 1.62, 4.03, H-0.035, 2.10, 'grille')
for i in range(4):
    a, b = (3.43, 1.50+i*0.0), None
box(3.42, H-0.037, 1.49, 4.16, H-0.036, 1.55, 'grille')
box(3.42, H-0.037, 2.17, 4.16, H-0.036, 2.23, 'grille')
box(3.42, H-0.037, 1.55, 3.48, H-0.036, 2.17, 'grille')
box(4.10, H-0.037, 1.55, 4.16, H-0.036, 2.17, 'grille')

rnd = random.Random(7)

def leaves(cx, cy, cz, n, spread, height, size=0.07, droop=0.0, seed=0, mats=('leaf1', 'leaf2', 'leaf3')):
    r = random.Random(seed)
    for i in range(n):
        a = r.random()*2*math.pi; rr = spread*math.sqrt(r.random())
        y = cy + r.random()*height - droop*rr
        R = Ry(r.random()*2*math.pi) @ Rz(r.uniform(-0.9, 0.9)) @ Rx(r.uniform(-0.6, 0.6))
        s = size*r.uniform(0.7, 1.25)
        ell((cx+math.cos(a)*rr, y, cz+math.sin(a)*rr), (s, 0.006, s*0.45), R, r.choice(mats))

def bottle(x, z, y0, h, r, m, capm='cap'):
    cyl((x, y0, z), (x, y0+h*0.78, z), r, m)
    cyl((x, y0+h*0.78, z), (x, y0+h*0.9, z), r*0.45, m)
    cyl((x, y0+h*0.9, z), (x, y0+h, z), r*0.5, capm)

# ============================== north wall ================================
setg('plant')
cyl((0.55, 0, 0.42), (0.55, 0.40, 0.42), 0.17, 'pot')
cyl((0.55, 0.38, 0.42), (0.55, 0.405, 0.42), 0.155, 'soil')
cyl((0.55, 0.4, 0.42), (0.53, 1.0, 0.43), 0.014, 'stem')
cyl((0.53, 1.0, 0.43), (0.47, 1.45, 0.40), 0.01, 'stem')
cyl((0.53, 0.95, 0.43), (0.66, 1.3, 0.48), 0.008, 'stem')
leaves(0.53, 0.85, 0.44, 150, 0.28, 0.75, size=0.055, seed=3)

setg('reji')
box(1.06, 0.06, 0.05, 1.79, 1.0, 0.62, 'darkwood')
box(1.09, 0, 0.08, 1.76, 0.06, 0.58, 'blackmatte')
box(1.03, 1.0, 0.03, 1.82, 1.035, 0.65, 'oak_h')
for y in (0.31, 0.56, 0.81):
    box(1.06, y, 0.62, 1.79, y+0.004, 0.623, 'trim')
rbox((1.33, 1.13, 0.36), (0.12, 0.085, 0.006), Ry(0) @ Rx(-0.35), 'black')
cyl((1.33, 1.035, 0.38), (1.33, 1.07, 0.38), 0.04, 'steel')
box(1.55, 1.035, 0.40, 1.62, 1.05, 0.52, 'black')
bottle(1.70, 0.18, 1.035, 0.14, 0.04, 'pot', capm='pot')
leaves(1.70, 1.17, 0.18, 14, 0.06, 0.10, size=0.035, seed=9)

setg('shelf')
X1, X2, Y1 = 1.95, 3.42, 1.55
box(X1, Y1, 0.0, X2, Y1+0.025, 0.28, 'oak_h')
box(X1, Y1+0.32, 0.0, X2, Y1+0.345, 0.28, 'oak_h')
box(X1, Y1, 0.0, X1+0.025, Y1+0.345, 0.28, 'oak_v')
box(X2-0.025, Y1, 0.0, X2, Y1+0.345, 0.28, 'oak_v')
cols = ['amber', 'bottle_w', 'bottle_k', 'amber', 'bottle_w', 'bottle_w', 'bottle_k', 'amber', 'bottle_w', 'bottle_k', 'amber']
xs = np.linspace(2.35, 3.33, len(cols))
for i, (x, m) in enumerate(zip(xs, cols)):
    bottle(x, 0.14, Y1+0.025, 0.16+0.06*((i*7) % 3)/2, 0.028, m)
# trailing plant on the shelf
cyl((2.12, Y1+0.025, 0.14), (2.12, Y1+0.14, 0.14), 0.07, 'pot')
leaves(2.12, Y1-0.45, 0.17, 70, 0.14, 0.62, size=0.04, seed=21)

setg('sink')
box(3.55, 0.07, 0.03, 4.35, 0.84, 0.62, 'oak_v')
box(3.58, 0, 0.06, 4.32, 0.07, 0.58, 'blackmatte')
box(3.947, 0.09, 0.62, 3.953, 0.82, 0.623, 'trim')
for x in (3.90, 4.00):
    box(x, 0.62, 0.62, x+0.012, 0.76, 0.64, 'black')
# counter top with basin opening
box(3.53, 0.84, 0.02, 4.37, 0.875, 0.16, 'quartz')
box(3.53, 0.84, 0.50, 4.37, 0.875, 0.64, 'quartz')
box(3.53, 0.84, 0.16, 3.76, 0.875, 0.50, 'quartz')
box(4.14, 0.84, 0.16, 4.37, 0.875, 0.50, 'quartz')
box(3.76, 0.70, 0.16, 4.14, 0.71, 0.50, 'steel')
box(3.76, 0.71, 0.16, 3.765, 0.84, 0.50, 'steel')
box(4.135, 0.71, 0.16, 4.14, 0.84, 0.50, 'steel')
box(3.76, 0.71, 0.16, 4.14, 0.84, 0.165, 'steel')
box(3.76, 0.71, 0.495, 4.14, 0.84, 0.50, 'steel')
cyl((3.95, 0.875, 0.09), (3.95, 1.16, 0.09), 0.014, 'black')
cyl((3.95, 1.16, 0.09), (3.95, 1.16, 0.29), 0.012, 'black')
cyl((3.95, 1.16, 0.29), (3.95, 1.10, 0.29), 0.012, 'black')
cyl((3.95, 1.0, 0.09), (4.05, 1.02, 0.09), 0.007, 'black')
bottle(4.25, 0.10, 0.875, 0.18, 0.03, 'bottle_k')

setg('shampoo')
# stylist stool
cyl((4.88, 0, 0.78), (4.88, 0.03, 0.78), 0.2, 'chrome')
cyl((4.88, 0.03, 0.78), (4.88, 0.5, 0.78), 0.03, 'chrome')
cyl((4.88, 0.5, 0.78), (4.88, 0.57, 0.78), 0.19, 'leather_blk')
# reclining shampoo chair (head to the east, onto the bowl)
box(5.62, 0, 0.56, 6.12, 0.06, 0.84, 'chrome')
box(5.72, 0.06, 0.60, 6.02, 0.30, 0.80, 'black')
box(5.32, 0.30, 0.45, 6.02, 0.40, 0.95, 'black')
rbox((5.67, 0.45, 0.70), (0.35, 0.055, 0.25), np.eye(3), 'leather_blk')
rbox((6.24, 0.62, 0.70), (0.27, 0.045, 0.235), Rz(math.radians(30)), 'leather_blk')
rbox((5.14, 0.34, 0.70), (0.19, 0.04, 0.22), Rz(math.radians(-22)), 'leather_blk')
for z in (0.43, 0.97):
    box(5.45, 0.58, z-0.03, 5.98, 0.62, z+0.03, 'leather_blk')
    cyl((5.55, 0.40, z), (5.55, 0.58, z), 0.012, 'chrome')
    cyl((5.90, 0.40, z), (5.90, 0.58, z), 0.012, 'chrome')
# shampoo bowl unit
box(6.48, 0, 0.40, 6.98, 0.74, 0.98, 'black')
box(6.46, 0.74, 0.38, 7.00, 0.78, 1.00, 'ceramic')
ell((6.74, 0.84, 0.69), (0.22, 0.12, 0.27), np.eye(3), 'ceramic')
ell((6.74, 0.87, 0.69), (0.17, 0.05, 0.21), np.eye(3), 'grille')
cyl((6.92, 0.78, 0.5), (6.92, 0.98, 0.5), 0.012, 'chrome')
cyl((6.92, 0.98, 0.5), (6.84, 0.99, 0.5), 0.012, 'chrome')

setg('partition')
box(7.10, 0, 0, 7.20, H, 0.80, 'plaster')
wainscot_z(0, 0.80, 7.10, -1)
wainscot_z(0, 0.80, 7.20, +1)
box(7.08, 0, 0.80, 7.22, H, 0.815, 'plaster')

setg('towel')
box(7.28, 0.0, 0.02, 7.80, 1.95, 0.56, 'white')
box(7.536, 0.05, 0.56, 7.544, 1.9, 0.563, 'grille')
box(7.27, 1.95, 0.01, 7.81, 2.36, 0.57, 'darkwood')
box(7.536, 1.98, 0.57, 7.544, 2.33, 0.573, 'trim')
for x in (7.50, 7.57):
    box(x, 0.9, 0.56, x+0.01, 1.15, 0.58, 'chrome')

# ============================== west wall =================================
setg('entrance')
box(0, 0, 0.30, 0.045, 2.05, 1.20, 'door')
box(0, 0, 0.24, 0.03, 2.11, 0.30, 'trim')
box(0, 0, 1.20, 0.03, 2.11, 1.26, 'trim')
box(0, 2.05, 0.24, 0.03, 2.11, 1.26, 'trim')
box(0.04, 0.45, 0.52, 0.05, 1.86, 0.98, 'frosted')
cyl((0.045, 1.02, 1.09), (0.10, 1.02, 1.09), 0.012, 'black')
cyl((0.10, 1.02, 1.09), (0.10, 1.02, 0.97), 0.011, 'black')

setg('waiting')
def eames(x, z):
    ell((x, 0.45, z), (0.23, 0.04, 0.235), np.eye(3), 'black')
    ell((x-0.17, 0.63, z), (0.04, 0.17, 0.245), Rz(math.radians(-16)), 'black')
    ell((x-0.08, 0.50, z), (0.14, 0.07, 0.235), Rz(math.radians(-40)), 'black')
    for dx in (-0.14, 0.14):
        for dz in (-0.14, 0.14):
            cyl((x+dx, 0.41, z+dz), (x+dx*1.75, 0.0, z+dz*1.75), 0.013, 'oak')
    cyl((x-0.2, 0.17, z-0.2), (x+0.2, 0.17, z+0.2), 0.004, 'black')
    cyl((x-0.2, 0.17, z+0.2), (x+0.2, 0.17, z-0.2), 0.004, 'black')
    cyl((x-0.21, 0.17, z-0.21), (x-0.21, 0.17, z+0.21), 0.004, 'black')
    cyl((x+0.21, 0.17, z-0.21), (x+0.21, 0.17, z+0.21), 0.004, 'black')
eames(0.42, 1.55)
eames(0.42, 3.17)
# sideboard
Z1, Z2 = 1.94, 2.86
box(0.03, 0.6, Z1, 0.44, 0.63, Z2, 'oak_hz')
box(0.03, 0.08, Z1, 0.43, 0.60, Z1+0.025, 'oak_v')
box(0.03, 0.08, Z2-0.025, 0.43, 0.60, Z2, 'oak_v')
box(0.03, 0.40, Z1+0.025, 0.42, 0.60, Z2-0.025, 'oak_hz')
box(0.42, 0.405, Z1+0.03, 0.435, 0.595, 2.395, 'oak_hz')
box(0.42, 0.405, 2.405, 0.435, 0.595, Z2-0.03, 'oak_hz')
for zc in (2.17, 2.63):
    box(0.435, 0.49, zc-0.04, 0.445, 0.51, zc+0.04, 'trim')
box(0.03, 0.08, Z1+0.025, 0.43, 0.105, Z2-0.025, 'oak_hz')
box(0.03, 0.105, Z1+0.025, 0.045, 0.40, Z2-0.025, 'oak_hz')
for zz in (Z1+0.05, Z2-0.05):
    for xx in (0.07, 0.39):
        cyl((xx, 0, zz), (xx, 0.08, zz), 0.016, 'oak')
for i, (z0, w, m) in enumerate([(2.0, 0.24, 'book1'), (2.55, 0.24, 'book3')]):
    box(0.08, 0.105, z0, 0.36, 0.135, z0+w, m)
    box(0.09, 0.135, z0+0.01, 0.35, 0.16, z0+w-0.02, 'book2')
cyl((0.24, 0.63, 2.18), (0.24, 0.75, 2.18), 0.065, 'pot')
leaves(0.24, 0.74, 2.18, 40, 0.10, 0.20, size=0.045, seed=33)
rbox((0.12, 0.72, 2.66), (0.008, 0.09, 0.07), Rz(math.radians(-10)), 'black')
rbox((0.126, 0.72, 2.66), (0.004, 0.07, 0.05), Rz(math.radians(-10)), 'book1')
# framed landscape
box(0, 1.30, 2.02, 0.03, 1.86, 2.78, 'picture')
box(0, 1.27, 1.99, 0.038, 1.30, 2.81, 'black')
box(0, 1.86, 1.99, 0.038, 1.89, 2.81, 'black')
box(0, 1.30, 1.99, 0.038, 1.86, 2.02, 'black')
box(0, 1.30, 2.78, 0.038, 1.86, 2.81, 'black')

# ============================== east wall =================================
setg('shelf_e')
Za, Zb = 1.47, 2.42
box(6.40, 0.06, Za, 6.76, 0.86, Zb, 'oak_v')
box(6.42, 0, Za+0.03, 6.74, 0.06, Zb-0.03, 'blackmatte')
box(6.397, 0.08, 1.942, 6.40, 0.84, 1.948, 'trim')
for z in (1.90, 1.99):
    box(6.385, 0.70, z, 6.40, 0.80, z+0.01, 'black')
box(6.38, 0.86, Za-0.01, 6.76, 0.89, Zb+0.01, 'oak_hz')
box(6.40, 0.89, Za, 6.76, 2.15, Za+0.025, 'oak_v')
box(6.40, 0.89, Zb-0.025, 6.76, 2.15, Zb, 'oak_v')
box(6.73, 0.89, Za, 6.745, 2.15, Zb, 'darkwood')
box(6.40, 2.12, Za, 6.76, 2.15, Zb, 'oak_hz')
for y in (1.27, 1.68):
    box(6.42, y, Za+0.025, 6.745, y+0.025, Zb-0.025, 'oak_hz')
r = random.Random(5)
for y0 in (0.89, 1.295, 1.705):
    z = Za + 0.10
    while z < Zb - 0.12:
        kind = r.random()
        if kind < 0.18 and y0 > 1.0:
            cyl((6.56, y0, z+0.05), (6.56, y0+0.10, z+0.05), 0.05, 'pot')
            leaves(6.56, y0+0.09, z+0.05, 18, 0.07, 0.12, size=0.035, seed=int(z*100+y0*10))
            z += 0.17
        elif kind < 0.28:
            box(6.47, y0, z-0.02, 6.67, y0+0.08, z+0.12, 'book3')
            z += 0.18
        else:
            bottle(6.56, z, y0, r.uniform(0.16, 0.23), 0.03, r.choice(['amber', 'bottle_w', 'bottle_k', 'bottle_w']))
            z += 0.085

setg('door_house')
box(6.715, 0, 2.62, 6.76, 2.05, 3.42, 'door')
box(6.73, 0, 2.56, 6.76, 2.11, 2.62, 'trim')
box(6.73, 0, 3.42, 6.76, 2.11, 3.48, 'trim')
box(6.73, 2.05, 2.56, 6.76, 2.11, 3.48, 'trim')
cyl((6.715, 1.02, 2.72), (6.66, 1.02, 2.72), 0.012, 'chrome')
cyl((6.66, 1.02, 2.72), (6.66, 1.02, 2.84), 0.011, 'chrome')
box(6.71, 0.97, 2.69, 6.715, 1.12, 2.75, 'chrome')

# ============================== south wall (cut space) ====================
setg('mirrors')
for x in (4.15, 5.93):
    box(x-0.40, 1.00, 3.462, x+0.40, 2.10, 3.47, 'mirror')
    box(x-0.44, 0.96, 3.45, x+0.44, 1.00, 3.5, 'oak_h')
    box(x-0.44, 2.10, 3.45, x+0.44, 2.14, 3.5, 'oak_h')
    box(x-0.44, 1.00, 3.45, x-0.40, 2.10, 3.5, 'oak_v')
    box(x+0.40, 1.00, 3.45, x+0.44, 2.10, 3.5, 'oak_v')

setg('counter')
for a, b in ((3.38, 4.98), (5.12, 6.74)):
    box(a, 0.74, 3.15, b, 0.78, 3.486, 'oak_h')
    for x in (a+0.1, (a+b)/2, b-0.1):
        box(x-0.012, 0.58, 3.30, x+0.012, 0.74, 3.486, 'black')
for x, m in ((4.55, 'bottle_w'), (4.62, 'amber'), (6.35, 'bottle_k'), (6.42, 'bottle_w')):
    bottle(x, 3.38, 0.78, 0.17, 0.028, m)

setg('divider')
box(5.00, 0, 3.32, 5.10, 1.95, 3.486, 'oak_v')
box(5.035, 0.04, 2.52, 5.065, 1.90, 3.32, 'glass')

setg('chairs_cut')
def stylechair(x, z):
    cyl((x, 0, z), (x, 0.03, z), 0.28, 'chrome')
    cyl((x, 0.03, z), (x, 0.34, z), 0.045, 'chrome')
    cyl((x, 0.34, z), (x, 0.45, z), 0.06, 'black')
    box(x-0.28, 0.45, z-0.24, x+0.28, 0.58, z+0.27, 'leather')
    rbox((x, 0.86, z-0.27), (0.27, 0.27, 0.06), Rx(math.radians(-8)), 'leather')
    for sx in (-1, 1):
        box(x+sx*0.33-0.035, 0.62, z-0.20, x+sx*0.33+0.035, 0.70, z+0.22, 'leather')
        box(x+sx*0.33-0.012, 0.50, z+0.12, x+sx*0.33+0.012, 0.62, z+0.15, 'chrome')
        box(x+sx*0.33-0.012, 0.50, z-0.17, x+sx*0.33+0.012, 0.62, z-0.14, 'chrome')
    cyl((x-0.18, 0.22, z+0.36), (x+0.18, 0.22, z+0.36), 0.015, 'chrome')
    cyl((x, 0.38, z+0.2), (x, 0.22, z+0.36), 0.015, 'chrome')
stylechair(4.15, 2.62)
stylechair(5.93, 2.62)

setg('pendants')
for x in (4.15, 5.93):
    cyl((x, 1.97, 3.0), (x, H, 3.0), 0.004, 'black', noshadow=True)
    cyl((x, 1.80, 3.0), (x, 1.97, 3.0), 0.085, 'shade', noshadow=True)
    cyl((x, 1.965, 3.0), (x, 1.975, 3.0), 0.09, 'darkwood', noshadow=True)
    light((x, 1.78, 3.0), 3.2, inner=35, outer=80, rad=0.05, up=0.0, col=(1.0, 0.64, 0.36))

setg('toilet')
box(1.74, 0, 2.38, 1.85, H, 2.46, 'plaster')
box(2.38, 0, 2.38, 3.33, H, 2.46, 'plaster')
box(1.85, 2.05, 2.38, 2.38, H, 2.46, 'plaster')
box(1.74, 0, 2.38, 1.82, H, 3.5, 'plaster')
box(3.25, 0, 2.38, 3.33, H, 3.5, 'plaster')
for a, b in ((1.74, 1.85), (2.38, 3.33)):
    wainscot_x(a, b, 2.38, -1)
wainscot_z(2.38, 3.5, 3.33, +1)
wainscot_z(2.38, 3.5, 1.74, -1)
box(1.80, 0, 2.355, 1.85, 2.11, 2.48, 'trim')
box(2.38, 0, 2.355, 2.43, 2.11, 2.48, 'trim')
box(1.80, 2.05, 2.355, 2.43, 2.11, 2.48, 'trim')
box(1.82, 0, 2.46, 3.25, 0.004, 3.5, 'checker')
hinge = np.array([1.855, 0, 2.46])
R = Ry(math.radians(78))
rbox(hinge + R @ np.array([0.262, 1.02, 0.018]), (0.262, 1.02, 0.018), R, 'door')
hp = hinge + R @ np.array([0.47, 1.0, 0.06])
cyl(hp, hp + R @ np.array([-0.11, 0, 0]), 0.01, 'chrome')
box(2.36, 0.40, 3.30, 2.74, 0.80, 3.49, 'ceramic')
ell((2.55, 0.30, 3.10), (0.18, 0.13, 0.24), np.eye(3), 'ceramic')
cyl((2.55, 0.0, 3.16), (2.55, 0.25, 3.16), 0.12, 'ceramic')
ell((2.55, 0.43, 3.10), (0.19, 0.012, 0.25), np.eye(3), 'ceramic')
box(1.82, 0.6, 2.9, 1.84, 0.72, 3.02, 'chrome')
cyl((1.85, 0.66, 2.92), (1.85, 0.66, 3.0), 0.05, 'white')
downlight(2.55, 2.95, I=3.0, outer=60)

# ============================== export ====================================
VIEWS = {
    'north': dict(cam=(3.95, 1.22, 3.44, 0.0, 94, 0.0, -0.04),
                  drop={'chairs_cut', 'divider', 'pendants', 'counter', 'toilet'}),
    'east':  dict(cam=(3.55, 1.22, 2.05, math.pi/2, 80, 0.0, -0.04),
                  drop={'waiting', 'entrance', 'plant', 'toilet', 'chairs_cut'}),
    'west':  dict(cam=(3.35, 1.22, 1.85, -math.pi/2, 82, 0.0, -0.04),
                  drop={'shelf_e', 'chairs_cut', 'divider', 'toilet', 'sink', 'shampoo'}),
    'south': dict(cam=(4.30, 1.22, 0.10, math.pi, 86, 0.0, -0.04),
                  drop={'plant', 'reji', 'shelf', 'sink', 'shampoo', 'partition', 'towel'}),
}

def export(view, W, Hh, spp, path):
    v = VIEWS[view]
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
        elif p[1] == 'cyl':
            _, _, p0, p1, r, mi, fl = p
            out.append('cyl %f %f %f %f %f %f %f %d %d' % (*p0, *p1, r, mi, fl))
        else:
            _, _, c, M, rr, mi, fl = p
            out.append('ell %f %f %f %s %f %d %d' % (*c, ' '.join('%f' % x for x in np.array(M).reshape(-1)), rr, mi, fl))
    for l in LIGHTS:
        if l[0] in v['drop']:
            continue
        _, p, d, I, inner, outer, rad, up = l
        out.append('light %f %f %f %f %f %f %f %f %f %f %f %f %f' % (*p, *d, *I, inner, outer, rad, up))
    cx, cy, cz, yaw, fov, sx, sy = v['cam']
    out.append('cam %f %f %f %f %f %f %f %d %d %d' % (cx, cy, cz, yaw, fov, sx, sy, W, Hh, spp))
    out.append('env 0.02 0.02 0.025')
    open(path, 'w').write('\n'.join(out) + '\n')

if __name__ == '__main__':
    view, W, Hh, spp, path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    export(view, W, Hh, spp, path)
    print(len(PRIMS), 'prims', len(LIGHTS), 'lights')
