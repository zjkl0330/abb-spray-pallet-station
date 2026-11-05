"""按论文表 3-3 坐标装配喷涂-码垛复合工作站。单位 m，基座底面中心为原点。"""
import numpy as np

import geo
from geo import box, cyl, beam, rod, apply, T_rotz, T_roty, T_trans
from robot import IRB4600, tool_spray, tool_gripper, carton, SPRAY_TCP, GRIP_TCP

# ---- 论文表 3-3 坐标 ----
P_SPRAY = np.array([0.90, 0.0, 0.70])     # 喷涂工位，工件底面中心
P_PICK = np.array([1.60, 0.0, 0.70])      # 码垛取料位
P_PALLET = np.array([0.0, -1.10, 0.15])   # 托盘上表面中心
P_DOCK = np.array([-0.90, -0.60, 0.70])   # 换枪架
P_CAB = np.array([-1.60, 0.90, 0.0])      # 控制柜

CARTON = (0.35, 0.25, 0.25)   # 长 宽 高
PALLET = (1.20, 1.00, 0.15)


def walls():
    """车间围墙：左墙与后墙，提供空间参照。"""
    p = []
    p.append(box(0.10, 9.0, 4.2, (-3.30, -0.5, 2.1), 'wall'))
    p.append(box(9.0, 0.10, 4.2, (1.2, -3.10, 2.1), 'wall'))
    # 墙裙
    p.append(box(0.06, 9.0, 0.55, (-3.24, -0.5, 0.27), 'concrete'))
    p.append(box(9.0, 0.06, 0.55, (1.2, -3.04, 0.27), 'concrete'))
    # 墙面分缝
    for z in (1.35, 2.55):
        p.append(box(0.02, 9.0, 0.012, (-3.25, -0.5, z), 'dark2'))
    return p


def floor():
    p = [geo.slab(16, 14, -0.001, (2.0, -0.5), 0.002, 'floor')]
    # 围栏内警示黄线
    for pts in [
        [(-1.42, -1.98), (3.88, -1.98)], [(-1.42, 1.98), (3.88, 1.98)],
        [(-1.42, -1.98), (-1.42, 1.98)], [(3.88, -1.98), (3.88, 1.98)],
    ]:
        p += _line(pts[0], pts[1], 0.06, 'yellow')
    return p


def _line(a, b, w, mk):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    ang = float(np.arctan2(d[1], d[0]))
    m, k = box(L, w, 0.004, (0, 0, 0), mk)
    m.apply_transform(T_trans([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.002]) @ T_rotz(ang))
    return [(m, k)]


# ---------------- 输送链 ----------------
def conveyor(x0=0.30, x1=3.60, y=0.0, h=0.70, bw=0.40):
    """铝型材机架 + 皮带 + 侧导条 + 支腿；含两处挡停与光电。"""
    p = []
    L = x1 - x0
    cx = (x0 + x1) / 2
    # 侧梁（型材）
    for sy in (-1, 1):
        p.append(box(L, 0.045, 0.075, (cx, y + sy * (bw / 2 + 0.028), h - 0.055), 'alu'))
        p.append(box(L, 0.010, 0.055, (cx, y + sy * (bw / 2 + 0.004), h + 0.032), 'galv'))
    # 皮带
    p.append(box(L - 0.02, bw, 0.012, (cx, y, h - 0.006), 'rubber'))
    # 端部滚筒
    for xe in (x0 + 0.02, x1 - 0.02):
        p.append(cyl(0.035, bw + 0.04, (xe, y, h - 0.035), 'y', 'stain', 26))
    # 支腿
    n = max(2, int(L / 1.1) + 1)
    for i in range(n):
        x = x0 + 0.08 + i * (L - 0.16) / (n - 1)
        for sy in (-1, 1):
            p.append(box(0.055, 0.055, h - 0.10, (x, y + sy * (bw / 2 + 0.03), (h - 0.10) / 2), 'alu'))
            p.append(box(0.09, 0.09, 0.012, (x, y + sy * (bw / 2 + 0.03), 0.006), 'steel'))
        # 横撑
        p.append(box(0.04, bw + 0.06, 0.04, (x, y, 0.16), 'alu'))
    # 挡停气缸 + 光电
    for xs in (P_SPRAY[0], P_PICK[0]):
        p.append(cyl(0.016, 0.05, (xs, y - bw / 2 + 0.06, h + 0.03), 'z', 'steel', 14))
        p.append(box(0.03, 0.075, 0.05, (xs, y - bw / 2 + 0.06, h + 0.075), 'dark'))
        p.append(box(0.022, 0.022, 0.03, (xs - 0.20, y + bw / 2 + 0.02, h + 0.06), 'black'))
    return p


