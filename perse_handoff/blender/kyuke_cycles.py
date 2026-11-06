"""Render the staff-room scene (render/kyuke.py) with Blender Cycles.

The geometry, materials, lights and camera angles are read straight from kyuke.py,
so edits there show up in both renderers.  Requires the `bpy` module (pip install bpy).

    python3 kyuke_cycles.py <view> W H SPP out_prefix
      -> out_prefix.npy (linear HDR, float32 HxWx3) ; finish with post_cycles.py

Coordinates: kyuke uses x=east, y=up, z=south.  Blender uses Z up, so a kyuke point
(x, y, z) becomes (x, -z, y).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'render'))
import importlib  # noqa: E402
SCENE = os.environ.get('SCENE', 'kyuke')          # scene module in render/ (kyuke = staff room, morikawa = 森川ビル)
kyuke = importlib.import_module(SCENE)            # builds MATS / PRIMS / LIGHTS / VIEWS on import
if SCENE == 'kyuke':
    import variants  # noqa: E402
    variants.apply(os.environ.get('VARIANT', ''))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

P = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # kyuke -> blender
LIGHT_SCALE = 4 * math.pi * 0.869                            # pt intensity -> Cycles watts (calibrated)


# ----------------------------------------------------------------------------- geometry
class MeshBuf:
    """Accumulates many primitives into one mesh (per material) with exact per-loop normals."""

    def __init__(self):
        self.v, self.f, self.n, self.uv, self.uvn = [], [], [], [], []
        self.nv = 0

    def add(self, verts, faces, loop_n, loop_uv, loop_uvn=None):
        verts = np.asarray(verts, float)
        self.v.append(verts)
        for fc in faces:
            self.f.append([i + self.nv for i in fc])
        self.nv += len(verts)
        self.n.extend(loop_n)
        self.uv.extend(loop_uv)
        self.uvn.extend(loop_uvn if loop_uvn is not None else [(0.0, 0.0)] * len(loop_uv))


def _grain_axes(face_axis, h, mat_axis):
    g = mat_axis
    if g < 0:
        g = int(np.argmax(h))
    if g == face_axis:
        a1, a2 = (face_axis + 1) % 3, (face_axis + 2) % 3
        g = a1 if h[a1] >= h[a2] else a2
    o = 3 - face_axis - g
    return g, o


def box_mesh(buf, c, h, R, mat_axis, seed, rad=0.0):
    """Box (or rounded box when rad>0) with local frame R (columns = local axes)."""
    c = np.asarray(c, float); h = np.asarray(h, float); R = np.asarray(R, float)
    r = min(rad, float(h.min()) * 0.999) if rad > 0 else 0.0
    off = (seed * 0.731) % 13.0
    for a in range(3):
        for s in (-1, 1):
            b, cc = (a + 1) % 3, (a + 2) % 3
            def coords(ax):
                if r <= 0:
                    return [-h[ax], h[ax]]
                k = 4
                lo = list(np.linspace(-h[ax], -h[ax] + r, k + 1))
                hi = list(np.linspace(h[ax] - r, h[ax], k + 1))
                if h[ax] - r <= -h[ax] + r + 1e-9:
                    return sorted(set(lo[:-1] + [0.0] + hi[1:]))
                return lo + hi
            cb, cc_ = coords(b), coords(cc)
            nb, nc = len(cb), len(cc_)
            grid_local, grid_n = [], []
            for i in range(nb):
                for j in range(nc):
                    p = np.zeros(3); p[a] = s * h[a]; p[b] = cb[i]; p[cc] = cc_[j]
                    if r > 0:
                        q = np.clip(p, -(h - r), h - r)
                        d = p - q
                        dn = d / max(np.linalg.norm(d), 1e-12)
                        p = q + r * dn
                        nn = dn
                    else:
                        nn = np.zeros(3); nn[a] = s
                    grid_local.append(p); grid_n.append(nn)
            grid_local = np.array(grid_local); grid_n = np.array(grid_n)
            verts = c + grid_local @ R.T
            norms = grid_n @ R.T
            g, o = _grain_axes(a, h, mat_axis)
            faces, ln, luv, luvn = [], [], [], []
            for i in range(nb - 1):
                for j in range(nc - 1):
                    quad = [i * nc + j, (i + 1) * nc + j, (i + 1) * nc + j + 1, i * nc + j + 1]
                    # orient counter-clockwise seen from outside
                    e1 = grid_local[quad[1]] - grid_local[quad[0]]; e2 = grid_local[quad[3]] - grid_local[quad[0]]
                    nf = np.cross(e1, e2); outward = np.zeros(3); outward[a] = s
                    if np.dot(nf, outward) < 0:
                        quad = quad[::-1]
                    faces.append(quad)
                    for k in quad:
                        lp = grid_local[k]
                        ln.append(tuple(norms[k]))
                        luv.append((lp[g] + off, lp[o] + off * 0.37))
                        if a == 0:
                            luvn.append((0.5 - lp[2] / (2 * h[2]), 0.5 + lp[1] / (2 * h[1])))
                        else:
                            luvn.append((0.5 + lp[0] / (2 * h[0]), 0.5 + lp[1] / (2 * h[1])))
            buf.add(verts, faces, ln, luv, luvn)


def cyl_mesh(buf, p0, p1, r, seg=None):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    ax = p1 - p0; L = np.linalg.norm(ax)
    if L < 1e-9:
        return
    a = ax / L
    t = np.cross(a, [0, 1, 0]) if abs(a[1]) < 0.9 else np.cross(a, [1, 0, 0])
    t /= np.linalg.norm(t); bvec = np.cross(a, t)
    if seg is None:
        seg = 32 if r > 0.1 else (20 if r > 0.03 else 10)
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    ring = np.array([math.cos(x) * t + math.sin(x) * bvec for x in ang])
    verts = np.vstack([p0 + r * ring, p1 + r * ring, p0 + r * ring, p1 + r * ring])
    faces, ln, luv = [], [], []
    def wuv(k):  # kyuke-world based wood coords for round parts (as in pt.cpp)
        pnt = verts[k]
        return (pnt[1], pnt[0] + pnt[2] * 0.3)
    for i in range(seg):
        j = (i + 1) % seg
        quad = [i, j, seg + j, seg + i]
        faces.append(quad)
        for k in quad:
            ln.append(tuple(ring[k % seg])); luv.append(wuv(k))
    cap0 = [2 * seg + i for i in range(seg)][::-1]
    cap1 = [3 * seg + i for i in range(seg)]
    faces.append(cap0); ln.extend([tuple(-a)] * seg); luv.extend([(verts[k][0], verts[k][2]) for k in cap0])
    faces.append(cap1); ln.extend([tuple(a)] * seg); luv.extend([(verts[k][0], verts[k][2]) for k in cap1])
    buf.add(verts, faces, ln, luv)


_SPH = {}
def ell_mesh(buf, c, M, rmax):
    key = 'big' if rmax > 0.05 else 'small'
    if key not in _SPH:
        nu, nv = (24, 12) if key == 'big' else (10, 6)
        pts = [(0, 0, -1)]
        for i in range(1, nv):
            th = -math.pi / 2 + math.pi * i / nv
            for j in range(nu):
                ph = 2 * math.pi * j / nu
                pts.append((math.cos(th) * math.cos(ph), math.cos(th) * math.sin(ph), math.sin(th)))
        pts.append((0, 0, 1))
        pts = np.array(pts); faces = []
        top = len(pts) - 1
        for j in range(nu):
            faces.append([0, 1 + (j + 1) % nu, 1 + j])
        for i in range(nv - 2):
            for j in range(nu):
                a0 = 1 + i * nu + j; a1 = 1 + i * nu + (j + 1) % nu
                faces.append([a0, a1, a1 + nu, a0 + nu])
        for j in range(nu):
            b = 1 + (nv - 2) * nu
            faces.append([b + j, b + (j + 1) % nu, top])
        _SPH[key] = (pts, faces)
    pts, faces = _SPH[key]
    Minv = np.linalg.inv(np.asarray(M, float))
    verts = np.asarray(c, float) + pts @ Minv.T
    nrm = pts @ np.asarray(M, float)          # normal transform: M^T applied to unit normal
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    ln, luv = [], []
    for fc in faces:
        for k in fc:
            ln.append(tuple(nrm[k])); luv.append((verts[k][1], verts[k][0]))
    buf.add(verts, faces, ln, luv)


def to_blender_object(name, buf, noshadow):
    V = np.vstack(buf.v) @ P.T
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in V], [], buf.f)
    me.update()
    n = np.array(buf.n, float) @ P.T
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', np.array(buf.uv, np.float32).ravel())
    uvn = me.uv_layers.new(name='UVN'); uvn.data.foreach_set('uv', np.array(buf.uvn, np.float32).ravel())
    me.normals_split_custom_set([tuple(x) for x in n])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if noshadow:
        ob.visible_shadow = False
    return ob


# ----------------------------------------------------------------------------- shaders
class NB:
    """Tiny helper to wire shader math nodes."""

    def __init__(self, nt):
        self.nt = nt; self.N = nt.nodes; self.L = nt.links

    def link(self, a, sock):
        if isinstance(a, (int, float)):
            sock.default_value = a
        else:
            self.L.new(a, sock)

    def math(self, op, a, b=0.0, c=None):
        n = self.N.new('ShaderNodeMath'); n.operation = op
        self.link(a, n.inputs[0]); self.link(b, n.inputs[1])
        if c is not None:
            self.link(c, n.inputs[2])
        return n.outputs[0]

    def add(self, a, b): return self.math('ADD', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def mad(self, a, b, c): return self.math('MULTIPLY_ADD', a, b, c)

    def smooth(self, e0, e1, x):
        n = self.N.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'
        self.link(x, n.inputs['Value']); n.inputs['From Min'].default_value = e0; n.inputs['From Max'].default_value = e1
        return n.outputs['Result']

    def xyz(self, x, y, z):
        n = self.N.new('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.link(v, n.inputs[i])
        return n.outputs[0]

    def sep(self, vec):
        n = self.N.new('ShaderNodeSeparateXYZ'); self.L.new(vec, n.inputs[0]); return n.outputs

    def noise(self, vec, scale=1.0, detail=4.0, rough=0.5):
        n = self.N.new('ShaderNodeTexNoise'); n.noise_dimensions = '3D'
        self.L.new(vec, n.inputs['Vector']); n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        return n.outputs['Fac']

    def white(self, val):
        n = self.N.new('ShaderNodeTexWhiteNoise'); n.noise_dimensions = '1D'
        self.link(val, n.inputs['W']); return n.outputs['Value']

    def scale_col(self, col_rgb, k):
        n = self.N.new('ShaderNodeVectorMath'); n.operation = 'SCALE'
        n.inputs[0].default_value = (*col_rgb,); self.link(k, n.inputs['Scale']); return n.outputs[0]

    def mulvec(self, vec, k):
        n = self.N.new('ShaderNodeVectorMath'); n.operation = 'SCALE'
        self.L.new(vec, n.inputs[0]); self.link(k, n.inputs['Scale']); return n.outputs[0]

    def bump(self, height, strength, dist=0.001):
        n = self.N.new('ShaderNodeBump'); self.link(height, n.inputs['Height'])
        n.inputs['Strength'].default_value = strength; n.inputs['Distance'].default_value = dist
        return n.outputs['Normal']


def wood_k(nb, u, v, seed):
    """pt.cpp woodCol(): returns the brightness multiplier for grain coords (u along grain)."""
    q = nb.xyz(nb.mad(u, 1.1, seed), nb.mul(v, 28.0), 0.0)
    g = nb.noise(q, 1.0, 4.0)
    q2 = nb.xyz(nb.mad(u, 0.25, nb.mul(seed, 1.7)), nb.mul(v, 3.0), 0.0)
    g2 = nb.noise(q2, 1.0, 3.0)
    ring = nb.mad(nb.math('SINE', nb.add(nb.add(nb.mul(v, 70.0), nb.mul(g, 9.0)), nb.mul(g2, 6.0))), 0.5, 0.5)
    pores = nb.noise(nb.xyz(nb.mad(u, 6.0, seed), nb.mul(v, 160.0), 0.0), 1.0, 2.0)
    k = nb.mul(nb.mul(nb.mad(g2, 0.34, 0.80), nb.mad(ring, 0.20, 0.86)), nb.mad(pores, 0.12, 0.93))
    return k, ring


TV_IMG = None
def tv_image():
    """Sunrise over a sea of clouds with a snow-capped peak (as in the reference perse)."""
    global TV_IMG
    if TV_IMG is not None:
        return TV_IMG
    Wp, Hp = 640, 360
    rng = np.random.default_rng(7)
    def fbm1(n, octaves=5, base=3):
        out = np.zeros(n); a = 0.5
        for o in range(octaves):
            k = base * 2 ** o
            out += a * np.interp(np.linspace(0, k, n), np.arange(k + 1), rng.random(k + 1)); a *= 0.5
        return out
    lin = lambda c: ((np.asarray(c, float) / 255 + 0.055) / 1.055) ** 2.4
    y = np.linspace(1, 0, Hp)[:, None].repeat(Wp, 1); x = np.linspace(0, 1, Wp)[None, :].repeat(Hp, 0)
    t = np.clip((y - 0.35) / 0.65, 0, 1)[..., None]
    sky = lin((250, 196, 120)) * (1 - t) ** 2 + lin((90, 140, 210)) * (1 - (1 - t) ** 2)
    img = sky.copy()
    peak = 0.62 - 1.15 * np.abs(x - 0.47) + 0.03 * fbm1(Wp)[None, :]
    m = y < peak; img[m] = lin((70, 70, 92))
    snow = m & (y > peak - 0.07 - 0.05 * fbm1(Wp)[None, :]); img[snow] = lin((236, 238, 245))
    ridge = y < 0.30 + 0.06 * fbm1(Wp, base=6)[None, :]; img[ridge] = lin((40, 36, 40))
    cloud = (y < 0.36 + 0.05 * fbm1(Wp, base=5)[None, :]) & (y > 0.22)
    img[cloud] = img[cloud] * 0.2 + lin((240, 236, 232)) * 0.8
    fg = y < 0.12 + 0.05 * fbm1(Wp, base=8)[None, :]; img[fg] = lin((50, 34, 26))
    im = bpy.data.images.new('tvimg', Wp, Hp, float_buffer=True)
    im.colorspace_settings.name = 'Linear Rec.709'
    rgba = np.concatenate([img[::-1], np.ones((Hp, Wp, 1))], -1).astype(np.float32)
    im.pixels.foreach_set(rgba.ravel()); im.update(); im.pack()
    TV_IMG = im
    return im


PICTURE_IMG = None
def picture_image():
    """Landscape print for the wall art (approximation of pt.cpp pictureCol)."""
    global PICTURE_IMG
    if PICTURE_IMG is not None:
        return PICTURE_IMG
    Wp, Hp = 512, 384
    rng = np.random.default_rng(3)
    def fbm1(n, octaves=4):
        out = np.zeros(n); a = 0.5
        for o in range(octaves):
            k = 4 * 2 ** o
            out += a * np.interp(np.linspace(0, k, n), np.arange(k + 1), rng.random(k + 1)); a *= 0.5
        return out
    sr = lambda r, g, b: np.array([((c / 255 + 0.055) / 1.055) ** 2.4 for c in (r, g, b)])
    s = np.linspace(0, 1, Wp)[None, :].repeat(Hp, 0); t = np.linspace(0, 1, Hp)[:, None].repeat(Wp, 1)
    m = 0.07
    x = (s - m) / (1 - 2 * m); y = (t - m * 1.4) / (1 - 2.8 * m)
    hor = 0.42
    sm = lambda a, b, v: np.clip((v - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((v - a) / (b - a), 0, 1))
    sky = sr(222, 214, 200) * (1 - sm(0.45, 1, y))[..., None] + sr(150, 170, 188) * sm(0.45, 1, y)[..., None]
    r1 = hor + 0.20 + 0.12 * fbm1(Wp)[None, :] - 0.08 * np.abs(x - 0.35)
    r2 = hor + 0.07 + 0.08 * fbm1(Wp)[None, :]
    img = sky.copy()
    m1 = y < r1; img[m1] = sr(130, 140, 150)
    m2 = y < r2; img[m2] = sr(78, 92, 98)
    w = y < hor
    img[w] = (sr(60, 78, 88) * 0.7 + sky[w] * 0.3)
    frame = (s < m) | (s > 1 - m) | (t < m * 1.4) | (t > 1 - m * 1.4)
    img[frame] = sr(238, 236, 230)
    im = bpy.data.images.new('picture', Wp, Hp, float_buffer=True)
    im.colorspace_settings.name = 'Linear Rec.709'
    rgba = np.concatenate([img, np.ones((Hp, Wp, 1))], -1).astype(np.float32)
    im.pixels.foreach_set(rgba.ravel()); im.update(); im.pack()
    PICTURE_IMG = im
    return im


def make_material(idx):
    c, typ, tex, ks, ex, emit, bump, axis = kyuke.MATS[idx]
    name = [k for k, v in kyuke.NAMES.items() if v == idx][0]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nb = NB(nt)
    bsdf = nt.nodes['Principled BSDF']
    I = bsdf.inputs
    rough = float(np.clip(0.8 * (2.0 / (ex + 2.0)) ** 0.25, 0.04, 0.9))
    I['Roughness'].default_value = rough if (ks > 0 or typ in (1, 4)) else 0.85
    I['Specular IOR Level'].default_value = float(np.clip(ks / 0.08, 0.0, 1.0)) * 0.5 + (0.08 if ks == 0 else 0.0)
    base = tuple(float(x) for x in c)
    I['Base Color'].default_value = (*base, 1)

    geo = nt.nodes.new('ShaderNodeNewGeometry')
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    uvs = nb.sep(uvn.outputs['UV'])
    pos = geo.outputs['Position']

    if typ == 1:
        I['Metallic'].default_value = 1.0; I['Roughness'].default_value = 0.0
    elif typ == 2:
        I['Transmission Weight'].default_value = 1.0; I['Roughness'].default_value = 0.0; I['IOR'].default_value = 1.45
    elif typ == 4:
        I['Metallic'].default_value = 1.0

    if max(emit) > 0:
        mx = max(emit)
        I['Emission Color'].default_value = (emit[0] / mx, emit[1] / mx, emit[2] / mx, 1)
        I['Emission Strength'].default_value = mx
        I['Base Color'].default_value = (0, 0, 0, 1)

    if tex == 1:   # floor planks along kyuke z (= blender -Y)
        p = nb.sep(pos)
        X, Y = p[0], p[1]
        along = nb.mul(Y, -1.0)
        pw, plen = 0.165, 1.8
        row = nb.math('FLOOR', nb.math('DIVIDE', X, pw))
        px = nb.mad(nb.white(row), 1.8, along)
        pid = nb.math('FLOOR', nb.math('DIVIDE', px, plen))
        tone = nb.white(nb.mad(row, 13.1, nb.mul(pid, 7.7)))
        seed = nb.mad(row, 3.1, nb.mul(pid, 1.3))
        k, ring = wood_k(nb, nb.mul(px, 0.6), X, seed)
        fz = nb.mul(nb.math('FRACT', nb.math('DIVIDE', X, pw)), pw)
        fx = nb.mul(nb.math('FRACT', nb.math('DIVIDE', px, plen)), plen)
        gap = nb.math('MINIMUM', nb.math('MINIMUM', fz, nb.math('SUBTRACT', pw, fz)),
                      nb.math('MINIMUM', fx, nb.math('SUBTRACT', plen, fx)))
        gk = nb.mad(nb.smooth(0.0007, 0.0028, gap), 0.55, 0.45)
        warm = nb.white(nb.mad(pid, 3.3, row))
        tint = nb.N.new('ShaderNodeMix'); tint.data_type = 'RGBA'
        nb.link(warm, tint.inputs['Factor'])
        tint.inputs['A'].default_value = (*base, 1)
        tint.inputs['B'].default_value = (base[0] * 1.05, base[1] * 0.95, base[2] * 0.85, 1)
        kk = nb.mul(nb.mul(k, gk), nb.mad(tone, 0.38, 0.80))
        col = nb.mulvec(tint.outputs['Result'], kk)
        nt.links.new(col, I['Base Color'])
        nt.links.new(nb.bump(nb.add(gk, nb.mul(ring, 0.05)), 0.25, 0.002), I['Normal'])
        # gloss varies a little plank to plank
        nt.links.new(nb.mad(tone, 0.08, rough * 0.9), I['Roughness'])
    elif tex in (2, 4):  # wood grain along UV u
        seed = 0.0
        k, ring = wood_k(nb, uvs[0], uvs[1], seed)
        nt.links.new(nb.scale_col(base, k), I['Base Color'])
        nt.links.new(nb.bump(nb.add(k, nb.mul(ring, 0.3)), 0.08, 0.001), I['Normal'])
    elif tex == 3:  # plaster / cloth wallcovering
        a = nb.noise(pos, 7.0, 4.0); c2 = nb.noise(pos, 1.3, 3.0); b = nb.noise(pos, 90.0, 1.0)
        k = nb.mul(nb.add(nb.add(nb.mad(a, 0.06, 0.95), nb.mul(b, 0.03)), -0.045), nb.mad(c2, 0.05, 0.97))
        nt.links.new(nb.scale_col(base, k), I['Base Color'])
        if bump > 0:
            nt.links.new(nb.bump(nb.noise(pos, 55.0, 3.0), 0.12 * bump, 0.002), I['Normal'])
    elif tex == 8:  # fabric / paper
        k = nb.mad(nb.noise(pos, 30.0, 3.0), 0.15, 0.9)
        nt.links.new(nb.scale_col(base, k), I['Base Color'])
        I['Sheen Weight'].default_value = 0.6; I['Sheen Roughness'].default_value = 0.5
        I['Roughness'].default_value = 0.9
        weave = nb.noise(pos, 600.0, 2.0)
        nt.links.new(nb.bump(weave, 0.15, 0.0005), I['Normal'])
    elif tex == 9:   # exposed concrete: cloudy mottling, darker stains; bump>0 adds formwork joints + tie holes
        nrm = nb.sep(geo.outputs['Normal'])
        p = nb.sep(pos)
        nx = nb.math('ABSOLUTE', nrm[0])
        side = nb.math('GREATER_THAN', nx, 0.5)              # wall facing x -> use Y as horizontal
        u = nb.add(nb.mul(p[1], side), nb.mul(p[0], nb.math('SUBTRACT', 1.0, side)))
        v = p[2]
        m1 = nb.noise(pos, 0.7, 6.0, 0.6); m2 = nb.noise(pos, 3.5, 4.0); m3 = nb.noise(pos, 22.0, 2.0)
        stain = nb.smooth(0.52, 0.75, nb.noise(pos, 1.6, 5.0, 0.65))
        k = nb.mul(nb.mul(nb.mad(m1, 0.75, 0.58), nb.mad(m2, 0.30, 0.85)), nb.mad(m3, 0.12, 0.94))
        k = nb.mul(k, nb.mad(stain, -0.30, 1.0))
        k = nb.mul(k, nb.mad(nb.smooth(0.6, 0.8, nb.noise(pos, 6.0, 3.0)), 0.12, 0.94))
        height = nb.add(nb.mul(m2, 0.3), nb.mul(m3, 0.2))
        if bump > 0:
            up = nb.math('ABSOLUTE', nrm[2]); wall = nb.math('LESS_THAN', up, 0.5)
            fu = nb.mul(nb.math('FRACT', nb.math('DIVIDE', u, 0.9)), 0.9)
            fv = nb.mul(nb.math('FRACT', nb.math('DIVIDE', v, 0.6)), 0.6)
            gap = nb.math('MINIMUM', nb.math('MINIMUM', fu, nb.math('SUBTRACT', 0.9, fu)),
                          nb.math('MINIMUM', fv, nb.math('SUBTRACT', 0.6, fv)))
            joint = nb.mul(nb.math('SUBTRACT', 1.0, nb.smooth(0.0008, 0.003, gap)), wall)
            hu = nb.mul(nb.math('SUBTRACT', nb.math('FRACT', nb.math('DIVIDE', nb.add(u, 0.15), 0.45)), 0.5), 0.45)
            hv = nb.mul(nb.math('SUBTRACT', nb.math('FRACT', nb.math('DIVIDE', nb.add(v, 0.15), 0.30)), 0.5), 0.30)
            dist = nb.math('SQRT', nb.add(nb.mul(hu, hu), nb.mul(hv, hv)))
            hole = nb.mul(nb.math('SUBTRACT', 1.0, nb.smooth(0.010, 0.014, dist)), wall)
            # panel-to-panel tone shift
            pid = nb.white(nb.add(nb.math('FLOOR', nb.math('DIVIDE', u, 0.9)), nb.mul(nb.math('FLOOR', nb.math('DIVIDE', v, 0.6)), 17.0)))
            k = nb.mul(k, nb.mad(pid, 0.08, 0.96))
            k = nb.mul(k, nb.mad(joint, -0.25, 1.0)); k = nb.mul(k, nb.mad(hole, -0.55, 1.0))
            height = nb.add(height, nb.mul(nb.add(joint, hole), -1.5))
        nt.links.new(nb.scale_col(base, k), I['Base Color'])
        nt.links.new(nb.mad(m2, 0.15, 0.72), I['Roughness'])
        nt.links.new(nb.bump(height, 0.25, 0.002), I['Normal'])
    elif tex == 10:  # walnut / acacia flooring with strong plank-to-plank colour variation
        p = nb.sep(pos)
        along = p[0] if axis == 0 else nb.mul(p[1], -1.0)
        across = nb.mul(p[1], -1.0) if axis == 0 else p[0]
        pw = 0.125
        row = nb.math('FLOOR', nb.math('DIVIDE', across, pw))
        plen = 0.9
        px = nb.mad(nb.white(row), 3.0, along)
        pid = nb.math('FLOOR', nb.math('DIVIDE', px, plen))
        tone = nb.white(nb.mad(row, 13.1, nb.mul(pid, 7.7)))
        seed = nb.mad(row, 3.1, nb.mul(pid, 1.3))
        k, ring = wood_k(nb, nb.mul(px, 0.6), across, seed)
        streak = nb.noise(nb.xyz(nb.mad(px, 0.8, seed), nb.mul(across, 14.0), 0.0), 1.0, 3.0)
        mixf = nb.math('POWER', nb.add(nb.mul(tone, 0.75), nb.mul(streak, 0.35)), 1.3)
        cm = nb.N.new('ShaderNodeMix'); cm.data_type = 'RGBA'
        nb.link(nb.math('MINIMUM', mixf, 1.0), cm.inputs['Factor'])
        cm.inputs['A'].default_value = (*[float(x) for x in kyuke.srgb(56, 32, 19)], 1)
        cm.inputs['B'].default_value = (*[float(x) for x in kyuke.srgb(170, 112, 64)], 1)
        fz = nb.mul(nb.math('FRACT', nb.math('DIVIDE', across, pw)), pw)
        fx = nb.mul(nb.math('FRACT', nb.math('DIVIDE', px, plen)), plen)
        gap = nb.math('MINIMUM', nb.math('MINIMUM', fz, nb.math('SUBTRACT', pw, fz)),
                      nb.math('MINIMUM', fx, nb.math('SUBTRACT', plen, fx)))
        gk = nb.mad(nb.smooth(0.0006, 0.0022, gap), 0.6, 0.4)
        col = nb.mulvec(cm.outputs['Result'], nb.mul(k, gk))
        nt.links.new(col, I['Base Color'])
        nt.links.new(nb.bump(nb.add(gk, nb.mul(ring, 0.05)), 0.25, 0.002), I['Normal'])
        nt.links.new(nb.mad(tone, 0.10, rough * 0.85), I['Roughness'])
    elif tex == 11:  # TV picture
        img = nt.nodes.new('ShaderNodeTexImage'); img.image = tv_image()
        uv2 = nt.nodes.new('ShaderNodeUVMap'); uv2.uv_map = 'UVN'
        nt.links.new(uv2.outputs['UV'], img.inputs['Vector'])
        I['Base Color'].default_value = (0, 0, 0, 1)
        nt.links.new(img.outputs['Color'], I['Emission Color']); I['Emission Strength'].default_value = 0.45
        I['Roughness'].default_value = 0.15
    elif tex == 7:
        k = nb.mad(nb.noise(pos, 45.0, 3.0), 0.18, 0.88)
        nt.links.new(nb.scale_col(base, k), I['Base Color'])
    elif tex == 5:
        img = nt.nodes.new('ShaderNodeTexImage'); img.image = picture_image()
        uv2 = nt.nodes.new('ShaderNodeUVMap'); uv2.uv_map = 'UVN'
        nt.links.new(uv2.outputs['UV'], img.inputs['Vector'])
        nt.links.new(img.outputs['Color'], I['Base Color'])
    return m


# ----------------------------------------------------------------------------- scene
def build(vname, W, H, spp):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    v = kyuke.VIEWS[vname]
    drop = v['drop']

    def inset(h, idx, fl):
        # flush faces of two different boxes make Cycles block light between them (black bands).
        # Pull every non-shell box in by a tiny, per-part different amount (0.1-0.9 mm).
        if fl & 2:
            return h
        e = 0.0001 * (1 + (idx * 7) % 9)
        return tuple(max(x - e, x * 0.7) for x in h)

    bufs = {}
    for idx, p in enumerate(kyuke.PRIMS):
        if p[0] in drop:
            continue
        kind = p[1]
        if kind == 'box':
            _, _, c, h, R, mi, fl = p
            key = (mi, fl & 1)
            h = inset(h, idx, fl)
            if kyuke.MATS[mi][2] == 5:   # print sits flush with its frame: lift it 1 mm so it wins
                h = (h[0] + 0.002, h[1], h[2])
            box_mesh(bufs.setdefault(key, MeshBuf()), c, h, R, kyuke.MATS[mi][7], idx)
        elif kind == 'rbx':
            _, _, c, h, R, mi, fl, r = p
            key = (mi, fl & 1)
            h = inset(h, idx, fl)
            box_mesh(bufs.setdefault(key, MeshBuf()), c, h, R, kyuke.MATS[mi][7], idx, rad=r)
        elif kind == 'cyl':
            _, _, p0, p1, r, mi, fl = p
            key = (mi, fl & 1)
            cyl_mesh(bufs.setdefault(key, MeshBuf()), p0, p1, r)
        else:
            _, _, c, M, rmax, mi, fl = p
            key = (mi, fl & 1)
            ell_mesh(bufs.setdefault(key, MeshBuf()), c, M, rmax)

    mats = {}
    for (mi, ns), buf in bufs.items():
        if mi not in mats:
            mats[mi] = make_material(mi)
        ob = to_blender_object('%s_%d' % (mats[mi].name, ns), buf, ns)
        ob.data.materials.append(mats[mi])

    for i, l in enumerate(kyuke.LIGHTS):
        g, p, d, I, inner, outer, rad, up = l
        if g in drop:
            continue
        mx = max(I)
        ld = bpy.data.lights.new('L%d' % i, 'SPOT')
        ld.energy = mx * LIGHT_SCALE
        ld.color = (I[0] / mx, I[1] / mx, I[2] / mx)
        ld.spot_size = math.radians(min(2 * outer, 179.0))
        ld.spot_blend = float(np.clip((outer - inner) / outer, 0, 1))
        ld.shadow_soft_size = rad
        ld.use_soft_falloff = False
        ob = bpy.data.objects.new('L%d' % i, ld)
        ob.location = Vector(P @ np.array(p, float))
        dirb = Vector(P @ np.array(d, float)).normalized()
        ob.rotation_euler = dirb.to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(ob)

    world = bpy.data.worlds.new('env'); world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    e = kyuke.ENV; mx = max(e)
    bg.inputs['Color'].default_value = (e[0] / mx, e[1] / mx, e[2] / mx, 1); bg.inputs['Strength'].default_value = mx
    sc.world = world

    cx, cy, cz, yaw, fov, sx, sy = v['cam']
    cd = bpy.data.cameras.new('cam')
    cd.sensor_fit = 'HORIZONTAL'; cd.angle = math.radians(fov)
    cd.shift_x = sx * 0.5; cd.shift_y = sy * (H / W) * 0.5
    cd.clip_start = 0.02
    cam = bpy.data.objects.new('cam', cd)
    cam.location = Vector(P @ np.array([cx, cy, cz]))
    cam.rotation_euler = (math.pi / 2, 0.0, -yaw)
    sc.collection.objects.link(cam); sc.camera = cam

    r = sc.render
    r.engine = 'CYCLES'; r.resolution_x = W; r.resolution_y = H; r.resolution_percentage = 100
    r.film_transparent = False
    cy_ = sc.cycles
    cy_.device = 'CPU'; cy_.samples = spp; cy_.use_adaptive_sampling = True; cy_.adaptive_threshold = 0.01
    cy_.use_denoising = True; cy_.denoiser = 'OPENIMAGEDENOISE'
    cy_.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy_.max_bounces = 10; cy_.diffuse_bounces = 6; cy_.glossy_bounces = 4; cy_.transmission_bounces = 8
    cy_.sample_clamp_indirect = 10.0; cy_.caustics_reflective = False; cy_.caustics_refractive = False
    cy_.blur_glossy = 1.0
    sc.view_settings.view_transform = 'Standard'
    return sc


def main():
    vname, W, H, spp, pre = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    sc = build(vname, W, H, spp)
    if os.environ.get('SAVE_BLEND'):
        bpy.ops.wm.save_as_mainfile(filepath=pre + '.blend')
    exr = pre + '.exr'
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    sc.render.filepath = exr
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(exr)
    a = np.array(im.pixels[:], np.float32).reshape(H, W, 4)[::-1, :, :3]
    np.save(pre + '.npy', a)
    print('saved', pre + '.npy')


if __name__ == '__main__':
    main()
