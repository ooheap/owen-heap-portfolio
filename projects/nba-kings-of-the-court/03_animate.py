"""
Stage 4 + 5: Draw the court, then animate zone-by-zone leader reveals
with green arc lines showing made shots.

Court orientation: basket at (0, 0) at the bottom, baseline along y=0,
positive y going up toward half court. This is the standard NBA half-court
matplotlib convention (Savvas Tjortjoglou's code is the well-known reference).
"""

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle, Arc, FancyArrowPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from importlib import import_module
zones = import_module("02_zones_and_leaders")
assign_zone = zones.assign_zone
ZONE_ORDER = zones.ZONE_ORDER


# ---------- Court drawing ----------
def draw_court(ax, line_color="black", lw=2):
    """Draw an NBA half-court in matplotlib. Units = tenths of feet."""
    # Hoop
    ax.add_patch(Circle((0, 0), radius=7.5, lw=lw, color=line_color, fill=False))
    # Backboard
    ax.add_patch(Rectangle((-30, -7.5), 60, -1, lw=lw, color=line_color))
    # Outer paint box (the key)
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, lw=lw, color=line_color, fill=False))
    # Free-throw circles
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0, theta2=180, lw=lw, color=line_color))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=0, lw=lw,
                     color=line_color, linestyle="dashed"))
    # Restricted area
    ax.add_patch(Arc((0, 0), 80, 80, theta1=0, theta2=180, lw=lw, color=line_color))
    # 3-point line: two straight segments + arc
    ax.plot([-220, -220], [-47.5, 92.5], color=line_color, lw=lw)
    ax.plot([220, 220], [-47.5, 92.5], color=line_color, lw=lw)
    ax.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, lw=lw, color=line_color))
    # Half-court line + center circle
    ax.plot([-250, 250], [422.5, 422.5], color=line_color, lw=lw)
    ax.add_patch(Arc((0, 422.5), 120, 120, theta1=180, theta2=0, lw=lw, color=line_color))
    # Outer court boundary
    ax.add_patch(Rectangle((-250, -47.5), 500, 470, lw=lw, color=line_color, fill=False))

    ax.set_xlim(-260, 260)
    ax.set_ylim(-60, 430)
    ax.set_aspect("equal")
    ax.axis("off")


# ---------- Arc paths (the green "swish" lines) ----------
def make_arc_path(x0, y0, x1=0, y1=0, height_factor=0.7):
    """
    Quadratic Bezier from (x0,y0) to (x1,y1) bulging upward.
    height_factor controls how high the arc peaks.
    """
    dist = math.hypot(x1 - x0, y1 - y0)
    cx = (x0 + x1) / 2
    cy = max(y0, y1) + dist * height_factor
    return Path([(x0, y0), (cx, cy), (x1, y1)],
                [Path.MOVETO, Path.CURVE3, Path.CURVE3])


def draw_shot_arcs(ax, shots_df, color="#7CFC00", alpha=0.55, lw=1.6):
    """Draw arcs from each made shot to the rim."""
    patches = []
    for _, row in shots_df.iterrows():
        path = make_arc_path(row["LOC_X"], row["LOC_Y"])
        p = PathPatch(path, facecolor="none", edgecolor=color,
                      lw=lw, alpha=alpha, capstyle="round")
        ax.add_patch(p)
        patches.append(p)
    return patches


