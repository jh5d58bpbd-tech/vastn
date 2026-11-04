"""Design variants for the staff room: finishes, colours and light colour only.

Layout (positions and sizes of everything) is never changed here.
Usage:  import kyuke, variants; variants.apply('cafe')   (after kyuke is imported)
        or set VARIANT=cafe for blender/kyuke_cycles.py
"""
import kyuke


def _set(name, rgb=None, **kw):
    i = kyuke.NAMES[name]
    c, typ, tex, ks, ex, emit, bump, axis = kyuke.MATS[i]
    if rgb is not None:
        c = kyuke.srgb(*rgb)
    d = dict(typ=typ, tex=tex, ks=ks, ex=ex, emit=emit, bump=bump, axis=axis)
    d.update(kw)
    kyuke.MATS[i] = (c, d['typ'], d['tex'], d['ks'], d['ex'], d['emit'], d['bump'], d['axis'])


def _new(name, rgb, **kw):
    kyuke.mat(name, rgb, **kw)
    return kyuke.NAMES[name]


def _retarget(pred, mat_name):
    mi = kyuke.NAMES[mat_name]
    for i, p in enumerate(kyuke.PRIMS):
        if pred(i, p):
            q = list(p); q[5] = mi; kyuke.PRIMS[i] = tuple(q)


def cafe():
    """「Warm Oak & Smoke」— 明るいオーク × スモークドオーク × 石目、2層の光。

    ベース（70%）: オーク床・温白の壁は据え置き、天井は温かみのある薄いグレージュへ。
    アソート（25%）: 造作（ベンチ台・ハイカウンター腰・前室カウンター天板）をスモークドオークで締め、
                     テーブル天板は明るいオークのマット仕上げ。ソファ後ろの木目クロスは深めのウォールナット調。
    アクセント（5%）: クッションに木の補色寄りのくすんだ青緑と、類似色のテラコッタ。
    引き締め: ハイカウンター天板を明るい石目（テラゾー調）に、脚は既存の黒スチール。
    光: 席まわりは電球色 2700K のまま、キッチン・前室のダウンライトは温白色 3500K。
    """
    # --- base
    _set('gyptone', (216, 211, 203), bump=0.3)                         # 天井クロス: 温かい薄グレージュ
    # --- assort: wood
    _set('woodcloth', (128, 88, 58), ks=0.02, ex=25)                   # アクセント壁: ウォールナット調 木目クロス（マット）
    _set('walnut_h', (112, 84, 62), ks=0.04, ex=60)                    # 造作: スモークドオーク（オイル仕上げ）
    _set('walnut', (204, 156, 104), ks=0.04, ex=70)                    # テーブル天板・スツール座: 明るいオーク（マット）
    _set('chairwood', (46, 36, 30), ks=0.05, ex=80)                    # 椅子フレーム: 焦げ茶
    _set('louver', (150, 118, 88), ks=0.03, ex=40)                     # 前室ルーバー: オーク（少し明るく）
    # --- assort: fabric
    _set('fabric_g', (206, 196, 178))                                  # ソファ: オートミール（生成り寄り）
    _set('cognac', (214, 204, 186))                                    # 椅子座面: 生成り
    _set('rug', (152, 138, 120))                                       # ラグ: 温かいグレージュ
    # --- accents
    _set('cushion', (104, 128, 122))                                   # くすんだ青緑（木の補色寄り）
    _set('mustard', (160, 104, 82))                                    # テラコッタ（類似色）
    # --- hard contrast: high counter top in light terrazzo-like stone
    _new('terrazzo', (228, 222, 212), tex=3, bump=1.6, ks=0.06, ex=160)
    _retarget(lambda i, p: p[0] == 'counter' and p[1] == 'box' and abs(p[3][1] - 0.025) < 1e-6 and abs(p[3][0] - 1.15) < 1e-6,
              'terrazzo')
    # --- light colour: kitchen / front room downlights at 3500K
    NEUTRAL = (1.0, 0.92, 0.82)
    for i, l in enumerate(kyuke.LIGHTS):
        g, p, d, I, inner, outer, rad, up = l
        if p[2] < 2.0 and p[1] > 2.0:          # ceiling downlights over the kitchen / front room
            mx = max(I)
            kyuke.LIGHTS[i] = (g, p, d, (mx * NEUTRAL[0], mx * NEUTRAL[1], mx * NEUTRAL[2]), inner, outer, rad, up)


VARIANTS = {'cafe': cafe}


def apply(name):
    if name:
        VARIANTS[name]()
