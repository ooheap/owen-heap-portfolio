"""
Kings of the Court – v2
Sleek dark animation: zone shading, staggered arc reveal/dismiss, clean layout.
"""

import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.colors import to_rgb

from importlib import import_module
_z = import_module("02_zones_and_leaders")
assign_zone = _z.assign_zone
ZONE_ORDER  = _z.ZONE_ORDER

# ── Palette ──────────────────────────────────────────────────────────────────
DARK_BG    = "#0b0d17"
COURT_FILL = "#16213e"
COURT_LINE = "#c8b99a"
TEXT_HI    = "#f0f0f0"
TEXT_LO    = "#6b7280"
ARC_COLOR  = "#39ff14"

ZONE_COLORS = {
    "Left Corner 3":         "#e63946",
    "Left Wing 3":           "#f4a261",
    "Top of Key 3":          "#ffd166",
    "Right Wing 3":          "#06d6a0",
    "Right Corner 3":        "#118ab2",
    "Left Baseline Mid":     "#c77dff",
    "Left Elbow Mid":        "#ff6b6b",
    "Center Mid (FT)":       "#4ecdc4",
    "Right Elbow Mid":       "#45b7d1",
    "Right Baseline Mid":    "#f9844a",
    "High Post / Far Paint": "#a8dadc",
    "Restricted Area":       "#ff006e",
}

# ── Timing (frames @ 30 fps) ─────────────────────────────────────────────────
FPS      = 30
T_INTRO  = 8    # zone highlights, label appears
T_IN     = 20   # arcs stagger in  (far → near)
T_HOLD   = 14   # all arcs visible
T_OUT    = 14   # arcs stagger out (near → far)
T_PAUSE  = 6    # zone dims, blank before next zone
FPZ      = T_INTRO + T_IN + T_HOLD + T_OUT + T_PAUSE   # 62 frames ≈ 2.1 s/zone
END_HOLD = 45

# Cumulative boundaries within a zone slot
_B_IN_S  = T_INTRO
_B_IN_E  = _B_IN_S + T_IN
_B_HLD_E = _B_IN_E + T_HOLD
_B_OUT_E = _B_HLD_E + T_OUT    # arcs fully gone here; T_PAUSE follows


# ── Court ────────────────────────────────────────────────────────────────────
def draw_court(ax):
    kw = dict(color=COURT_LINE, lw=1.5, zorder=4)
    ax.add_patch(Circle((0, 0), 7.5, fill=False, **kw))
    ax.add_patch(Rectangle((-30, -7.5), 60, -1, color=COURT_LINE, lw=1.5, zorder=4))
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, fill=False, **kw))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0,   theta2=180, **kw))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=0,
                     linestyle="dashed", **kw))
    ax.add_patch(Arc((0, 0), 80, 80, theta1=0, theta2=180, **kw))
    ax.plot([-220, -220], [-47.5, 92.5], **kw)
    ax.plot([ 220,  220], [-47.5, 92.5], **kw)
    ax.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, **kw))
    ax.plot([-250, 250], [422.5, 422.5], **kw)
    ax.add_patch(Arc((0, 422.5), 120, 120, theta1=180, theta2=0, **kw))
    ax.add_patch(Rectangle((-250, -47.5), 500, 470, fill=False, **kw))


# ── Zone grid ────────────────────────────────────────────────────────────────
_GRID_RES = 240

def _build_grid():
    xs = np.linspace(-250, 250, _GRID_RES)
    ys = np.linspace(-47.5, 422.5, _GRID_RES)
    XX, YY = np.meshgrid(xs, ys)
    grid = np.vectorize(assign_zone)(XX.ravel(), YY.ravel()).reshape(XX.shape)
    return xs, ys, grid


def _zone_rgba(grid, active=None):
    H, W = grid.shape
    img = np.zeros((H, W, 4), dtype=float)
    for zone, color in ZONE_COLORS.items():
        mask = grid == zone
        r, g, b = to_rgb(color)
        a = 0.55 if zone == active else 0.10
        img[mask] = (r, g, b, a)
    return img


# ── Arc geometry ─────────────────────────────────────────────────────────────
def _shot_arc(x, y):
    """Bezier from shot location → basket.
    Control point is pulled 80% toward the basket horizontally so the arc
    steepens sharply into the rim — reads unambiguously as going IN.
    """
    dist = math.hypot(x, y)
    cx = x * 0.20          # 80% of the way toward basket
    cy = dist * 0.52       # peak height proportional to shot distance
    return Path([(x, y), (cx, cy), (0., 0.)],
                [Path.MOVETO, Path.CURVE3, Path.CURVE3])


