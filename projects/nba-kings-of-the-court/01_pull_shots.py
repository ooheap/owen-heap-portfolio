"""
Stage 1: Pull all shot data for the 2025-26 NBA regular season.

The NBA's ShotChartDetail endpoint requires a team_id and player_id. To get
league-wide data, we loop through all 30 teams. Using player_id=0 gives all
players on that team. We add sleeps to avoid being rate-limited.

This script caches the result as a parquet file so you only pay the cost once.
"""

import time
import os
import pandas as pd
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import teams

SEASON = "2025-26"
SEASON_TYPE = "Regular Season"
CACHE_PATH = f"shots_{SEASON}.parquet"


def pull_team_shots(team_id: int, season: str, season_type: str) -> pd.DataFrame:
    """Pull all shots for one team in one season."""
    resp = shotchartdetail.ShotChartDetail(
        team_id=team_id,
        player_id=0,                # 0 = all players
        season_nullable=season,
        season_type_all_star=season_type,
        context_measure_simple="FGA",  # all field-goal attempts
    )
    df = resp.get_data_frames()[0]
    return df


def main():
    if os.path.exists(CACHE_PATH):
        print(f"Cache exists at {CACHE_PATH}. Delete it to re-pull.")
        df = pd.read_parquet(CACHE_PATH)
        print(f"Loaded {len(df):,} shots from cache.")
        return df

    all_teams = teams.get_teams()
    print(f"Pulling shots for {len(all_teams)} teams...")

    frames = []
    for i, team in enumerate(all_teams, 1):
        print(f"  [{i:2d}/30] {team['full_name']}...", end=" ", flush=True)
        try:
            df = pull_team_shots(team["id"], SEASON, SEASON_TYPE)
            print(f"{len(df):,} shots")
            frames.append(df)
        except Exception as e:
            print(f"FAILED: {e}")
        time.sleep(0.6)  # be polite to stats.nba.com

    full = pd.concat(frames, ignore_index=True)
    full.to_parquet(CACHE_PATH)
    print(f"\nSaved {len(full):,} total shots to {CACHE_PATH}")
    return full


if __name__ == "__main__":
    main()
