import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="MLB Strikeout Predictor",
    page_icon="⚾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Portfolio-matched CSS ──────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@600;700&display=swap');

#MainMenu, footer, header { visibility: hidden; }

.stApp { background: #ffffff; font-family: 'Inter', sans-serif; color: #1e293b; }

/* ── App header ── */
.app-header {
    background: #1a3a5c; padding: 1.4rem 1.8rem; border-radius: 8px;
    margin-bottom: 1.5rem; border-bottom: 3px solid #2e86ab;
}
.app-header h1 {
    color: #ffffff; font-family: 'Source Serif 4', serif;
    font-size: 1.5rem; margin: 0; font-weight: 700;
}
.app-header p { color: #94b8d0; margin: 0.25rem 0 0; font-size: 0.82rem; }

/* ── Selects ── */
.stSelectbox label { font-weight: 600; color: #1a3a5c; font-size: 0.88rem; }


/* ── Prediction card ── */
.pred-card {
    background: #1a3a5c; border-radius: 10px; padding: 1.4rem 1.8rem;
    text-align: center; margin: 1.4rem 0; border: 1px solid #2e86ab;
}
.pred-eyebrow {
    color: #94b8d0; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.12em; margin-bottom: 0.4rem;
}
.pred-number {
    color: #ffffff; font-family: 'Source Serif 4', serif;
    font-size: 4.5rem; font-weight: 700; line-height: 1;
}
.pred-unit { color: #2e86ab; font-size: 1.1rem; font-weight: 600; }
.pred-range { color: #94b8d0; font-size: 0.82rem; margin-top: 0.5rem; }
.pred-matchup { color: #c8dde9; font-size: 0.8rem; margin-top: 0.3rem; }

/* ── Confidence bar ── */
.conf-wrap { margin: 0.6rem auto 0; max-width: 220px; }
.conf-track {
    height: 6px; background: #0e2540; border-radius: 999px; overflow: hidden;
}
.conf-fill { height: 100%; background: #2e86ab; border-radius: 999px; }
.conf-label { color: #94b8d0; font-size: 0.72rem; margin-top: 0.3rem; }

/* ── Key factors ── */
.factors-header {
    font-family: 'Source Serif 4', serif; color: #1a3a5c;
    font-size: 1.05rem; font-weight: 700;
    margin: 1.4rem 0 0.8rem; padding-bottom: 0.4rem;
    border-bottom: 2px solid #e2e8f0;
}
.factor-row {
    display: flex; align-items: flex-start; padding: 0.65rem 0.9rem;
    margin-bottom: 0.45rem; background: #f8f9fb; border-radius: 6px;
    border-left: 3px solid #2e86ab;
}
.factor-icon { font-size: 1rem; margin-right: 0.75rem; padding-top: 0.1rem; }
.factor-content { flex: 1; }
.factor-label { font-weight: 600; color: #1a3a5c; font-size: 0.83rem; }
.factor-value { color: #2e86ab; font-size: 0.88rem; font-weight: 600; }
.factor-note  { color: #64748b; font-size: 0.76rem; margin-top: 0.1rem; }

.badge {
    display: inline-block; padding: 0.1rem 0.45rem; border-radius: 999px;
    font-size: 0.7rem; font-weight: 600; margin-left: 0.4rem; vertical-align: middle;
}
.badge-elite  { background: #fef3c7; color: #92400e; }
.badge-above  { background: #dbeafe; color: #1e40af; }
.badge-avg    { background: #f1f5f9; color: #475569; }
.badge-below  { background: #fce7f3; color: #9d174d; }

/* ── Footer note ── */
.data-note {
    text-align: center; color: #94a3b8; font-size: 0.72rem;
    margin-top: 1.5rem; padding-top: 0.8rem; border-top: 1px solid #e2e8f0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Constants ──────────────────────────────────────────────────────────────────
LEAGUE_K9   = 8.8    # MLB avg K/9, 2024-25
LEAGUE_KPct = 0.225  # MLB avg batter K%, 2024-25
AVG_IP_START = 5.5   # average innings per starter outing

TEAM_FULL = {
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CWS": "Chicago White Sox",
    "CHW": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KC":  "Kansas City Royals",
    "KCR": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "OAK": "Oakland Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD":  "San Diego Padres",
    "SDP": "San Diego Padres",
    "SF":  "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "SEA": "Seattle Mariners",
    "STL": "St. Louis Cardinals",
    "TB":  "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WSH": "Washington Nationals",
    "WSN": "Washington Nationals",
}

ALL_TEAMS = sorted(set(v for v in TEAM_FULL.values()))


# ── MLB Stats API helpers ──────────────────────────────────────────────────────
MLB_API = "https://statsapi.mlb.com/api/v1"
_HEADERS = {"User-Agent": "mlb-strikeout-predictor/1.0"}


def _parse_ip(ip_str) -> float:
    """'58.2' (58 innings + 2 outs) → decimal innings."""
    try:
        parts = str(ip_str).split(".")
        return int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
    except Exception:
        return 0.0


def _get(path: str, params: dict) -> dict:
    import requests
    r = requests.get(f"{MLB_API}{path}", params=params, headers=_HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=43_200, show_spinner=False)
def load_pitcher_data() -> pd.DataFrame:
    last_err = ""
    for season in (2026, 2025, 2024):
        try:
            data = _get("/stats", {
                "stats": "season",
                "playerPool": "All",
                "position": 1,
                "sportId": 1,
                "season": season,
                "group": "pitching",
                "gameType": "R",
                "limit": 1000,
            })
            splits = data["stats"][0]["splits"]
            if not splits:
                continue

            rows = []
            for s in splits:
                st_obj = s.get("stat", {})
                gs  = int(st_obj.get("gamesStarted", 0))
                if gs < (3 if season == 2026 else 15):
                    continue
                ip  = _parse_ip(st_obj.get("inningsPitched", 0))
                so  = int(st_obj.get("strikeOuts", 0))
                bf  = int(st_obj.get("battersFaced", 0))
                k9  = (so / ip * 9) if ip > 0 else 0.0
                kpct = (so / bf) if bf > 0 else None
                rows.append({
                    "Name":      s.get("player", {}).get("fullName", "Unknown"),
                    "Team":      s.get("team",   {}).get("name", ""),
                    "GS":        gs,
                    "IP":        round(ip, 2),
                    "K/9":       round(k9, 2),
                    "K%":        kpct,
                    "whiff_pct": np.nan,   # not in standard stats API
                    "ip_per_gs": round(ip / gs, 2) if gs > 0 else AVG_IP_START,
                    "season":    season,
                })

            if not rows:
                continue
            df = pd.DataFrame(rows).dropna(subset=["K/9"])
            df = df[df["K/9"] > 0].sort_values("Name").reset_index(drop=True)
            return df

        except Exception as e:
            last_err = str(e)
            continue

    st.error(f"Could not load pitcher data: {last_err}")
    return pd.DataFrame()


@st.cache_data(ttl=43_200, show_spinner=False)
def load_team_batting() -> pd.DataFrame:
    fallback = pd.DataFrame({
        "team_full": ALL_TEAMS,
        "K%": LEAGUE_KPct,
    })

    for season in (2026, 2025, 2024):
        try:
            data = _get("/teams/stats", {
                "season": season,
                "group": "hitting",
                "stats": "season",
                "sportId": 1,
                "gameType": "R",
            })
            splits = data["stats"][0]["splits"]
            if not splits:
                continue

            rows = []
            for s in splits:
                st_obj = s.get("stat", {})
                so = int(st_obj.get("strikeOuts", 0))
                pa = int(st_obj.get("plateAppearances", 0))
                if pa == 0:
                    continue
                rows.append({
                    "team_full": s.get("team", {}).get("name", ""),
                    "K%": so / pa,
                })

            if rows:
                return pd.DataFrame(rows)

        except Exception:
            continue

    return fallback


# ── Prediction helpers ─────────────────────────────────────────────────────────
def percentile_badge(value: float, series: pd.Series) -> str:
    pct = (value > series.dropna()).mean() * 100
    if pct >= 80:
        return '<span class="badge badge-elite">Elite</span>'
    if pct >= 60:
        return '<span class="badge badge-above">Above Avg</span>'
    if pct >= 40:
        return '<span class="badge badge-avg">Average</span>'
    return '<span class="badge badge-below">Below Avg</span>'


def predict(pitcher_row: pd.Series, team_k_pct: float) -> dict:
    k9         = pitcher_row["K/9"]
    ip_per_gs  = pitcher_row.get("ip_per_gs", AVG_IP_START)
    whiff_pct  = pitcher_row.get("whiff_pct", np.nan)
    pitcher_k_pct = pitcher_row.get("K%", np.nan)

    # Base: convert K/9 → expected Ks given typical innings
    base_k = (k9 / 9.0) * ip_per_gs

    # Opponent adjustment: how much does this team K relative to league avg?
    opp_factor = team_k_pct / LEAGUE_KPct
    adjusted_k = base_k * opp_factor

    # Whiff% secondary adjustment (small weight so it doesn't dominate)
    if not np.isnan(whiff_pct):
        league_whiff = 0.11   # ~11% SwStr% league avg
        whiff_factor = 1.0 + 0.15 * (whiff_pct - league_whiff) / league_whiff
        whiff_factor = np.clip(whiff_factor, 0.85, 1.15)
        adjusted_k *= whiff_factor
    else:
        whiff_factor = 1.0

    predicted    = round(adjusted_k, 1)
    poisson_std  = np.sqrt(predicted) * 1.1
    low          = max(0, round(predicted - poisson_std))
    high         = round(predicted + poisson_std)
    opp_delta    = round((opp_factor - 1.0) * base_k, 1)

    return dict(
        predicted=predicted,
        low=low,
        high=high,
        k9=k9,
        ip_per_gs=round(ip_per_gs, 1),
        whiff_pct=whiff_pct,
        pitcher_k_pct=pitcher_k_pct if not np.isnan(pitcher_k_pct) else None,
        team_k_pct=team_k_pct,
        opp_delta=opp_delta,
        opp_factor=opp_factor,
        whiff_factor=round(whiff_factor, 3),
    )


# ── Render helpers ─────────────────────────────────────────────────────────────
def render_prediction(res: dict, pitcher_name: str, team_name: str) -> None:
    predicted   = res["predicted"]
    low, high   = res["low"], res["high"]
    conf_width  = min(100, int(60 + (predicted / 15) * 40))  # rough confidence bar

    st.markdown(
        f"""
<div class="pred-card">
  <div class="pred-eyebrow">Predicted Strikeouts</div>
  <div class="pred-number">{predicted:.0f}</div>
  <div class="pred-unit">K</div>
  <div class="pred-range">Likely range: {low}–{high} K</div>
  <div class="pred-matchup">{pitcher_name} vs {team_name}</div>
  <div class="conf-wrap">
    <div class="conf-track"><div class="conf-fill" style="width:{conf_width}%"></div></div>
    <div class="conf-label">Model confidence</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_factors(res: dict, pitcher_row: pd.Series, pitchers_df: pd.DataFrame, team_name: str) -> None:
    k9        = res["k9"]
    team_kpct = res["team_k_pct"]
    whiff_pct = res["whiff_pct"]
    ip_gs     = res["ip_per_gs"]
    opp_delta = res["opp_delta"]

    k9_badge  = percentile_badge(k9, pitchers_df["K/9"])
    opp_dir   = "+" if opp_delta >= 0 else ""
    opp_note  = f"{opp_dir}{opp_delta} K adjustment vs league-average lineup"

    if team_kpct > LEAGUE_KPct * 1.08:
        opp_badge = '<span class="badge badge-elite">High K%</span>'
        opp_desc  = f"{team_name} strikes out at a high rate ({team_kpct:.1%}) — boosts prediction"
    elif team_kpct < LEAGUE_KPct * 0.92:
        opp_badge = '<span class="badge badge-below">Low K%</span>'
        opp_desc  = f"{team_name} makes contact well ({team_kpct:.1%}) — suppresses prediction"
    else:
        opp_badge = '<span class="badge badge-avg">Near Avg</span>'
        opp_desc  = f"{team_name} K% ({team_kpct:.1%}) is close to MLB average — neutral"

    factors_html = f"""
<div class="factors-header">Key Factors</div>

<div class="factor-row">
  <div class="factor-icon">📈</div>
  <div class="factor-content">
    <div class="factor-label">Pitcher K/9 {k9_badge}</div>
    <div class="factor-value">{k9:.1f} strikeouts per 9 innings</div>
    <div class="factor-note">League average is {LEAGUE_K9:.1f} K/9</div>
  </div>
</div>
"""

    if not np.isnan(whiff_pct):
        league_whiff = 0.11
        whiff_badge  = percentile_badge(whiff_pct, pitchers_df["whiff_pct"].dropna())
        factors_html += f"""
<div class="factor-row">
  <div class="factor-icon">💨</div>
  <div class="factor-content">
    <div class="factor-label">Whiff / Swinging-Strike Rate {whiff_badge}</div>
    <div class="factor-value">{whiff_pct:.1%} SwStr%</div>
    <div class="factor-note">League average is {league_whiff:.0%} — higher = more chases</div>
  </div>
</div>
"""

    factors_html += f"""
<div class="factor-row">
  <div class="factor-icon">🏏</div>
  <div class="factor-content">
    <div class="factor-label">Opponent Team K% {opp_badge}</div>
    <div class="factor-value">{team_kpct:.1%} strikeout rate as batters</div>
    <div class="factor-note">{opp_desc}</div>
  </div>
</div>

<div class="factor-row">
  <div class="factor-icon">⏱️</div>
  <div class="factor-content">
    <div class="factor-label">Projected Innings</div>
    <div class="factor-value">{ip_gs} IP per start (season avg)</div>
    <div class="factor-note">More innings = more opportunities to accumulate Ks</div>
  </div>
</div>

<div class="factor-row">
  <div class="factor-icon">⚖️</div>
  <div class="factor-content">
    <div class="factor-label">Opponent Adjustment</div>
    <div class="factor-value">{opp_dir}{opp_delta} K</div>
    <div class="factor-note">{opp_note}</div>
  </div>
</div>
"""

    st.markdown(factors_html, unsafe_allow_html=True)


# ── Main app ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
  <h1>⚾ MLB Strikeout Predictor</h1>
  <p>Powered by the MLB Stats API &nbsp;·&nbsp; 2026 season data</p>
</div>
""",
    unsafe_allow_html=True,
)

# Load data
with st.spinner("Loading 2026 pitcher and team stats…"):
    pitchers_df = load_pitcher_data()
    team_batting = load_team_batting()

if pitchers_df.empty:
    st.error("Could not load pitcher data. Please try again in a moment.")
    st.stop()

# Build team K% lookup (full name → K%)
team_kpct_map: dict[str, float] = dict(zip(team_batting["team_full"], team_batting["K%"]))

# Fallback: any teams missing get league average
for t in ALL_TEAMS:
    if t not in team_kpct_map:
        team_kpct_map[t] = LEAGUE_KPct

pitcher_names = pitchers_df["Name"].tolist()

# ── Dropdowns ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    selected_pitcher = st.selectbox("Pitcher", pitcher_names, index=0)
with col2:
    selected_team = st.selectbox("Opposing Team", ALL_TEAMS, index=0)

# ── Prediction output ──────────────────────────────────────────────────────────
pitcher_row = pitchers_df[pitchers_df["Name"] == selected_pitcher].iloc[0]
team_k_pct  = team_kpct_map.get(selected_team, LEAGUE_KPct)

result = predict(pitcher_row, team_k_pct)
render_prediction(result, selected_pitcher, selected_team)
render_factors(result, pitcher_row, pitchers_df, selected_team)

st.markdown(
    """
<div class="data-note">
  Data sourced from the official MLB Stats API (statsapi.mlb.com).
  Predictions are statistical estimates, not guarantees.
  Model: K/9 × projected IP × opponent K% adjustment.
</div>
""",
    unsafe_allow_html=True,
)
