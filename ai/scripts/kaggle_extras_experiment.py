"""Experiment: do the Kaggle extras improve the match model? (plan phase 7)

Three candidate feature groups, each tested on the seasons its source covers:

1. **Champions League rest days** — days since each team's last match in the
   league *or* the Champions League, and whether it played in Europe in the
   previous 7 days. Sources: Sportmonks cups (2011/12–2021/22) and
   football-data.org (2023/24 onwards); other seasons are left missing.
2. **Rolling xG** — each team's mean xG for and against over its previous five
   league matches. Source: FBref (Premier League 2020/21–2024/25 only).
3. **FIFA team ratings** — attack, midfield and defence as of the match date.
   Source: FIFA ratings scraped weekly, July 2015 to May 2022.

Each group is added to the served model's feature matrix, the model is
retrained with the served configuration, and log loss is compared with a
paired bootstrap on rows where the source has data. Results are written up in
``docs/reports/kaggle-extras.md``.

Usage:
    uv run python -m scripts.kaggle_extras_experiment
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from evaluation.comparison import paired_bootstrap_delta
from training.configuration import TrainingConfig
from training.persistence import load_json
from training.splitter import SeasonSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel

RAW = Path("../datasets/raw/kaggle")
MATRIX = Path("../datasets/features/top5/feature_matrix.parquet")
CONFIG = Path("models/latest/config.json")
ALIASES = Path("../datasets/schemas/team_aliases.csv")
CL_WINDOW_DAYS = 7
XG_WINDOW = 5
FIFA_MATCH_CUTOFF = 0.85


# --------------------------------------------------------------------- sources


def aliases(source: str) -> dict[str, str]:
    """Source spelling → canonical team name, for one source."""
    table = pd.read_csv(ALIASES)
    rows = table[table["source"] == source]
    return dict(zip(rows["source_name"], rows["canonical_name"], strict=True))


def champions_league_appearances() -> pd.DataFrame:
    """One row per (date, canonical team) for Champions League matches."""
    cups = pd.read_csv(
        RAW / "enricocattaneo_match_prediction/cups_static.csv",
        usecols=[
            "league_id",
            "time_starting_at_date",
            "localTeam_name",
            "visitorTeam_name",
        ],
    )
    cups = cups[cups["league_id"] == 2]
    old = _appearances(
        cups["time_starting_at_date"],
        [cups["localTeam_name"], cups["visitorTeam_name"]],
        aliases("sportmonks"),
    )
    live = pd.read_parquet(
        RAW / "adrianjuliusaluoch_live_results/football_matches.parquet"
    )
    live = live[live["competition.code"] == "CL"]
    live = live.sort_values("lastUpdated").drop_duplicates("id", keep="last")
    new = _appearances(
        pd.to_datetime(live["utcDate"], errors="coerce", utc=True).dt.tz_localize(None),
        [live["homeTeam.name"], live["awayTeam.name"]],
        aliases("football_data_org"),
    )
    return pd.concat([old, new]).drop_duplicates().reset_index(drop=True)


def _appearances(
    dates: pd.Series, sides: list[pd.Series], names: dict[str, str]
) -> pd.DataFrame:
    frames = [
        pd.DataFrame(
            {"date": pd.to_datetime(dates).dt.normalize(), "team": side.map(names)}
        )
        for side in sides
    ]
    out = pd.concat(frames).dropna()
    return out[["date", "team"]]


# ------------------------------------------------------------ feature builders


def champions_league_features(df: pd.DataFrame, cl: pd.DataFrame) -> pd.DataFrame:
    """Days since the last league or CL match, and a CL-in-last-7-days flag."""
    dates = pd.to_datetime(df["match_date"])
    covered = _cl_covered_seasons(df, cl)
    league = pd.concat(
        [
            pd.DataFrame(
                {"date": dates, "team": df["home_team"], "season": df["season"]}
            ),
            pd.DataFrame(
                {"date": dates, "team": df["away_team"], "season": df["season"]}
            ),
        ]
    )
    out = pd.DataFrame(index=df.index)
    for side in ("home", "away"):
        team = df[f"{side}_team"]
        last_cl = _last_before(cl, team, dates)
        last_league = _last_before(league[["date", "team"]], team, dates)
        last_any = pd.concat([last_cl, last_league], axis=1).max(axis=1)
        days = (dates - last_any).dt.days
        in_season = covered.reindex(df["season"]).to_numpy()
        out[f"{side}_days_since_any_match"] = np.where(in_season, days, np.nan)
        recent = ((dates - last_cl).dt.days <= CL_WINDOW_DAYS).astype(float)
        out[f"{side}_cl_last_7d"] = np.where(in_season, recent, np.nan)
    return out


def _cl_covered_seasons(df: pd.DataFrame, cl: pd.DataFrame) -> pd.Series:
    seasons = df.groupby("season")["match_date"].agg(["min", "max"])
    start, end = pd.to_datetime(seasons["min"]), pd.to_datetime(seasons["max"])
    covered = [
        bool(((cl["date"] >= s) & (cl["date"] <= e)).any())
        for s, e in zip(start, end, strict=True)
    ]
    return pd.Series(covered, index=seasons.index)


def _last_before(events: pd.DataFrame, team: pd.Series, dates: pd.Series) -> pd.Series:
    """Most recent event date strictly before each (team, date)."""
    query = pd.DataFrame(
        {"team": team.to_numpy(), "date": dates.to_numpy(), "row": team.index}
    )
    query = query.sort_values("date")
    ev = events.rename(columns={"date": "event"}).sort_values("event")
    ev = ev.assign(date=ev["event"] + pd.Timedelta(seconds=1))
    merged = pd.merge_asof(
        query,
        ev[["date", "team", "event"]],
        on="date",
        by="team",
        allow_exact_matches=False,
    )
    return merged.set_index("row")["event"].reindex(team.index)


FBREF_NAMES = {
    "Brighton And Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Leicester City": "Leicester",
    "Luton Town": "Luton",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Norwich City": "Norwich",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "West Bromwich Albion": "West Brom",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
}


def xg_features(df: pd.DataFrame) -> pd.DataFrame:
    """Mean xG for and against over each team's previous five league matches."""
    fb = pd.read_csv(RAW / "armin2080_epl_xg/final_matches.csv")
    fb = fb[fb["comp"] == "Premier League"]
    fb = fb.assign(
        date=pd.to_datetime(fb["date"]), team=fb["team"].replace(FBREF_NAMES)
    ).sort_values(["team", "date"])
    by_team = fb.groupby("team")
    for col in ("xg", "xga"):
        fb[f"{col}_prev{XG_WINDOW}"] = by_team[col].transform(
            lambda s: s.shift(1).rolling(XG_WINDOW, min_periods=3).mean()
        )
    keyed = fb.set_index(["date", "team"])[
        [f"xg_prev{XG_WINDOW}", f"xga_prev{XG_WINDOW}"]
    ]
    keyed = keyed[~keyed.index.duplicated()]
    dates = pd.to_datetime(df["match_date"])
    out = pd.DataFrame(index=df.index)
    for side in ("home", "away"):
        idx = pd.MultiIndex.from_arrays([dates, df[f"{side}_team"]])
        values = keyed.reindex(idx).to_numpy()
        out[f"{side}_xg_prev{XG_WINDOW}"] = values[:, 0]
        out[f"{side}_xga_prev{XG_WINDOW}"] = values[:, 1]
    return out


