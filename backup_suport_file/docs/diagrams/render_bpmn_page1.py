#!/usr/bin/env python3
"""Render BPMN page 1 to PNG using matplotlib."""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "BPMN_01_DangKy_DangNhap.png")
LANES = ["Người dùng", "Ứng dụng Android", "Backend API", "Cơ sở dữ liệu"]
LX, LY, LW, LH, GAP = 0.8, 1.0, 0.9, 1.6, 0.02


def ly(i):
    return LY + (len(LANES) - 1 - i) * (LH + GAP)


def box(ax, x, lane, text, w=2.0, h=0.48):
    y = ly(lane) + (LH - h) / 2
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.06",
                                ec="black", fc="white", lw=1.2, zorder=3))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=7.5, zorder=4)
    return (x + w, y + h/2), (x, y + h/2)


def diamond(ax, x, lane, text, s=0.72):
    y = ly(lane) + (LH - s) / 2
    cx, cy = x + s/2, y + s/2
    ax.add_patch(Polygon([(cx, y+s), (x+s, cy), (cx, y), (x, cy)], closed=True,
                         ec="black", fc="white", lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=6.5, zorder=4)
    return (x+s, cy), (x, cy), (cx, y+s), (cx, y)


def dot_start(ax, x, lane):
    cy = ly(lane) + LH/2
    ax.add_patch(Circle((x, cy), 0.1, fc="black", zorder=3))
    return (x, cy)


def dot_end(ax, x, lane):
    cy = ly(lane) + LH/2
    ax.add_patch(Circle((x, cy), 0.16, fc="white", ec="black", lw=2, zorder=3))
    ax.add_patch(Circle((x, cy), 0.07, fc="black", zorder=4))
    return (x, cy)


def arr(ax, a, b, label=""):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, lw=1,
                                 color="black", shrinkA=2, shrinkB=2, zorder=2))
    if label:
        ax.text((a[0]+b[0])/2, (a[1]+b[1])/2 + 0.1, label, ha="center", fontsize=6.5, color="#444")


