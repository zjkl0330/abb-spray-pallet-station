"""IRB 4600-20/2.05 运动学与几何，以及喷枪 / 真空夹爪两组末端工具。"""
import numpy as np
import trimesh

from geo import (M, box, cyl, beam, rod, apply, T_rotz, T_roty, T_trans)


class IRB4600:
    H1 = 0.44      # J2 高度（基座底面起）
    L1 = 0.78      # J2 -> J3
    L2 = 1.02      # J3 -> J5
    LW = 0.20      # J5 -> 法兰

    # ---------- 运动学 ----------
    def plan(self, q):
        """q1 尚未应用时的平面关节点（XZ 平面，+X 向前，+Z 向上）。"""
        q1, q2, q3, q4, q5, q6 = q
        a2, a3 = q2, q2 + q3
        a5 = q2 + q3 + q5
        j2 = np.array([0.0, 0.0, self.H1])
        j3 = j2 + self.L1 * np.array([np.cos(a2), 0, np.sin(a2)])
        j5 = j3 + self.L2 * np.array([np.cos(a3), 0, np.sin(a3)])
        fl = j5 + self.LW * np.array([np.cos(a5), 0, np.sin(a5)])
        return dict(j2=j2, j3=j3, j5=j5, fl=fl, a2=a2, a3=a3, a5=a5, q1=q1)

    def world(self, q):
        P = self.plan(q)
        Rz = T_rotz(q[0])
        out = {}
        for k in ('j2', 'j3', 'j5', 'fl'):
            v = np.ones(4)
            v[:3] = P[k]
            out[k] = (Rz @ v)[:3]
        out.update({k: P[k] for k in ('a2', 'a3', 'a5')})
        return out

    def ik(self, tcp, tool_dir=(0, 0, -1), tool_len=0.0, elbow=-1):
        """TCP 目标 + 工具指向 -> 关节角。工具沿法兰 +X 伸出，与 J5 臂同轴。"""
        dirv = np.array(tool_dir, float)
        dirv = dirv / np.linalg.norm(dirv)
        flange = np.array(tcp, float) - dirv * tool_len
        j5 = flange - dirv * self.LW           # 手腕中心回退一节
        q1 = np.arctan2(j5[1], j5[0])
        rho = float(np.hypot(j5[0], j5[1]))
        dz = float(j5[2] - self.H1)
        d = float(np.hypot(rho, dz))
        d = min(d, self.L1 + self.L2 - 1e-3)
        c3 = np.clip((d * d - self.L1 ** 2 - self.L2 ** 2) / (2 * self.L1 * self.L2), -1, 1)
        q3 = elbow * np.arccos(c3)
        k = np.arctan2(self.L2 * np.sin(q3), self.L1 + self.L2 * np.cos(q3))
        q2 = np.arctan2(dz, rho) - k
        dir_r = float(np.hypot(dirv[0], dirv[1]))
        a5 = np.arctan2(dirv[2], dir_r if dir_r > 1e-6 else 0.0)
        q5 = a5 - (q2 + q3)
        q5 = (q5 + np.pi) % (2 * np.pi) - np.pi
        return [q1, q2, q3, 0.0, q5, 0.0]

    # ---------- 几何 ----------
    def build(self, q, body='white'):
        P = self.plan(q)
        q1 = q[0]
        parts = []

        # 底座（世界坐标，不随 J1 旋转）
        parts += [
            box(0.56, 0.56, 0.05, (0, 0, 0.025), 'dark'),
            box(0.44, 0.44, 0.19, (0, 0, 0.145), body),
            box(0.49, 0.49, 0.02, (0, 0, 0.24), 'dark'),
        ]
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box(0.085, 0.085, 0.014, (sx * 0.225, sy * 0.225, 0.007), 'steel'))
                parts.append(cyl(0.016, 0.03, (sx * 0.225, sy * 0.225, 0.03), 'z', 'steel', 12))

        # J1 转座
        body1 = [
            cyl(0.255, 0.035, (0, 0, 0.26), 'z', 'dark', 44),
            cyl(0.238, 0.17, (0, 0, 0.345), 'z', body, 44),
            box(0.335, 0.40, 0.295, (0.025, 0, 0.452), body),
            cyl(0.118, 0.375, (0.030, 0, self.H1), 'y', 'dark', 36),
            cyl(0.062, 0.40, (0.030, 0, self.H1), 'y', 'steel', 24),
            box(0.012, 0.20, 0.085, (-0.122, 0, 0.455), 'red'),
            cyl(0.082, 0.19, (-0.155, 0, 0.415), 'x', 'dark', 26),
            cyl(0.028, 0.03, (0.16, 0.06, 0.34), 'z', 'steel', 12),
        ]
        parts += apply(body1, T_rotz(q1))

        # 下臂 J2 -> J3
        arm1 = [
            beam(self.L1 - 0.02, 0.30, 0.255, 0.215, 0.185, x0=0.02, mk=body),
            cyl(0.118, 0.30, (0, 0, 0), 'y', body, 36),
            cyl(0.098, 0.062, (0, 0.178, 0), 'y', 'dark', 26),
            cyl(0.098, 0.062, (0, -0.178, 0), 'y', 'dark', 26),
            box(0.10, 0.20, 0.022, (0.34, 0, 0.148), 'dark'),
        ]
        parts += apply(arm1, T_rotz(q1) @ T_trans(P['j2']) @ T_roty(-P['a2']))

        # 上臂 J3 -> J5
        arm2 = [
            beam(self.L2 - 0.06, 0.225, 0.195, 0.135, 0.125, x0=0.03, mk=body),
            cyl(0.092, 0.27, (0, 0, 0), 'y', 'dark', 30),
            cyl(0.055, 0.29, (0, 0, 0), 'y', body, 24),
            box(0.30, 0.012, 0.055, (0.45, 0.101, 0.02), 'dark'),
            box(0.115, 0.004, 0.040, (0.30, 0.098, -0.055), 'red'),
            cyl(0.078, 0.012, (0.92, 0, 0), 'y', 'dark', 24),
        ]
        parts += apply(arm2, T_rotz(q1) @ T_trans(P['j3']) @ T_roty(-P['a3']))

        # 手腕 J5 -> 法兰
        wr = [
            beam(self.LW, 0.135, 0.125, 0.098, 0.095, mk=body),
            cyl(0.068, 0.185, (0, 0, 0), 'y', 'dark', 26),
            cyl(0.048, 0.10, (0.055, 0, 0), 'x', body, 26),
            cyl(0.050, 0.024, (self.LW + 0.012, 0, 0), 'x', 'steel', 30),
            cyl(0.012, 0.03, (self.LW + 0.02, 0.028, 0), 'x', 'steel', 10),
        ]
        parts += apply(wr, T_rotz(q1) @ T_trans(P['j5']) @ T_roty(-P['a5']))

        # 线缆：沿上臂外侧走线，从上臂根部到手腕
        cab = self._cables(P)
        parts += apply(cab, T_rotz(q1))

        Tf = T_rotz(q1) @ T_trans(P['fl']) @ T_roty(-P['a5'])
        return parts, Tf

    def _cables(self, P):
        """在 XZ 平面内用折线近似线缆走向，附加到上臂与手腕两侧。"""
        out = []
        a3, a5 = P['a3'], P['a5']
        d3 = np.array([np.cos(a3), 0, np.sin(a3)])
        d5 = np.array([np.cos(a5), 0, np.sin(a5)])
        n3 = np.array([-np.sin(a3), 0, np.cos(a3)])
        j3, j5 = P['j3'], P['j5']
        for side, off in ((1, 0.098), (-1, 0.098)):
            y = off * side
            p0 = j3 + np.array([0, y * 0.85, 0]) - d3 * 0.02 + n3 * 0.02
            p1 = j3 + d3 * self.L2 * 0.55 + n3 * 0.055 + np.array([0, y * 0.72, 0])
            p2 = j5 - d5 * 0.05 + n3 * 0.045 + np.array([0, y * 0.62, 0])
            p3 = j5 + d5 * 0.10 + np.array([0, y * 0.5, 0])
            for a, b in ((p0, p1), (p1, p2), (p2, p3)):
                g = rod(a, b, 0.016, 'rubber', 8)
                if g:
                    out.append(g)
        return out


