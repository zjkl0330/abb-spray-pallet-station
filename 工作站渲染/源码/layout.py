"""按论文表 3-3 坐标绘制工作站平面布局图（CAD 风格，带尺寸标注）。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Polygon
import numpy as np
import matplotlib.font_manager as fm

for f in ['/tmp/NotoSansSC-Regular.otf', '/tmp/NotoSansSC-Bold.otf']:
    try:
        fm.fontManager.addfont(f)
    except Exception as e:
        print('font add failed', e)
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

C_LINE = '#1a1a1a'
C_FILL = '#e8e8e6'
C_ACC = '#b3261e'


def dim(ax, p1, p2, text, off=0.0, fs=8.5, vertical=False):
    """尺寸线 + 箭头 + 数值。"""
    p1, p2 = np.array(p1, float), np.array(p2, float)
    if vertical:
        p1 = p1 + [off, 0]
        p2 = p2 + [off, 0]
    else:
        p1 = p1 + [0, off]
        p2 = p2 + [0, off]
    ax.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle='<|-|>', color=C_ACC, lw=0.9,
                                shrinkA=0, shrinkB=0, mutation_scale=7))
    mid = (p1 + p2) / 2
    ax.text(mid[0], mid[1], text, color=C_ACC, fontsize=fs, ha='center', va='center',
            bbox=dict(fc='white', ec='none', pad=1.2))


def main():
    fig, ax = plt.subplots(figsize=(11.2, 8.2), dpi=200)
    ax.set_aspect('equal')

    # 地面与围栏
    ax.add_patch(Rectangle((-3.3, -2.6), 8.4, 5.4, fc='#f7f7f5', ec='none', zorder=0))
    ax.add_patch(Rectangle((-1.42, -1.98), 3.88 + 1.42, 3.96, fc='#fdfdfb',
                           ec='#b08a20', lw=1.6, zorder=1))
    ax.text(-1.38, 2.06, '安全围栏  h=2000', fontsize=8, color='#8a6a12')

    # 输送链
    for x0, x1 in [(0.46, 0.74), (1.06, 3.60)]:
        ax.add_patch(Rectangle((x0, -0.20), x1 - x0, 0.40, fc='#d8d8d4', ec=C_LINE, lw=0.8, zorder=3))
    for i in range(6):
        ax.plot([0.52 + i * 0.52, 0.52 + i * 0.52], [-0.19, 0.19], color='#b9b9b4', lw=0.6, zorder=4)

    # 喷涂工位台
    ax.add_patch(Rectangle((0.62, -0.23), 0.56, 0.46, fc='#c9ccc9', ec=C_LINE, lw=1.0, zorder=5))
    # 工件（喷涂位）
    ax.add_patch(Rectangle((0.90 - 0.175, -0.125), 0.35, 0.25, fc='#c9a173', ec=C_LINE, lw=0.9, zorder=6))
    # 工件（取料位）
    ax.add_patch(Rectangle((1.60 - 0.175, -0.125), 0.35, 0.25, fc='#c9a173', ec=C_LINE, lw=0.9, zorder=6))

    # 托盘 + 垛
    ax.add_patch(Rectangle((-0.60, -1.60), 1.20, 1.00, fc='#b99a6b', ec=C_LINE, lw=1.2, zorder=3))
    for k in range(5):
        off = 0.125 if k % 2 else 0.0
        for i in range(3):
            for j in range(4):
                x = -0.60 + i * 0.35 + off
                y = -1.60 + j * 0.25
                ax.add_patch(Rectangle((x, y), 0.35, 0.25,
                                       fc='none', ec='#6b5a3e', lw=0.35, alpha=0.55, zorder=4))


    # 机器人：基座 + 工作半径 + 臂
    R0 = 0.28
    ax.add_patch(Circle((0, 0), R0, fc='#efefec', ec=C_LINE, lw=1.2, zorder=7))
    ax.add_patch(Circle((0, 0), 0.20, fc='#dcdcd8', ec=C_LINE, lw=0.6, zorder=8))
    ax.add_patch(Circle((0, 0), 2.05, fc='none', ec='#4a6fa5', lw=1.0, ls=(0, (5, 3)), zorder=2))
    ax.text(1.45, 1.42, 'R2050 工作范围', fontsize=7.6, color='#31527d', rotation=-32)
    # 臂（示意摆向喷涂工位）
    ax.plot([0, 0.55], [0, 0.26], color='#3a3a38', lw=6, solid_capstyle='round', zorder=9)
    ax.plot([0.55, 0.90], [0.26, 0.04], color='#3a3a38', lw=4.2, solid_capstyle='round', zorder=9)
    ax.add_patch(Circle((0.55, 0.26), 0.05, fc='#8a8a86', ec='#3a3a38', lw=0.6, zorder=10))
    ax.add_patch(Circle((0.90, 0.04), 0.035, fc='#c9a173', ec='#3a3a38', lw=0.6, zorder=10))
    ax.text(0.02, -0.74, 'IRB 4600-20/2.05', fontsize=8, ha='center', color=C_LINE)

    # 换枪架
    ax.add_patch(Rectangle((-0.94, -0.66), 0.08, 0.12, fc='#8a8a86', ec=C_LINE, lw=0.8, zorder=6))
    for dy in (-0.20, 0.20):
        ax.add_patch(Circle((-0.88, -0.60 + dy), 0.045, fc='#c0c0bc', ec=C_LINE, lw=0.7, zorder=7))
    ax.plot([-0.90, -0.90], [-0.80, -0.40], color=C_LINE, lw=2.2, zorder=6)

    # 控制柜
    ax.add_patch(Rectangle((-1.60 - 0.49, 0.90 - 0.36), 0.98, 0.72, fc='#dededa', ec=C_LINE, lw=1.0, zorder=5))
    ax.plot([-2.09, -1.11], [0.90, 0.90], color='#9a9a96', lw=0.6, zorder=6)

    # 检修门
    ax.plot([0.45, 1.35], [1.98, 1.98], color=C_ACC, lw=2.4, zorder=6)
    ax.text(0.90, 2.04, '检修门 900', fontsize=7.4, color=C_ACC, ha='center')

    # ---- 尺寸标注 ----
    dim(ax, (0, 0.30), (0.90, 0.30), '900', off=0.0)
    dim(ax, (0.90, 0.30), (1.60, 0.30), '700', off=0.0)
    dim(ax, (0, -0.36), (1.60, -0.36), '1600（基座至取料位）', off=0.0)
    dim(ax, (0.46, 0.40), (3.60, 0.40), '3300（输送链长）', off=0.0)
    dim(ax, (-0.60, -1.82), (0.60, -1.82), '1200', off=0.0)
    dim(ax, (0.72, -1.60), (0.72, -0.60), '1000', off=0.0, vertical=True)
    dim(ax, (-1.24, 0), (-1.24, -1.10), '1100', off=0.0, vertical=True)
    dim(ax, (-0.88, -0.46), (0, -0.46), '900（至换枪架）', off=0.0)

    # ---- 编号 ----
    tags = [(0.90, 0.64, '1'), (1.60, 0.64, '2'), (-0.62, 0.66, '3'),
            (-1.36, -0.62, '4'), (-1.60, 1.42, '5'), (0.20, 1.78, '6'), (3.40, 0.64, '7')]
    for x, y, s in tags:
        ax.add_patch(Circle((x, y), 0.115, fc='white', ec=C_LINE, lw=0.9, zorder=12))
        ax.text(x, y, s, fontsize=9, ha='center', va='center', zorder=13)

    # 图例
    legend = ('1 喷涂工位    2 码垛取料位    3 机器人\n'
              '4 换枪架      5 控制柜        6 安全围栏\n'
              '7 输送链（带速 0.15 m/s）\n'
              '托盘 1200×1000，垛型 3×4×5（60 箱），垛高 1400')
    ax.text(-3.25, -2.62, legend, fontsize=8.0, va='top', ha='left',
            bbox=dict(fc='white', ec='#bbbbbb', lw=0.7, pad=6))

    # 坐标轴指示
    ax.annotate('', xy=(3.95, -2.42), xytext=(3.55, -2.42),
                arrowprops=dict(arrowstyle='-|>', color=C_LINE, lw=1.2, mutation_scale=10))
    ax.annotate('', xy=(3.55, -2.02), xytext=(3.55, -2.42),
                arrowprops=dict(arrowstyle='-|>', color=C_LINE, lw=1.2, mutation_scale=10))
    ax.text(4.00, -2.46, 'X', fontsize=9)
    ax.text(3.50, -1.95, 'Y', fontsize=9)
    ax.text(2.05, -2.46, '世界坐标系（原点 = 机器人基座底面中心）', fontsize=7.4, color='#555')

    ax.set_xlim(-3.35, 4.15)
    ax.set_ylim(-2.78, 2.36)
    ax.axis('off')
    ax.set_title('图 3-1  ABB 喷涂-码垛复合工作站平面布局（单位：mm）',
                 fontsize=11.5, pad=8)
    plt.tight_layout()
    plt.savefig('/tmp/r3/F_layout.png', dpi=200, bbox_inches='tight', facecolor='white')
    print('saved')


if __name__ == '__main__':
    main()
