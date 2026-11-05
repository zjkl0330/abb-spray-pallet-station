"""机位与出图脚本。"""
import os
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
import sys
import numpy as np
import pyrender
from PIL import Image

import engine
import geo
import robot
import station

R = robot.IRB4600()


def base_scene(layers=5, carton_on_stand=True, carton_on_conv=True, with_walls=True):
    p = []
    p += station.floor()
    if with_walls:
        p += station.walls()
    p += station.conveyor(0.46, 0.74)
    p += station.conveyor(1.06, 3.60)
    p += station.spray_stand()
    p += station.pallet(*station.P_PALLET[:2])
    p += station.stack(*station.P_PALLET[:2], n_layer=layers)
    p += station.tool_rack()
    p += station.cabinet()
    p += station.fence()
    if carton_on_stand:
        p += robot.carton(station.P_SPRAY[0], station.P_SPRAY[1],
                          station.P_SPRAY[2] + station.CARTON[2] / 2)
    if carton_on_conv:
        p += robot.carton(1.60, 0, 0.70 + station.CARTON[2] / 2)      # 取料位待抓
        p += robot.carton(2.55, 0, 0.70 + station.CARTON[2] / 2, yaw=0.02)
        p += robot.carton(3.20, 0, 0.70 + station.CARTON[2] / 2, yaw=-0.03)
    return p


def robot_parts(q, tool='spray'):
    parts, Tf = R.build(q)
    if tool == 'spray':
        parts += geo.apply(robot.tool_spray(), Tf)
    elif tool == 'grip':
        parts += geo.apply(robot.tool_gripper(), Tf)
    elif tool == 'none':
        pass
    return parts, Tf


def shot(parts, eye, target, fov, out, w=1600, h=900, ss=2, ortho=None,
         exposure=1.12, key=0.95, ambient=0.22, bg=(0.55, 0.58, 0.61, 1.0),
         shadows=True, contrast=1.05):
    sc = engine.make_scene(parts, bg=bg, ambient=ambient)
    engine.add_lights(sc, key_int=key)
    cam = engine.add_cam(sc, eye, target, fov=fov, ortho=ortho, aspect=w / h)
    img, depth = engine.render(sc, cam, w, h, ss=ss, shadows=shadows)
    img = engine.grade(img, exposure=exposure, gamma=1.0, contrast=contrast)
    Image.fromarray(img).save(out)
    return img, depth


if __name__ == '__main__':
    q = R.ik((0.9, 0, 1.10), tool_dir=(0, 0, -1), tool_len=robot.SPRAY_TCP)
    parts = base_scene() + robot_parts(q)[0]
    shot(parts, (3.15, 1.85, 2.70), (0.15, -0.62, 0.55), 39, '/tmp/r3/wide.png')
    p2 = base_scene() + robot_parts(q)[0]
    shot(p2, (0.35, -0.55, 9.0), (0.35, -0.55, 0.0), 0, '/tmp/r3/top.png',
         w=1400, h=1000, ortho=3.4)
    print('done')
