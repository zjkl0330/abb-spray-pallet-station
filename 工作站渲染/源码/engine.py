"""场景装配与离屏渲染。"""
import os
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')

import numpy as np

# pyrender 0.1.45 仍引用 numpy 1.x 已移除的别名
if not hasattr(np, 'infty'):
    np.infty = np.inf
if not hasattr(np, 'float'):
    np.float = float

import trimesh
import pyrender
from PIL import Image

from geo import M
import geo


def to_meshes(parts, shadow=True):
    """按材质分组合并，减少 draw call。"""
    groups = {}
    for g, k in parts:
        if g is None or len(g.faces) == 0:
            continue
        groups.setdefault(k, []).append(g)
    out = []
    for k, gs in groups.items():
        merged = trimesh.util.concatenate(gs) if len(gs) > 1 else gs[0]
        out.append(pyrender.Mesh.from_trimesh(merged, material=M[k], smooth=False))
    return out


def look_at(eye, target, up=(0, 0, 1)):
    eye = np.array(eye, float)
    target = np.array(target, float)
    f = target - eye
    f /= np.linalg.norm(f)
    up = np.array(up, float)
    if abs(float(np.dot(f, up))) > 0.999:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    T = np.eye(4)
    T[:3, 0] = r
    T[:3, 1] = u
    T[:3, 2] = -f
    T[:3, 3] = eye
    return T


def make_scene(parts, bg=(0.60, 0.63, 0.66, 1.0), ambient=0.20):
    scene = pyrender.Scene(bg_color=list(bg), ambient_light=np.array([ambient] * 3))
    for m in to_meshes(parts):
        scene.add(m)
    return scene


def add_lights(scene, key_dir=(0.85, -0.95, 1.45), key_int=0.95, fill_int=0.22, rim_int=0.18):
    key = pyrender.DirectionalLight(color=np.array([1.0, 0.985, 0.96]), intensity=key_int)
    key.cast_shadows = True
    T = look_at(np.array(key_dir, float) * 4, np.zeros(3))
    scene.add(key, pose=T)

    fill = pyrender.DirectionalLight(color=np.array([0.86, 0.91, 1.0]), intensity=fill_int)
    scene.add(fill, pose=look_at(np.array([-2.4, 2.2, 2.0]), np.zeros(3)))

    rim = pyrender.DirectionalLight(color=np.array([0.95, 0.96, 1.0]), intensity=rim_int)
    scene.add(rim, pose=look_at(np.array([-1.5, -3.0, 1.2]), np.zeros(3)))

    top = pyrender.DirectionalLight(color=np.array([1.0, 0.99, 0.97]), intensity=0.35)
    scene.add(top, pose=look_at(np.array([0.2, 0.1, 6.0]), np.zeros(3)))


def add_cam(scene, eye, target, fov=38.0, ortho=None, up=(0, 0, 1), aspect=16 / 9):
    if ortho is None:
        cam = pyrender.PerspectiveCamera(yfov=np.radians(fov), znear=0.05, zfar=100.0)
    else:
        cam = pyrender.OrthographicCamera(xmag=ortho, ymag=ortho / aspect, znear=0.1, zfar=100.0)
    return scene.add(cam, pose=look_at(eye, target, up))


def render(scene, cam_node, w=1600, h=900, ssao=True, shadows=True, ss=2):
    r = pyrender.OffscreenRenderer(int(w * ss), int(h * ss))
    flags = pyrender.RenderFlags.NONE
    if shadows:
        flags |= pyrender.RenderFlags.SHADOWS_DIRECTIONAL

    color, depth = r.render(scene, flags=flags)
    r.delete()
    img = Image.fromarray(color)
    if ss != 1:
        img = img.resize((w, h), Image.LANCZOS)
    return np.array(img), depth


def grade(arr, exposure=1.0, gamma=2.2, contrast=1.04):
    x = arr.astype(np.float32) / 255.0
    x = np.clip(x * exposure, 0, 1)
    x = np.power(x, 1.0 / gamma) if gamma != 1.0 else x
    x = np.clip((x - 0.5) * contrast + 0.5, 0, 1)
    return (x * 255).astype(np.uint8)
