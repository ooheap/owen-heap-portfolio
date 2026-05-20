"""
Kings of the Court – v3
Black background, zone grid lines, progressive arc draw/retract, text at top.
"""

import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb

from importlib import import_module
_z = import_module("02_zones_and_leaders")
assign_zone = _z.assign_zone
ZONE_ORDER  = _z.ZONE_ORDER

ARC_3_RADIUS  = 237.5
CORNER_3_X    = 220
CORNER_Y_LIMIT = 140
PAINT_TOP_Y   = 190
CENTER_COL_X  = 60
WING_ANGLE    = 20          # degrees from the y-axis

# ── Palette ──────────────────────────────────────────────────────────────────
BLACK       = "#000000"
COURT_LINE  = "#3a3a3a"     # dim gray court lines
ACTIVE_RGBA = (0.15, 0.15, 0.15, 0.40)   # dark gray, 40% — same every time
TEXT_HI     = "#e8e8e8"
TEXT_LO     = "#555555"
ARC_COLOR   = "#39ff14"     # neon green

# ── Timing (frames @ 30 fps) ─────────────────────────────────────────────────
FPS      = 30
T_INTRO  = 8     # zone highlights, text appears
T_IN     = 22    # arcs draw in  (shot → basket)
T_HOLD   = 14    # all arcs fully visible
T_OUT    = 16    # arcs retract  (basket → shot)
T_PAUSE  = 6     # zone dims before next
FPZ      = T_INTRO + T_IN + T_HOLD + T_OUT + T_PAUSE   # 66 frames ≈ 2.2 s
END_HOLD = 45

_B_IN_S  = T_INTRO
_B_IN_E  = _B_IN_S + T_IN
_B_HLD_E = _B_IN_E + T_HOLD
_B_OUT_E = _B_HLD_E + T_OUT

# Court clipped at this y — just above the 3pt arc peak
YMAX = 272
# Text sits above the court in the same axes
TEXT_TOP = YMAX + 10

# ── Court ────────────────────────────────────────────────────────────────────
def draw_court(ax):
    kw = dict(color=COURT_LINE, lw=1.3, zorder=4)
    # Hoop + backboard
    ax.add_patch(Circle((0, 0), 7.5, fill=False, **kw))
    ax.add_patch(Rectangle((-30, -7.5), 60, -1, color=COURT_LINE, lw=1.3, zorder=4))
    # Paint box
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, fill=False, **kw))
    # Free-throw arc
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0,   theta2=180, **kw))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=0,
                     linestyle="dashed", **kw))
    # Restricted area
    ax.add_patch(Arc((0, 0), 80, 80, theta1=0, theta2=180, **kw))
    # 3pt line: corner straights + arc
    ax.plot([-CORNER_3_X, -CORNER_3_X], [-47.5, 92.5], **kw)
    ax.plot([ CORNER_3_X,  CORNER_3_X], [-47.5, 92.5], **kw)
    ax.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, **kw))
    # 3 sides of outer boundary (no half-court top edge)
    ax.plot([-250, 250], [-47.5, -47.5], **kw)          # baseline
    ax.plot([-250, -250], [-47.5, YMAX], **kw)           # left sideline
    ax.plot([ 250,  250], [-47.5, YMAX], **kw)           # right sideline




# ── Zone grid (for active-zone fill) ─────────────────────────────────────────
_GRID_RES = 240

def _build_grid():
    xs = np.linspace(-250, 250, _GRID_RES)
    ys = np.linspace(-47.5, YMAX, _GRID_RES)
    XX, YY = np.meshgrid(xs, ys)
    grid = np.vectorize(assign_zone)(XX.ravel(), YY.ravel()).reshape(XX.shape)
    return xs, ys, grid


def _active_rgba(grid, active_zone=None):
    H, W = grid.shape
    img = np.zeros((H, W, 4), dtype=float)
    if active_zone is not None:
        mask = grid == active_zone
        img[mask] = ACTIVE_RGBA
    return img


# ── Bezier arc points (shot → basket) ────────────────────────────────────────
N_PTS = 28

def _bezier_pts(x, y, n=N_PTS):
    """
    Quadratic Bezier from shot location (x,y) to basket (0,0).
    Control point placed between shot and basket, moderately elevated,
    so the arc clearly reads as going INTO the rim.
    """
    dist = math.hypot(x, y)
    cx = x * 0.38                        # 62% toward basket horizontally
    cy = max(y, 0) + dist * 0.30         # moderate arc height
    t  = np.linspace(0, 1, n)
    bx = (1 - t)**2 * x + 2*t*(1 - t)*cx
    by = (1 - t)**2 * y + 2*t*(1 - t)*cy
    # bx[-1], by[-1] = 0, 0 naturally (t=1 term is 0)
    return bx, by


