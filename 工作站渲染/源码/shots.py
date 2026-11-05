"""批量出图：全景 / 喷涂 / 码垛 / 换枪 / 俯视布局。"""
import os
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
import numpy as np
from PIL import Image

import engine
import geo
import robot
import station
import shot as S

R = robot.IRB4600()
OUT = '/tmp/r3/'


def stamp(parts):
    """工业现场常见的地面标识牌、灭火器、工具箱等点缀。"""
    p = []
    # 灭火器
    x, y = 3.55, 1.55
    p.append(geo.cyl(0.075, 0.46, (x, y, 0.23), 'z', 'red', 20))
    p.append(geo.cyl(0.028, 0.10, (x, y, 0.51), 'z', 'black', 12))
    p.append(geo.box(0.02, 0.10, 0.03, (x, y + 0.09, 0.40), 'black'))
    # 工具箱
    p.append(geo.box(0.55, 0.32, 0.22, (3.35, -1.55, 0.11), 'orange'))
    p.append(geo.box(0.56, 0.33, 0.02, (3.35, -1.55, 0.225), 'dark'))
    # 立柱上的急停盒
    p.append(geo.box(0.10, 0.07, 0.14, (0.45, 1.86, 1.20), 'yellow'))
    p.append(geo.cyl(0.032, 0.03, (0.45, 1.82, 1.20), 'y', 'red', 20))
    return p


def spray_cone(tcp, length=0.15, r=0.13, alpha=0.16):
    """喷涂扇形雾锥：从喷嘴到工件表面的锥体。"""
    import trimesh
    V = np.array([
        [0, -r * 1.5, -length], [0, r * 1.5, -length],
        [r, 0, -length], [-r, 0, -length],
        [0, 0, 0],
    ], float)
    F = np.array([[4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0]])
    m = trimesh.Trimesh(vertices=V, faces=F, process=False)
    m.apply_translation(np.array(tcp, float))
    return [(m, 'fog')]


def main():
    # ---------- A 全景 ----------
    q_spray = R.ik((0.9, 0, 1.10), (0, 0, -1), robot.SPRAY_TCP)
    parts = S.base_scene() + S.robot_parts(q_spray)[0] + stamp(None)
    parts += spray_cone((0.9, 0, 1.10))
    S.shot(parts, (4.55, 3.05, 3.35), (0.30, -0.55, 0.50), 36, OUT + 'A_wide.png')
    print('A done')

    # ---------- B 喷涂特写 ----------
    pb = S.base_scene(layers=5) + S.robot_parts(q_spray)[0]
    pb += spray_cone((0.9, 0, 1.10))
    S.shot(pb, (1.95, 1.35, 1.72), (0.86, 0.02, 1.00), 34, OUT + 'B_spray.png')
    print('B done')

    # ---------- C 码垛特写 ----------
    tgt = (0.05, -0.78, 1.28)     # 第 4 层某箱位上方
    q_pal = R.ik(tgt, (0, 0, -1), robot.GRIP_TCP)
    pc = S.base_scene(layers=3) + S.robot_parts(q_pal, 'grip')[0]
    pc += robot.carton(tgt[0], tgt[1], tgt[2] - 0.125)
    S.shot(pc, (2.30, 0.95, 2.45), (0.00, -0.95, 1.05), 33, OUT + 'C_pallet.png')
    print('C done')

    # ---------- D 换枪特写 ----------
    tgt_d = (-0.88, -0.80, 0.84)
    q_d = R.ik(tgt_d, (0, 0, -1), robot.GRIP_TCP)
    pd = S.base_scene(layers=5, carton_on_stand=False, carton_on_conv=False)
    pd += S.robot_parts(q_d, 'grip')[0]
    S.shot(pd, (0.15, 1.05, 2.25), (-0.80, -0.62, 0.72), 36, OUT + 'D_dock.png')
    print('D done')

    # ---------- E 俯视布局 ----------
    pe = S.base_scene(with_walls=False) + S.robot_parts(q_spray)[0]
    S.shot(pe, (0.60, -0.60, 9.0), (0.60, -0.60, 0.0), 0, OUT + 'E_top.png',
           w=1500, h=1000, ortho=3.05, exposure=1.10, shadows=False,
           ambient=0.55, key=0.62, bg=(0.88, 0.89, 0.90, 1.0))
    print('E done')


if __name__ == '__main__':
    main()