# ---------- Animation ----------
def animate_zone_leaders(shots_df, leaders_df, out_path="kings_of_the_court.mp4",
                         title="Kings of the Court — 2025-26"):
    """
    Frame plan:
      - For each zone in order:
          frame A: fade in the zone highlight + player name + FG%
          frame B: draw the made-shot arcs (revealed one by one or all at once)
          frame C: hold for a beat
      - At the end: show the full court with every zone's leader visible.
    """
    fig, ax = plt.subplots(figsize=(8, 10), dpi=120)
    fig.patch.set_facecolor("#f4f1ea")
    ax.set_facecolor("#f4f1ea")

    draw_court(ax)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=10)

    # Pre-assign zones to all shots
    shots = shots_df.copy()
    shots["ZONE"] = shots.apply(lambda r: assign_zone(r["LOC_X"], r["LOC_Y"]), axis=1)

    # Text overlays we'll update each "scene"
    label = ax.text(0, 460, "", ha="center", va="bottom",
                    fontsize=14, fontweight="bold")
    stat = ax.text(0, 440, "", ha="center", va="bottom", fontsize=11)

    # Persistent patches across frames (so prior zones stay drawn)
    drawn_patches = []

    # Frames: 8 for label fade-in, then arcs stagger in over remaining 22 frames,
    # then 15 frames hold. Total = 45 frames (~1.5 s) per zone.
    LABEL_FRAMES = 8
    ARC_FRAMES = 22
    HOLD_FRAMES = 15
    FRAMES_PER_ZONE = LABEL_FRAMES + ARC_FRAMES + HOLD_FRAMES  # 45

    END_HOLD = 45
    total_frames = FRAMES_PER_ZONE * len(leaders_df) + END_HOLD

    # Precompute, for each zone, the made shots by that leader in that zone
    zone_shots = {}
    for _, ldr in leaders_df.iterrows():
        z = ldr["ZONE"]
        s = shots[
            (shots["ZONE"] == z)
            & (shots["PLAYER_ID"] == ldr["PLAYER_ID"])
            & (shots["SHOT_MADE_FLAG"] == 1)
        ].reset_index(drop=True)
        zone_shots[z] = s

    # Pre-build all arc patches per zone (hidden initially via alpha=0)
    zone_arc_patches = {}
    for zone, zdf in zone_shots.items():
        patches = []
        for _, row in zdf.iterrows():
            path = make_arc_path(row["LOC_X"], row["LOC_Y"])
            p = PathPatch(path, facecolor="none", edgecolor="#7CFC00",
                          lw=1.6, alpha=0, capstyle="round")
            ax.add_patch(p)
            patches.append(p)
        zone_arc_patches[zone] = patches

    leaders_list = leaders_df.to_dict("records")

    def update(frame):
        zone_idx = frame // FRAMES_PER_ZONE
        if zone_idx >= len(leaders_list):
            label.set_text("Kings of the Court")
            stat.set_text("2025-26 Regular Season")
            return [label, stat]

        ldr = leaders_list[zone_idx]
        local_frame = frame % FRAMES_PER_ZONE
        zone = ldr["ZONE"]
        patches = zone_arc_patches[zone]
        n = len(patches)

        if local_frame == 0:
            label.set_text(f"{ldr['PLAYER_NAME']} — {ldr['ZONE']}")
            stat.set_text(
                f"{ldr['FGM']}/{ldr['FGA']}  |  {ldr['FG_PCT']*100:.1f}%"
            )

        if local_frame >= LABEL_FRAMES and n > 0:
            # Reveal arcs one by one, evenly spaced over ARC_FRAMES
            arc_local = local_frame - LABEL_FRAMES  # 0..ARC_FRAMES+HOLD-1
            reveal_count = min(n, int(n * arc_local / ARC_FRAMES) + 1)
            for i, p in enumerate(patches):
                p.set_alpha(0.55 if i < reveal_count else 0)

        return [label, stat] + patches

    anim = animation.FuncAnimation(
        fig, update, frames=total_frames, interval=1000 / 30, blit=False
    )

    # Save as mp4 (requires ffmpeg) or gif
    if out_path.endswith(".gif"):
        anim.save(out_path, writer="pillow", fps=30)
    else:
        FFMPEG_PATH = (
            r"C:\Users\oohea\AppData\Local\Microsoft\WinGet\Packages"
            r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
            r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
        )
        writer = animation.FFMpegWriter(fps=30)
        writer._exec_key = "animation.ffmpeg_path"
        import matplotlib as mpl
        mpl.rcParams["animation.ffmpeg_path"] = FFMPEG_PATH
        anim.save(out_path, writer=writer, dpi=120)
    plt.close(fig)
    print(f"Saved animation to {out_path}")


if __name__ == "__main__":
    shots = pd.read_parquet("shots_2025-26.parquet")
    leaders = pd.read_parquet("leaders_2025-26.parquet")
    animate_zone_leaders(shots, leaders, out_path="kings_of_the_court.mp4")