# ── Main ─────────────────────────────────────────────────────────────────────
def animate_zone_leaders(shots_df, leaders_df,
                         out_path="kings_of_the_court.mp4",
                         season="2025–26"):

    # Figure: court in upper 86%, text strip in lower 14%
    fig = plt.figure(figsize=(7.0, 9.8), dpi=130)
    fig.patch.set_facecolor(DARK_BG)
    fig.subplots_adjust(left=0.0, right=1.0, top=0.86, bottom=0.0)

    ax = fig.add_subplot(111)
    ax.set_facecolor(DARK_BG)

    # Court floor fill (under zone overlay and court lines)
    ax.add_patch(Rectangle((-250, -47.5), 500, 470,
                            facecolor=COURT_FILL, edgecolor="none", zorder=0))
    draw_court(ax)
    ax.set_xlim(-260, 260)
    ax.set_ylim(-60, 440)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Title (figure space — always above axes, never overlaps court)
    fig.text(0.5, 0.975, "KINGS OF THE COURT",
             ha="center", va="top", color=TEXT_HI,
             fontsize=13, fontweight="bold", fontfamily="DejaVu Sans")
    fig.text(0.5, 0.950, f"{season} NBA REGULAR SEASON",
             ha="center", va="top", color=TEXT_LO,
             fontsize=8.5, fontfamily="DejaVu Sans")

    # ── Info strip (figure space — below axes, never overlaps court)
    t_zone  = fig.text(0.5, 0.118, "",
                       ha="center", va="top", color=TEXT_LO,
                       fontsize=8, fontfamily="DejaVu Sans")
    t_name  = fig.text(0.5, 0.090, "",
                       ha="center", va="top", color=TEXT_HI,
                       fontsize=12, fontweight="bold", fontfamily="DejaVu Sans")
    t_stats = fig.text(0.5, 0.060, "",
                       ha="center", va="top", color=TEXT_LO,
                       fontsize=8.5, fontfamily="DejaVu Sans")

    # ── Zone overlay image
    print("Building zone grid…", end=" ", flush=True)
    xs_g, ys_g, grid = _build_grid()
    print("done")
    extent = [xs_g[0], xs_g[-1], ys_g[0], ys_g[-1]]

    print("Precomputing zone images…", end=" ", flush=True)
    zone_imgs = {None: _zone_rgba(grid, None)}
    for z in ZONE_ORDER:
        zone_imgs[z] = _zone_rgba(grid, z)
    print("done")

    zone_im = ax.imshow(zone_imgs[None], extent=extent, origin="lower",
                        aspect="auto", zorder=1, interpolation="nearest")

    # ── Shot data
    shots = shots_df.copy()
    shots["ZONE"] = shots.apply(lambda r: assign_zone(r["LOC_X"], r["LOC_Y"]), axis=1)
    shots["DIST"] = np.hypot(shots["LOC_X"], shots["LOC_Y"])

    # Pre-build arc patches per zone, sorted far→near for stagger reveal
    zone_arcs: dict[str, list] = {}
    for _, ldr in leaders_df.iterrows():
        z = ldr["ZONE"]
        made = shots[
            (shots["ZONE"] == z) &
            (shots["PLAYER_ID"] == ldr["PLAYER_ID"]) &
            (shots["SHOT_MADE_FLAG"] == 1)
        ].sort_values("DIST", ascending=False).reset_index(drop=True)

        plist = []
        for _, row in made.iterrows():
            p = PathPatch(_shot_arc(row["LOC_X"], row["LOC_Y"]),
                          facecolor="none", edgecolor=ARC_COLOR,
                          lw=1.2, alpha=0, capstyle="round", zorder=3)
            ax.add_patch(p)
            plist.append(p)
        zone_arcs[z] = plist

    leaders_list  = leaders_df.to_dict("records")
    total_frames  = FPZ * len(leaders_list) + END_HOLD

    def update(frame):
        zi = frame // FPZ
        if zi >= len(leaders_list):
            # End card
            if frame == FPZ * len(leaders_list):
                zone_im.set_data(zone_imgs[None])
                t_zone.set_text("")
                t_name.set_text("KINGS OF THE COURT")
                t_stats.set_text(
                    f"{season}  ·  12 zones  ·  {len(shots_df):,} shots"
                )
            return

        ldr   = leaders_list[zi]
        zone  = ldr["ZONE"]
        local = frame % FPZ
        arcs  = zone_arcs[zone]
        n     = max(len(arcs), 1)

        # Zone entry: highlight + update text, reset arcs
        if local == 0:
            zone_im.set_data(zone_imgs[zone])
            t_zone.set_text(zone.upper())
            t_name.set_text(ldr["PLAYER_NAME"])
            t_stats.set_text(
                f"{ldr['FGM']} / {ldr['FGA']} FGA   ·   {ldr['FG_PCT']*100:.1f}% FG"
            )
            for p in arcs:
                p.set_alpha(0)

        # Stagger IN: far → near (already sorted by distance descending)
        if _B_IN_S <= local < _B_IN_E:
            t = (local - _B_IN_S) / T_IN
            thresh = int(t * n)
            for i, p in enumerate(arcs):
                p.set_alpha(0.62 if i < thresh else 0.0)

        # Full hold
        elif _B_IN_E <= local < _B_HLD_E:
            for p in arcs:
                p.set_alpha(0.62)

        # Stagger OUT: near → far (reverse order of arcs list)
        elif _B_HLD_E <= local < _B_OUT_E:
            t = (local - _B_HLD_E) / T_OUT
            thresh = int(t * n)
            for i, p in enumerate(reversed(arcs)):
                p.set_alpha(0.0 if i < thresh else 0.62)

        # Pause: all arcs gone, zone dims before next
        elif local == _B_OUT_E:
            for p in arcs:
                p.set_alpha(0.0)
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