# ---------------- 末端工具 ----------------
SPRAY_TCP = 0.22
GRIP_TCP = 0.18


def tool_spray():
    """空气喷枪：TCP 在喷嘴出口，沿 +X。"""
    p = [
        cyl(0.050, 0.022, (0.011, 0, 0), 'x', 'steel', 30),
        box(0.075, 0.072, 0.072, (0.062, 0, 0), 'dark'),
        box(0.030, 0.045, 0.10, (0.075, 0, 0.075), 'steel'),
        cyl(0.017, 0.085, (0.140, 0, 0), 'x', 'steel', 20),
        cyl(0.024, 0.030, (0.196, 0, 0), 'x', 'stain', 24),
        cyl(0.012, 0.014, (0.214, 0, 0), 'x', 'steel', 16),
        # 供漆/供气管
        rod((0.05, 0.03, 0.03), (0.03, 0.10, 0.12), 0.008, 'cu', 10),
        rod((0.05, -0.03, 0.03), (0.03, -0.105, 0.10), 0.008, 'black', 10),
        rod((0.03, 0.10, 0.12), (0.005, 0.115, 0.045), 0.008, 'cu', 10),
        rod((0.03, -0.105, 0.10), (0.005, -0.12, 0.035), 0.008, 'black', 10),
    ]
    return p


def tool_gripper():
    """单吸盘真空夹爪：TCP 在吸盘表面，沿 +X。"""
    p = [
        cyl(0.050, 0.022, (0.011, 0, 0), 'x', 'steel', 30),
        cyl(0.075, 0.035, (0.040, 0, 0), 'x', 'dark', 30),
        cyl(0.062, 0.055, (0.085, 0, 0), 'x', 'alu', 30),
        cyl(0.105, 0.016, (0.120, 0, 0), 'x', 'alu', 36),
        cyl(0.098, 0.014, (0.135, 0, 0), 'x', 'rubber', 36),
        cyl(0.052, 0.040, (0.166, 0, 0), 'x', 'rubber', 28),
        cyl(0.048, 0.012, (0.176, 0, 0), 'x', 'black', 28),
        rod((0.045, 0.045, 0.02), (0.02, 0.075, 0.075), 0.010, 'alu', 10),
        rod((0.02, 0.075, 0.075), (0.0, 0.045, 0.075), 0.010, 'black', 10),
    ]
    return p


# ---------------- 工件 ----------------
def carton(cx, cy, cz, L=0.35, W=0.25, H=0.25, yaw=0.0, mk='card'):
    """纸箱：箱体 + 上下封箱胶带 + 正面面单。"""
    L, W, H = L - 0.002, W - 0.002, H - 0.002
    p = [
        box(L, W, H, (0, 0, 0), mk),
        box(L * 0.995, 0.048, H + 0.001, (0, 0, 0), 'tape'),
        box(L + 0.001, W * 0.995, 0.048, (0, 0, H / 2 - 0.024), 'tape'),
        box(0.11, 0.004, 0.075, (L * 0.18, -W / 2 - 0.001, 0.01), 'label'),
    ]
    T = T_trans((cx, cy, cz)) @ T_rotz(yaw)
    return apply(p, T)