def _normalise(name: str) -> str:
    text = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    )
    text = re.sub(
        r"\b(fc|cf|ac|as|ss|sc|sv|vfl|vfb|tsg|rc|ogc|afc|club|calcio|sco|sd|ud|cd)\b",
        " ",
        text,
    )
    return re.sub(r"[^a-z]+", " ", text).strip()


def _fifa_dates(raw: pd.Series) -> pd.Series:
    """Parse ISO dates and scraped ones such as 'Sept. 23, 2021' or 'March 6, 2017'."""
    text = raw.astype(str).str.replace(".", "", regex=False).str.replace("Sept", "Sep")
    return pd.to_datetime(text, format="mixed", errors="coerce")


def fifa_features(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Attack, midfield and defence ratings as of each match date.

    FIFA spellings are matched to ours automatically with a strict cutoff;
    unmatched clubs are left missing. Returns the features and match count.
    """
    fifa = pd.read_csv(
        RAW / "enricocattaneo_match_prediction/team_weekly_complete.csv",
        usecols=["TeamName", "ObservationDate", "Attack", "Midfield", "Defence"],
    )
    fifa["date"] = _fifa_dates(fifa["ObservationDate"])
    fifa = fifa.dropna(subset=["date"])
    ours = sorted(set(df["home_team"]) | set(df["away_team"]))
    lookup = {_normalise(n): n for n in ours}
    mapping = {}
    for name in fifa["TeamName"].unique():
        hit = difflib.get_close_matches(
            _normalise(name), list(lookup), n=1, cutoff=FIFA_MATCH_CUTOFF
        )
        if hit:
            mapping[name] = lookup[hit[0]]
    fifa["team"] = fifa["TeamName"].map(mapping)
    fifa = fifa.dropna(subset=["team"]).sort_values("date")
    dates = pd.to_datetime(df["match_date"])
    out = pd.DataFrame(index=df.index)
    for side in ("home", "away"):
        query = pd.DataFrame(
            {"date": dates, "team": df[f"{side}_team"], "row": df.index}
        )
        joined = (
            pd.merge_asof(
                query.sort_values("date"),
                fifa[["date", "team", "Attack", "Midfield", "Defence"]],
                on="date",
                by="team",
                tolerance=pd.Timedelta(days=60),
            )
            .set_index("row")
            .reindex(df.index)
        )
        for col in ("Attack", "Midfield", "Defence"):
            out[f"{side}_fifa_{col.lower()}"] = joined[col]
    return out, len(set(mapping.values()))


# ------------------------------------------------------------------ ablations


def fit(frame: pd.DataFrame, config: TrainingConfig) -> tuple[TrainedModel, list[str]]:
    """Train on the configured season split."""
    columns = get_feature_columns(frame, config)
    return (
        ModelTrainer().train(SeasonSplitter().split(frame, columns, config), config),
        columns,
    )


def compare(
    base: pd.DataFrame,
    extended: pd.DataFrame,
    config: TrainingConfig,
    blocks: dict[str, pd.Series],
) -> None:
    """Print the log-loss change (new − current) on each block of rows."""
    current, cur_cols = fit(base, config)
    candidate, cand_cols = fit(extended, config)
    for name, mask in blocks.items():
        rows = extended[mask]
        if rows.empty:
            print(f"  {name}: no rows")
            continue
        _, p_cur = ModelTrainer().predict(current, rows[cur_cols])
        _, p_new = ModelTrainer().predict(candidate, rows[cand_cols])
        delta = paired_bootstrap_delta(
            rows["result"].to_numpy(), p_new, p_cur, current.classes
        )
        print(
            f"  {name} ({len(rows)} matches): log loss change {delta.mean:+.4f} "
            f"(95% interval {delta.lower:+.4f} to {delta.upper:+.4f})",
            flush=True,
        )


def main(argv: list[str] | None = None) -> int:
    """Run the three ablations and print the results."""
    argparse.ArgumentParser(
        prog="scripts.kaggle_extras_experiment",
        description="Test Champions League rest days, rolling xG and FIFA ratings.",
    ).parse_args(argv)
    config = TrainingConfig(**load_json(CONFIG))
    df = pd.read_parquet(MATRIX)
    df = df.sort_values(["match_date", "competition", "home_team"], kind="stable")
    df = df.reset_index(drop=True)
    season = df["season"]
    test = season.isin(config.test_seasons)
    holdout = season.isin(config.holdout_seasons)

    print("1. Champions League rest days", flush=True)
    cl = champions_league_features(df, champions_league_appearances())
    played = (cl["home_cl_last_7d"] == 1) | (cl["away_cl_last_7d"] == 1)
    print(f"  matches after a CL game within 7 days: {int(played.sum())}")
    compare(
        df,
        pd.concat([df, cl], axis=1),
        config,
        {
            "test": test,
            "holdout": holdout,
            "test+holdout, after a CL game": (test | holdout) & played,
        },
    )

    print("2. Rolling xG (Premier League)", flush=True)
    xg = xg_features(df)
    has_xg = xg["home_xg_prev5"].notna() & xg["away_xg_prev5"].notna()
    compare(
        df,
        pd.concat([df, xg], axis=1),
        config,
        {"test, with xG": test & has_xg, "holdout, with xG": holdout & has_xg},
    )

    print("3. FIFA team ratings", flush=True)
    fifa, matched = fifa_features(df)
    print(f"  clubs matched to FIFA names: {matched}")
    has_fifa = fifa["home_fifa_attack"].notna() & fifa["away_fifa_attack"].notna()
    # Ratings stop in May 2022, so test on the last two covered seasons instead.
    fifa_config = config.model_copy(
        update={
            "val_seasons": ["2019/20"],
            "test_seasons": ["2020/21", "2021/22"],
            "holdout_seasons": [],
        }
    )
    fifa_test = season.isin(fifa_config.test_seasons)
    compare(
        df[season <= "2021/22"],
        pd.concat([df, fifa], axis=1)[season <= "2021/22"],
        fifa_config,
        {"2020/21–2021/22, with ratings": (fifa_test & has_fifa)[season <= "2021/22"]},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
