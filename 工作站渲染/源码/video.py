"""喷涂循环动画：按论文表 4-3 的 6 个顶面示教点生成帧序列。"""
import os
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
import sys
import numpy as np
from PIL import Image

import engine
import geo
import robot
import station
import shot as S
from shots import spray_cone

R = robot.IRB4600()
FPS = 15
OUT = '/tmp/r3/frames/'


def ease(t):
    return t * t * (3 - 2 * t)


def blend(qa, qb, n, use_ease=True):
    a, b = np.array(qa, float), np.array(qb, float)
    for k in range(6):
        while b[k] - a[k] > np.pi:
            b[k] -= 2 * np.pi
        while b[k] - a[k] < -np.pi:
            b[k] += 2 * np.pi
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        s = ease(t) if use_ease else t
        out.append(list(a + (b - a) * s))
    return out


def build_timeline():
    """返回 [(q, 是否喷雾)] 序列。"""
    base = station.P_SPRAY
    # 示教点（世界坐标，TCP 高度 1.10，即箱顶 0.95 上方 150 mm）
    pts = [(0.76, -0.09, 1.10), (0.76, 0.09, 1.10),
           (0.90, 0.09, 1.10), (0.90, -0.09, 1.10),
           (1.04, -0.09, 1.10), (1.04, 0.09, 1.10)]
    qs = [R.ik(p, (0, 0, -1), robot.SPRAY_TCP) for p in pts]
    q_home = R.ik((0.62, 0.0, 1.52), (0, 0, -1), robot.SPRAY_TCP)
    q_appr = R.ik((0.76, -0.09, 1.26), (0, 0, -1), robot.SPRAY_TCP)

    seq = []
    seq += [(q, False) for q in blend(q_home, q_appr, 18)]
    seq += [(q, False) for q in blend(q_appr, qs[0], 8, use_ease=False)]
    for i in range(len(qs) - 1):
        seq += [(q, True) for q in blend(qs[i], qs[i + 1], 10, use_ease=False)]
    seq += [(q, True) for q in blend(qs[-1], q_appr, 8, use_ease=False)]
    seq += [(q, False) for q in blend(q_appr, q_home, 16)]
    # 循环停顿
    seq += [(q_home, False)] * 6
    return seq


def main():
    os.makedirs(OUT, exist_ok=True)
    seq = build_timeline()
    n = len(seq)
    print('frames', n, 'duration %.2fs' % (n / FPS))

    # 静态部分只构建一次
    static = S.base_scene()

    eye0 = np.array([2.30, 1.52, 1.80])
    eye1 = np.array([1.98, 1.30, 1.66])
    tgt = np.array([0.93, 0.00, 1.02])

    for i, (q, spraying) in enumerate(seq):
        parts = list(static)
        parts += S.robot_parts(q, 'spray')[0]
        if spraying:
            P = R.world(q)
            tcp = P['fl'] + (np.array([0, 0, -1]) * 0)
            # 喷枪 TCP 位于法兰下方 220 mm（工具朝下）
            tcp = P['fl'] + np.array([0, 0, -robot.SPRAY_TCP])
            parts += spray_cone(tuple(tcp), length=0.15, r=0.15)
        t = i / max(n - 1, 1)
        eye = eye0 + (eye1 - eye0) * ease(t)
        S.shot(parts, tuple(eye), tuple(tgt), 34, (OUT + 'f%03d.png') % i,
               w=1280, h=720, ss=2, exposure=1.14)
        if i % 15 == 0:
            print('  frame', i, '/', n)
    print('done')


if __name__ == '__main__':
    main()