# ---------------- 喷涂工位支架 ----------------
def spray_stand():
    p = []
    cx, cy, h = P_SPRAY[0], P_SPRAY[1], P_SPRAY[2]
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(box(0.05, 0.05, h - 0.02, (cx + sx * 0.22, cy + sy * 0.16, (h - 0.02) / 2), 'steel'))
            p.append(box(0.10, 0.10, 0.012, (cx + sx * 0.22, cy + sy * 0.16, 0.006), 'steel'))
    p.append(box(0.56, 0.46, 0.025, (cx, cy, h - 0.012), 'galv'))
    p.append(box(0.50, 0.05, 0.045, (cx, cy - 0.205, h + 0.018), 'galv'))   # 挡边
    p.append(box(0.50, 0.05, 0.045, (cx, cy + 0.205, h + 0.018), 'galv'))
    # 台面中央的定位销（工件对中）
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(cyl(0.012, 0.02, (cx + sx * 0.13, cy + sy * 0.09, h + 0.02), 'z', 'steel', 10))
    for sx in (-1, 1):
        p.append(box(0.04, 0.36, 0.04, (cx + sx * 0.22, cy, 0.10), 'steel'))
    return p


# ---------------- 托盘与垛型 ----------------
def pallet(cx, cy, z=0.0):
    """1200 x 1000 四向进叉木托盘，上表面 150 mm。"""
    L, W, H = PALLET
    p = []
    # 顶板 5 条（沿 X 向长条，Y 向排布）
    for i in range(5):
        yy = cy - W / 2 + W / 10 + i * W / 5
        p.append(box(L, W / 5 * 0.86, 0.022, (cx, yy, z + H - 0.011), 'wood'))
    # 纵梁 3 条
    for i in (-1, 0, 1):
        p.append(box(L, 0.09, 0.09, (cx, cy + i * (W / 2 - 0.06), z + H - 0.067), 'wood2'))
    # 底板 3 条
    for i in (-1, 0, 1):
        p.append(box(L, 0.10, 0.022, (cx, cy + i * (W / 2 - 0.05), z + 0.011), 'wood'))
    # 垫块
    for sx in (-1, 0, 1):
        for sy in (-1, 0, 1):
            p.append(box(0.10, 0.09, 0.09,
                         (cx + sx * (L / 2 - 0.07), cy + sy * (W / 2 - 0.06), z + H - 0.067), 'wood2'))
    return p


def stack(cx, cy, n_layer=5):
    """3 列 x 4 行 x n 层，偶数层 X 向偏移 125 mm。"""
    p = []
    Lb, Wb, Hb = CARTON
    for k in range(n_layer):
        off = 0.125 if k % 2 == 1 else 0.0
        z = 0.15 + Hb / 2 + k * Hb
        for i in range(3):
            for j in range(4):
                x = cx - 0.6 + Lb / 2 + i * Lb + off
                y = cy - 0.5 + Wb / 2 + j * Wb
                p += carton(x, y, z, mk='card' if (i + j + k) % 2 == 0 else 'card_b')
    return p


# ---------------- 换枪架 ----------------
def tool_rack():
    p = []
    x, y, z = P_DOCK
    p.append(box(0.10, 0.10, z, (x, y, z / 2), 'steel'))
    p.append(box(0.16, 0.16, 0.012, (x, y, 0.006), 'steel'))
    p.append(box(0.08, 0.86, 0.08, (x, y, z + 0.04 - 0.04), 'dark'))  # 立柱
    # 横梁（两个工具位，间距 400）
    p.append(box(0.07, 0.44, 0.06, (x, y, z - 0.02), 'dark'))
    for dy, tool in ((-0.20, 'spray'), (0.20, 'grip')):
        # 工具座
        p.append(cyl(0.055, 0.05, (x + 0.02, y + dy, z - 0.03), 'z', 'steel', 24))
        p.append(box(0.10, 0.09, 0.03, (x + 0.02, y + dy, z - 0.065), 'alu'))
        T = T_trans((x + 0.02, y + dy, z - 0.08)) @ T_roty(-np.pi / 2)
        p += apply(tool_spray() if tool == 'spray' else tool_gripper(), T)
    return p


