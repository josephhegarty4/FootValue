from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.scrapers.fbref import fetch_fbref_player_stats
from src.scrapers.transfermarkt import (
    bootstrap_transfermarkt_templates,
    combine_transfermarkt_data,
    load_transfermarkt_fees,
    load_transfermarkt_injuries,
)
from src.utils.inflation import build_linear_proxy_index, normalize_fee
from src.utils.name_matching import fuzzy_join


def run_phase1_pipeline(
    league: str = "EPL",
    season: str = "2022-2023",
    raw_dir: str | Path = "src/data/raw",
    processed_dir: str | Path = "src/data/processed",
    score_cutoff: float = 88.0,
    strict_soccerdata: bool = False,
    force_refresh_fbref: bool = False,
    fbref_mirror_csv: str | Path | None = None,
    min_fbref_rows: int = 0,
) -> dict[str, Path]:
    raw_directory = Path(raw_dir)
    processed_directory = Path(processed_dir)
    processed_directory.mkdir(parents=True, exist_ok=True)

    fbref_df = fetch_fbref_player_stats(
        league=league,
        season=season,
        raw_dir=raw_directory,
        force_refresh=force_refresh_fbref,
        strict_soccerdata=strict_soccerdata,
        mirror_csv_source=fbref_mirror_csv,
    )

    if min_fbref_rows > 0 and len(fbref_df) < min_fbref_rows:
        raise ValueError(
            f"FBref dataset too small: {len(fbref_df)} rows (minimum required: {min_fbref_rows}). "
            "Check --fbref-mirror-csv path or data source."
        )
    fees_path, injuries_path = bootstrap_transfermarkt_templates(raw_dir=raw_directory)

    fees_df = load_transfermarkt_fees(fees_path)
    injuries_df = load_transfermarkt_injuries(injuries_path)
    transfermarkt_df = combine_transfermarkt_data(fees_df, injuries_df)

    if transfermarkt_df.empty:
        joined_df = fbref_df.copy()
        joined_df["matched_name"] = pd.NA
        joined_df["match_score"] = pd.NA
        joined_df["match_method"] = "no-transfermarkt-data"
        unmatched_df = fbref_df[["player_name"]].rename(columns={"player_name": "source_name"})
    else:
        joined_df, unmatched_df = fuzzy_join(
            left_df=fbref_df,
            right_df=transfermarkt_df,
            left_name_col="player_name",
            right_name_col="player_name",
            manual_corrections_path=raw_directory / "manual_name_corrections.json",
            score_cutoff=score_cutoff,
        )

    if "transfer_fee_eur" in joined_df.columns and "transfer_year" in joined_df.columns:
        fee_rows = joined_df["transfer_fee_eur"].notna() & joined_df["transfer_year"].notna()
        if fee_rows.any():
            index = build_linear_proxy_index(
                years=joined_df.loc[fee_rows, "transfer_year"].astype(int).tolist() + [2026],
                anchor_year=2026,
                annual_rate=0.03,
            )
            joined_df.loc[fee_rows, "transfer_fee_2026_proxy_eur"] = joined_df.loc[fee_rows].apply(
                lambda row: normalize_fee(
                    amount=float(row["transfer_fee_eur"]),
                    from_year=int(row["transfer_year"]),
                    index=index,
                    to_year=2026,
                ),
                axis=1,
            )

    joined_output = processed_directory / f"phase1_joined_{league.lower()}_{season}.csv"
    unmatched_output = processed_directory / f"phase1_unmatched_{league.lower()}_{season}.csv"

    joined_df.to_csv(joined_output, index=False)
    unmatched_df.to_csv(unmatched_output, index=False)

    return {
        "fbref_cache": raw_directory / f"fbref_{league.lower()}_{season}_players.csv",
        "transfermarkt_fees_template": fees_path,
        "transfermarkt_injuries_template": injuries_path,
        "joined_output": joined_output,
        "unmatched_output": unmatched_output,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 1 FootValue pipeline")
    parser.add_argument("--strict-soccerdata", action="store_true", help="Fail if soccerdata cannot be used")
    parser.add_argument("--force-refresh-fbref", action="store_true", help="Ignore FBref cache and fetch fresh data")
    parser.add_argument("--fbref-mirror-csv", type=str, default=None, help="Path or URL to mirror CSV when FBref blocks requests")
    parser.add_argument("--min-fbref-rows", type=int, default=0, help="Fail if FBref rows are below this threshold")
    args = parser.parse_args()

    outputs = run_phase1_pipeline(
        strict_soccerdata=args.strict_soccerdata,
        force_refresh_fbref=args.force_refresh_fbref,
        fbref_mirror_csv=args.fbref_mirror_csv,
        min_fbref_rows=args.min_fbref_rows,
    )
    for key, path in outputs.items():
        print(f"{key}: {path}")