# ── Main ─────────────────────────────────────────────────────────────────────
def animate_zone_leaders(shots_df, leaders_df,
                         out_path="kings_of_the_court.mp4",
                         season="2025-26"):

    # Extra vertical space above court cut for text labels
    YTEXT_ZONE   = TEXT_TOP + 58
    YTEXT_NAME   = TEXT_TOP + 40
    YTEXT_STATS  = TEXT_TOP + 22

    fig, ax = plt.subplots(figsize=(7.0, 7.5), dpi=130)
    fig.patch.set_facecolor(BLACK)
    ax.set_facecolor(BLACK)

    draw_court(ax)

    ax.set_xlim(-260, 260)
    ax.set_ylim(-60, YTEXT_ZONE + 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Text labels (inside axes, above the court cut line)
    t_zone  = ax.text(0, YTEXT_ZONE,  "", ha="center", va="top",
                      color=TEXT_LO,  fontsize=8,  fontfamily="DejaVu Sans", zorder=7)
    t_name  = ax.text(0, YTEXT_NAME,  "", ha="center", va="top",
                      color=TEXT_HI,  fontsize=13, fontweight="bold",
                      fontfamily="DejaVu Sans", zorder=7)
    t_stats = ax.text(0, YTEXT_STATS, "", ha="center", va="top",
                      color=TEXT_LO,  fontsize=8.5, fontfamily="DejaVu Sans", zorder=7)

    # ── Zone overlay image
    print("Building zone grid...", end=" ", flush=True)
    xs_g, ys_g, grid = _build_grid()
    print("done")
    extent = [xs_g[0], xs_g[-1], ys_g[0], ys_g[-1]]

    print("Precomputing zone images...", end=" ", flush=True)
    zone_imgs = {None: _active_rgba(grid, None)}
    for z in ZONE_ORDER:
        zone_imgs[z] = _active_rgba(grid, z)
    print("done")

    zone_im = ax.imshow(zone_imgs[None], extent=extent, origin="lower",
                        aspect="auto", zorder=1, interpolation="nearest")

    # ── Shot data
    shots = shots_df.copy()
    shots["ZONE"] = shots.apply(lambda r: assign_zone(r["LOC_X"], r["LOC_Y"]), axis=1)

    # Pre-build one Line2D per made shot, alpha=0
    # Store bezier point arrays alongside each line
    zone_lines: dict[str, list] = {}
    zone_bx:    dict[str, list] = {}
    zone_by:    dict[str, list] = {}

    for _, ldr in leaders_df.iterrows():
        z = ldr["ZONE"]
        made = shots[
            (shots["ZONE"] == z) &
            (shots["PLAYER_ID"] == ldr["PLAYER_ID"]) &
            (shots["SHOT_MADE_FLAG"] == 1)
        ].reset_index(drop=True)

        lines, bxs, bys = [], [], []
        for _, row in made.iterrows():
            bx, by = _bezier_pts(row["LOC_X"], row["LOC_Y"])
            (line,) = ax.plot(bx[:1], by[:1],
                              color=ARC_COLOR, lw=1.1, alpha=0,
                              solid_capstyle="round", zorder=3)
            lines.append(line)
            bxs.append(bx)
            bys.append(by)

        zone_lines[z] = lines
        zone_bx[z]    = bxs
        zone_by[z]    = bys

    leaders_list = leaders_df.to_dict("records")
    total_frames = FPZ * len(leaders_list) + END_HOLD

    def _set_all_alpha(z, a):
        for ln in zone_lines[z]:
            ln.set_alpha(a)

    def _draw_progress(z, pts):
        """Show first `pts` Bezier points on every arc in zone z."""
        pts = max(2, pts)
        for ln, bx, by in zip(zone_lines[z], zone_bx[z], zone_by[z]):
            ln.set_data(bx[:pts], by[:pts])

    def update(frame):
        zi = frame // FPZ
        if zi >= len(leaders_list):
            if frame == FPZ * len(leaders_list):
                zone_im.set_data(zone_imgs[None])
                t_zone.set_text("")
                t_name.set_text("KINGS OF THE COURT")
                t_stats.set_text(f"{season}  |  12 zones  |  {len(shots_df):,} shots")
            return

        ldr   = leaders_list[zi]
        zone  = ldr["ZONE"]
        local = frame % FPZ

        # Zone entry
        if local == 0:
            zone_im.set_data(zone_imgs[zone])
            t_zone.set_text(zone.upper())
            t_name.set_text(ldr["PLAYER_NAME"])
            t_stats.set_text(
                f"{ldr['FGM']} / {ldr['FGA']} FGA   |   {ldr['FG_PCT']*100:.1f}% FG"
            )
            # Reset all arcs to invisible dot at shot location
            for ln, bx, by in zip(zone_lines[zone], zone_bx[zone], zone_by[zone]):
                ln.set_data(bx[:1], by[:1])
                ln.set_alpha(0)

        # DRAW IN: arcs grow from shot to basket
        if _B_IN_S <= local < _B_IN_E:
            t    = (local - _B_IN_S) / T_IN
            pts  = max(2, int(t * N_PTS))
            _draw_progress(zone, pts)
            _set_all_alpha(zone, 0.70)

        # HOLD: full arcs
        elif _B_IN_E <= local < _B_HLD_E:
            _draw_progress(zone, N_PTS)
            _set_all_alpha(zone, 0.70)

        # RETRACT: arcs shrink from basket back toward shot
        elif _B_HLD_E <= local < _B_OUT_E:
            t    = (local - _B_HLD_E) / T_OUT
            pts  = max(2, int((1 - t) * N_PTS))
            _draw_progress(zone, pts)
            _set_all_alpha(zone, 0.70)

        # PAUSE: arcs gone, zone dims
        elif local == _B_OUT_E:
            _set_all_alpha(zone, 0.0)
            zone_im.set_data(zone_imgs[None])

    anim = animation.FuncAnimation(
        fig, update, frames=total_frames, interval=1000 / FPS, blit=False
    )

    FFMPEG = (
        r"C:\Users\oohea\AppData\Local\Microsoft\WinGet\Packages"
        r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
    )
    if out_path.endswith(".gif"):
        anim.save(out_path, writer="pillow", fps=FPS)
    else:
        matplotlib.rcParams["animation.ffmpeg_path"] = FFMPEG
        anim.save(out_path, writer=animation.FFMpegWriter(fps=FPS), dpi=130)
    plt.close(fig)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    shots   = pd.read_parquet("shots_2025-26.parquet")
    leaders = pd.read_parquet("leaders_2025-26.parquet")
    animate_zone_leaders(shots, leaders)