# ---------------- 控制柜 ----------------
def cabinet():
    p = []
    x, y, z = P_CAB
    W, D, H = 0.98, 0.72, 1.78
    p.append(box(W, D, H, (x, y, H / 2), 'white2'))
    p.append(box(W + 0.03, D + 0.03, 0.02, (x, y, H + 0.01), 'dark'))
    p.append(box(W + 0.03, D + 0.03, 0.05, (x, y, 0.025), 'dark'))
    # 门缝与把手
    p.append(box(0.006, D * 0.9, H * 0.92, (x - W / 2 - 0.002, y, H * 0.48), 'dark2'))
    for dy in (-0.18, 0.18):
        p.append(box(0.02, 0.02, 0.16, (x - W / 2 - 0.012, y + dy, H * 0.55), 'steel'))
    # 显示屏 + 急停
    p.append(box(0.005, 0.26, 0.20, (x - W / 2 - 0.004, y + 0.02, H * 0.80), 'screen'))
    p.append(cyl(0.035, 0.03, (x - W / 2 - 0.02, y - 0.26, H * 0.80), 'x', 'red', 22))
    # 顶部风扇罩
    p.append(cyl(0.09, 0.05, (x + 0.2, y, H + 0.035), 'z', 'dark', 20))
    # 铭牌
    p.append(box(0.003, 0.12, 0.05, (x - W / 2 - 0.003, y + 0.24, H * 0.62), 'steel'))
    return p


# ---------------- 安全围栏 ----------------
def mesh_panel(x0, x1, y, h, step=0.36):
    p = []
    for x in np.arange(x0 + step, x1 - 0.01, step):
        p.append(box(0.006, 0.006, h - 0.20, (x, y, h / 2), 'mesh'))
    for z in np.arange(0.22, h - 0.18, step):
        p.append(box(x1 - x0, 0.006, 0.006, ((x0 + x1) / 2, y, z), 'mesh'))
    return p


def mesh_panel_side(x, y0, y1, h, step=0.36):
    p = []
    for y in np.arange(y0 + step, y1 - 0.01, step):
        p.append(box(0.006, 0.006, h - 0.20, (x, y, h / 2), 'mesh'))
    for z in np.arange(0.22, h - 0.18, step):
        p.append(box(0.006, y1 - y0, 0.006, (x, (y0 + y1) / 2, z), 'mesh'))
    return p


def fence(x0=-1.42, x1=3.88, y0=-1.98, y1=1.98, h=2.0, door_y=1.42):
    """立柱 + 上下横杆；远侧加网格板，近侧留空以便观察。"""
    p = []
    posts = []
    for x in np.arange(x0, x1 + 0.01, 1.05):
        posts.append((x, y0))
        posts.append((x, y1))
    for y in np.arange(y0, y1 + 0.01, 1.05):
        posts.append((x0, y))
        posts.append((x1, y))
    for (x, y) in posts:
        p.append(box(0.06, 0.06, h, (x, y, h / 2), 'mesh'))
        p.append(box(0.13, 0.13, 0.014, (x, y, 0.007), 'steel'))
    # 横杆
    for y in (y0, y1):
        p.append(box(x1 - x0, 0.045, 0.045, ((x0 + x1) / 2, y, h - 0.03), 'mesh'))
        p.append(box(x1 - x0, 0.04, 0.04, ((x0 + x1) / 2, y, 0.16), 'mesh'))
    for x in (x0, x1):
        p.append(box(0.045, y1 - y0, 0.045, (x, (y0 + y1) / 2, h - 0.03), 'mesh'))
        p.append(box(0.04, y1 - y0, 0.04, (x, (y0 + y1) / 2, 0.16), 'mesh'))
    # 网格片：仅远侧，用细杆近似焊接网
    p += mesh_panel(x0, x1, y0, h)
    p += mesh_panel_side(x0, y0, y1, h)
    # 检修门（y=+1.42 侧）
    p.append(box(0.09, 0.09, h, (0.45, door_y, h / 2), 'mesh'))
    p.append(box(0.09, 0.09, h, (1.35, door_y, h / 2), 'mesh'))
    p.append(box(0.90, 0.045, 0.045, (0.90, door_y, h - 0.06), 'mesh'))
    p.append(box(0.90, 0.008, h - 0.30, (0.90, door_y, h / 2), 'panel'))
    # 门锁与警示牌
    p.append(box(0.05, 0.05, 0.10, (1.30, door_y - 0.03, 1.05), 'steel'))
    p.append(box(0.28, 0.005, 0.20, (0.90, door_y - 0.02, 1.55), 'sign'))
    return p
