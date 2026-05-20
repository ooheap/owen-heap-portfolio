"""
Stage 2 + 3: Define your 12 zones, assign each shot to a zone, find leaders.

NBA shot coordinates (from ShotChartDetail):
  - LOC_X: horizontal, -250 to 250 (in tenths of feet from the basket)
  - LOC_Y: vertical, basket at y=0, half court at ~470
  - So (0, 0) = basket. Positive X = right side from shooter's perspective.
  - Court is 50 ft wide. 3pt line: 23.75 ft (237.5 units) above the break,
    22 ft (220 units) in the corners. Corners end at LOC_Y = 140 (14 ft).

Your 12 zones:
  THREE-POINT (5):
    1. Left corner 3       (x <= -220, y <= 140, beyond 3pt line)
    2. Left wing 3         (left side, above break, between corner and TOK)
    3. Top of key 3        (center, above the break)
    4. Right wing 3        (right side, above break)
    5. Right corner 3      (x >= 220, y <= 140)
  MID-RANGE (5):
    6. Left baseline mid   (left side, low y, inside 3pt line, outside paint)
    7. Left elbow          (left side, mid y, outside paint, inside 3pt)
    8. Free throw / center mid (center, above the paint, inside 3pt)
    9. Right elbow
    10. Right baseline mid
  PAINT (2):
    11. High post / far paint  (in the paint but away from rim)
    12. Restricted area / at the rim
"""

import math
import numpy as np
import pandas as pd

# Court constants (units = tenths of feet)
PAINT_LEFT_X = -80      # paint is 16 ft wide -> -80 to 80
PAINT_RIGHT_X = 80
PAINT_TOP_Y = 190       # paint extends from baseline to free throw line (19 ft)
CORNER_3_X = 220        # corner 3pt line is 22 ft from center
CORNER_Y_LIMIT = 140    # corner 3 region ends at 14 ft from baseline
ARC_3_RADIUS = 237.5    # above-the-break 3pt line is 23.75 ft
RIM_Y = 0
RESTRICTED_RADIUS = 40  # ~4 ft restricted area arc


def assign_zone(x: float, y: float) -> str:
    """Assign a shot at (x, y) to one of 12 zones."""
    # Distance from basket
    dist = math.hypot(x, y)
    # Angle from basket (0 = straight ahead, positive = right, in degrees)
    # We compute angle from the positive y-axis.
    angle = math.degrees(math.atan2(x, max(y, 0.01)))

    # --- Is it a 3-point shot? ---
    # Corner 3: y <= CORNER_Y_LIMIT and |x| >= CORNER_3_X
    if y <= CORNER_Y_LIMIT and abs(x) >= CORNER_3_X:
        return "Left Corner 3" if x < 0 else "Right Corner 3"
    # Above-the-break 3: distance from rim >= ARC_3_RADIUS (and not a corner)
    if dist >= ARC_3_RADIUS and y > CORNER_Y_LIMIT:
        # Split into 3 wedges by angle: left wing, top of key, right wing
        if angle < -20:
            return "Left Wing 3"
        elif angle > 20:
            return "Right Wing 3"
        else:
            return "Top of Key 3"

    # --- It's a 2-point shot. ---
    in_paint = (PAINT_LEFT_X <= x <= PAINT_RIGHT_X) and (0 <= y <= PAINT_TOP_Y)

    if in_paint:
        # Restricted area: very close to the rim
        if dist <= RESTRICTED_RADIUS + 10:
            return "Restricted Area"
        else:
            return "High Post / Far Paint"

    # Mid-range: not paint, inside the arc
    # Split by side (left/right) and height (baseline / elbow / center)
    # Threshold between "baseline" and "elbow" mid-range. ~14 ft up from the
    # baseline matches the corner-3 cutoff, which is a natural break.
    BASELINE_ELBOW_Y = 140

    # Center mid-range (free throw / above paint) — narrow center column
    if abs(x) < 60 and y > PAINT_TOP_Y:
        return "Center Mid (FT)"
    # Baseline mid-range: low y
    if y <= BASELINE_ELBOW_Y:
        return "Left Baseline Mid" if x < 0 else "Right Baseline Mid"
    # Elbow mid-range: higher y
    return "Left Elbow Mid" if x < 0 else "Right Elbow Mid"


# Canonical order for animation (clockwise-ish, perimeter to rim)
ZONE_ORDER = [
    "Left Corner 3",
    "Left Wing 3",
    "Top of Key 3",
    "Right Wing 3",
    "Right Corner 3",
    "Left Baseline Mid",
    "Left Elbow Mid",
    "Center Mid (FT)",
    "Right Elbow Mid",
    "Right Baseline Mid",
    "High Post / Far Paint",
    "Restricted Area",
]


def find_zone_leaders(
    df: pd.DataFrame,
    min_attempts: dict[str, int] | None = None,
    default_min: int = 50,
) -> pd.DataFrame:
    """
    For each zone, return the player with the highest FG% among players
    with at least `min_attempts[zone]` attempts.
    """
    if min_attempts is None:
        min_attempts = {}

    # Assign zones
    df = df.copy()
    df["ZONE"] = df.apply(lambda r: assign_zone(r["LOC_X"], r["LOC_Y"]), axis=1)
    df["MADE"] = (df["SHOT_MADE_FLAG"] == 1).astype(int)

    # Group by zone + player
    grouped = (
        df.groupby(["ZONE", "PLAYER_ID", "PLAYER_NAME"])
        .agg(FGA=("MADE", "size"), FGM=("MADE", "sum"))
        .reset_index()
    )
    grouped["FG_PCT"] = grouped["FGM"] / grouped["FGA"]

    leaders = []
    for zone in ZONE_ORDER:
        threshold = min_attempts.get(zone, default_min)
        candidates = grouped[
            (grouped["ZONE"] == zone) & (grouped["FGA"] >= threshold)
        ]
        if candidates.empty:
            print(f"  WARN: no qualifying players in {zone} (min {threshold} FGA)")
            continue
        top = candidates.sort_values("FG_PCT", ascending=False).iloc[0]
        leaders.append(
            {
                "ZONE": zone,
                "PLAYER_ID": int(top["PLAYER_ID"]),
                "PLAYER_NAME": top["PLAYER_NAME"],
                "FGM": int(top["FGM"]),
                "FGA": int(top["FGA"]),
                "FG_PCT": float(top["FG_PCT"]),
            }
        )
    return pd.DataFrame(leaders)


if __name__ == "__main__":
    df = pd.read_parquet("shots_2025-26.parquet")
    # You'll want different thresholds for different zones.
    # Rim shots are common, corner 3s are rarer.
    min_att = {
        "Left Corner 3": 40,
        "Right Corner 3": 40,
        "Left Wing 3": 75,
        "Right Wing 3": 75,
        "Top of Key 3": 100,
        "Left Baseline Mid": 40,
        "Right Baseline Mid": 40,
        "Left Elbow Mid": 25,
        "Right Elbow Mid": 20,
        "Center Mid (FT)": 20,
        "High Post / Far Paint": 50,
        "Restricted Area": 200,
    }
    leaders = find_zone_leaders(df, min_attempts=min_att)
    print(leaders.to_string(index=False))
    leaders.to_parquet("leaders_2025-26.parquet")
