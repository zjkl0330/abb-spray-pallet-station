"""几何基元与材质库。所有函数返回 (trimesh.Trimesh, 材质键)，最后统一转 pyrender。"""
import numpy as np
import trimesh


def mat(color, metallic=0.0, rough=0.5, alpha=None):
    import pyrender
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[*color, 1.0] if alpha is None else [*color, alpha],
        metallicFactor=metallic, roughnessFactor=rough,
        alphaMode='BLEND' if alpha is not None else 'OPAQUE')


M = {
    'white':    mat((0.815, 0.815, 0.800), 0.05, 0.40),
    'white2':   mat((0.780, 0.780, 0.765), 0.05, 0.46),
    'dark':     mat((0.130, 0.140, 0.155), 0.40, 0.45),
    'dark2':    mat((0.090, 0.095, 0.105), 0.30, 0.55),
    'red':      mat((0.775, 0.110, 0.120), 0.05, 0.38),
    'alu':      mat((0.690, 0.705, 0.725), 0.88, 0.36),
    'steel':    mat((0.545, 0.560, 0.575), 0.92, 0.28),
    'stain':    mat((0.755, 0.765, 0.775), 1.00, 0.20),
    'galv':     mat((0.640, 0.650, 0.660), 0.80, 0.42),
    'rubber':   mat((0.042, 0.042, 0.048), 0.00, 0.86),
    'card':     mat((0.505, 0.360, 0.222), 0.00, 0.92),
    'card_b':   mat((0.455, 0.318, 0.192), 0.00, 0.92),
    'tape':     mat((0.735, 0.675, 0.545), 0.00, 0.52),
    'label':    mat((0.880, 0.875, 0.860), 0.00, 0.60),
    'wood':     mat((0.530, 0.385, 0.230), 0.00, 0.84),
    'wood2':    mat((0.465, 0.330, 0.192), 0.00, 0.86),
    'floor':    mat((0.480, 0.490, 0.505), 0.08, 0.50),
    'yellow':   mat((0.830, 0.665, 0.070), 0.05, 0.48),
    'mesh':     mat((0.520, 0.400, 0.105), 0.40, 0.55),
    'glass':    mat((0.680, 0.760, 0.790), 0.10, 0.10, 0.13),
    'black':    mat((0.055, 0.055, 0.060), 0.10, 0.58),
    'screen':   mat((0.065, 0.085, 0.105), 0.35, 0.12),
    'concrete': mat((0.620, 0.615, 0.600), 0.00, 0.72),
    'cu':       mat((0.720, 0.430, 0.240), 0.95, 0.30),
    'panel':    mat((0.590, 0.605, 0.615), 0.60, 0.45, 0.42),
    'sign':     mat((0.880, 0.740, 0.090), 0.05, 0.45),
    'wall':     mat((0.700, 0.705, 0.700), 0.00, 0.80),
    'orange':   mat((0.820, 0.380, 0.075), 0.10, 0.42),
    'fog':      mat((0.945, 0.950, 0.960), 0.00, 0.88, 0.30),
}


# ---------------- 基元 ----------------
def box(sx, sy, sz, center=(0, 0, 0), mk='white'):
    m = trimesh.creation.box(extents=[sx, sy, sz])
    m.apply_translation(np.array(center, float))
    return m, mk


def cyl(r, h, center=(0, 0, 0), axis='z', mk='steel', seg=36):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=seg)
    if axis == 'x':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == 'y':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation(np.array(center, float))
    return m, mk


def beam(L, h0, w0, h1, w1, x0=0.0, mk='white', cap=False):
    """沿 +X 从 x0 到 x0+L 的变截面梁；h 为 Z 向高，w 为 Y 向宽。"""
    V = np.array([
        [x0, -w0/2, -h0/2], [x0+L, -w1/2, -h1/2], [x0+L, w1/2, -h1/2], [x0, w0/2, -h0/2],
        [x0, -w0/2,  h0/2], [x0+L, -w1/2,  h1/2], [x0+L, w1/2,  h1/2], [x0, w0/2,  h0/2],
    ], float)
    F = np.array([
        [0,2,1],[0,3,2],[4,5,6],[4,6,7],
        [0,1,5],[0,5,4],[1,2,6],[1,6,5],
        [2,3,7],[2,7,6],[3,0,4],[3,4,7],
    ])
    m = trimesh.Trimesh(vertices=V, faces=F, process=False)
    return m, mk


def rod(p1, p2, r, mk='rubber', seg=14):
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        return None
    m = trimesh.creation.cylinder(radius=r, height=L, sections=seg)
    m.apply_translation([0, 0, L / 2])
    z = d / L
    a = np.array([0, 0, 1.0])
    v = np.cross(a, z)
    s = float(np.linalg.norm(v))
    if s < 1e-9:
        R = np.eye(3) if z[2] > 0 else trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])[:3, :3]
    else:
        R = trimesh.transformations.rotation_matrix(np.arccos(np.clip(z[2], -1, 1)), v / s)[:3, :3]
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = p1
    m.apply_transform(T)
    return m, mk


def slab(sx, sy, z, center=(0, 0), thick=0.002, mk='floor'):
    return box(sx, sy, thick, (center[0], center[1], z), mk)


def T_rotz(a):
    return trimesh.transformations.rotation_matrix(a, [0, 0, 1])


def T_roty(a):
    return trimesh.transformations.rotation_matrix(a, [0, 1, 0])


def T_trans(v):
    T = np.eye(4)
    T[:3, 3] = np.array(v, float)
    return T


def apply(parts, T):
    """对一组 (mesh, mk) 施加同一变换。"""
    out = []
    for g, k in parts:
        if g is None:
            continue
        g = g.copy()
        g.apply_transform(T)
        out.append((g, k))
    return out