def main():
    fig, ax = plt.subplots(figsize=(20, 6.5))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("#efefef")
    ax.set_facecolor("#efefef")

    for gx in range(0, 25):
        ax.axvline(gx, color="#ddd", lw=0.25, zorder=0)
    for gy in range(0, 10):
        ax.axhline(gy, color="#ddd", lw=0.25, zorder=0)

    ax.text(12, 8.5, "1. Đăng ký và đăng nhập", ha="center", fontsize=14, fontweight="bold")

    pool_h = len(LANES) * (LH + GAP) - GAP
    ax.add_patch(FancyBboxPatch((LX, LY), 22, pool_h, boxstyle="square,pad=0",
                                ec="black", fc="#f5f5f5", lw=1.5, zorder=1))
    for i, name in enumerate(LANES):
        y = ly(i)
        ax.add_patch(FancyBboxPatch((LX, y), LW, LH, boxstyle="square,pad=0", ec="black", fc="white", lw=1, zorder=2))
        ax.text(LX + LW/2, y + LH/2, name, ha="center", va="center", fontsize=8, fontweight="bold", rotation=90)
        if i:
            ax.plot([LX, LX+22], [y, y], "k", lw=0.8, zorder=2)

    x = LX + LW + 0.4
    s = dot_start(ax, x, 0)
    r, _ = box(ax, x+0.25, 0, "Mở ứng dụng", 1.5)

    _, l_form = box(ax, x+2.0, 1, "Hiển thị form\nAuthActivity", 1.7)
    d_logged = diamond(ax, x+2.0, 1, "Đã đăng\nnhập?")
    r_main, _ = box(ax, x+3.5, 1, "Vào\nMainActivity", 1.4)
    e_ok = dot_end(ax, x+5.2, 1)

    d_mode = diamond(ax, x+3.5, 0, "ĐK hay\nĐN?")
    r_reg, _ = box(ax, x+4.6, 0, "Nhập thông tin\nđăng ký", 1.8)
    r_login, _ = box(ax, x+4.6, 0, "Nhập email\nvà mật khẩu", 1.7)
    ax.add_patch(FancyBboxPatch((x+4.6, ly(0)+0.08), 1.7, 0.42, boxstyle="round,pad=0.04,rounding_size=0.06",
                                 ec="black", fc="white", lw=1.2, zorder=3))
    ax.text(x+5.45, ly(0)+0.29, "Nhập email\nvà mật khẩu", ha="center", va="center", fontsize=7)

    r_val, _ = box(ax, x+6.6, 1, "Validate client\nAuthViewModel", 2.0)
    d_valid = diamond(ax, x+8.8, 1, "Hợp lệ?")
    _, l_err = box(ax, x+8.8, 0, "Hiển thị\nToast lỗi", 1.4)
    d_route = diamond(ax, x+10.2, 2, "ĐK hay\nĐN?")

    cy2 = ly(2) + LH/2
    ax.add_patch(FancyBboxPatch((x+11.5, cy2+0.18), 1.9, 0.42, boxstyle="round,pad=0.04,rounding_size=0.06",
                                 ec="black", fc="white", lw=1.2, zorder=3))
    ax.text(x+12.45, cy2+0.39, "POST /api/auth/register", ha="center", va="center", fontsize=7)
    d_email = diamond(ax, x+13.6, 2, "Email\ntồn tại?", s=0.68)
    _, l_create = box(ax, x+13.6, 3, "INSERT user\nbcrypt hash", 1.7)

    ax.add_patch(FancyBboxPatch((x+11.5, cy2-0.55), 1.7, 0.42, boxstyle="round,pad=0.04,rounding_size=0.06",
                                 ec="black", fc="white", lw=1.2, zorder=3))
    ax.text(x+12.35, cy2-0.34, "POST /api/auth/login", ha="center", va="center", fontsize=7)
    d_cred = diamond(ax, x+13.6, 2, "Đúng\nTK/MK?", s=0.68)

    r_jwt, _ = box(ax, x+15.0, 2, "Ký JWT\nsignToken", 1.3)
    r_sess, _ = box(ax, x+15.0, 1, "Lưu phiên\nSessionManager", 1.8)
    e_done = dot_end(ax, x+16.8, 0)

    arr(ax, s, (x+0.25, ly(0)+LH/2))
    arr(ax, r, d_logged[2])
    arr(ax, d_logged[0], r_main, "Có")
    arr(ax, r_main, e_ok)
    arr(ax, d_logged[3], l_form, "Không")
    arr(ax, (x+3.7, ly(1)+LH/2), d_mode[2])
    arr(ax, d_mode[0], r_reg, "ĐK")
    arr(ax, (x+3.86, ly(0)+0.35), (x+4.6, ly(0)+0.29), "ĐN")
    arr(ax, r_reg, r_val)
    arr(ax, (x+6.3, ly(0)+0.29), r_val)
    arr(ax, r_val, d_valid[2])
    arr(ax, d_valid[0], d_route[2], "Có")
    arr(ax, d_valid[3], l_err, "Không")
    arr(ax, d_route[0], (x+11.5, cy2+0.39), "ĐK")
    arr(ax, d_route[1], (x+11.5, cy2-0.34), "ĐN")
    arr(ax, (x+13.4, cy2+0.39), d_email[2])
    arr(ax, d_email[3], l_err, "Có")
    arr(ax, d_email[0], l_create, "Không")
    arr(ax, (x+13.4, cy2-0.34), d_cred[2])
    arr(ax, d_cred[0], r_jwt, "Có")
    arr(ax, d_cred[3], l_err, "Không")
    arr(ax, l_create, r_jwt)
    arr(ax, r_jwt, r_sess)
    arr(ax, r_sess, r_main)

    plt.tight_layout()
    plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Rendered: {OUT}")


if __name__ == "__main__":
    main()
