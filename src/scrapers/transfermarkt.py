from __future__ import annotations

from pathlib import Path

import pandas as pd


def bootstrap_transfermarkt_templates(raw_dir: str | Path = "src/data/raw") -> tuple[Path, Path]:
    raw_directory = Path(raw_dir)
    raw_directory.mkdir(parents=True, exist_ok=True)

    fees_path = raw_directory / "transfermarkt_fees_epl_2022_2023.csv"
    injuries_path = raw_directory / "transfermarkt_injuries_epl_2022_2023.csv"

    if not fees_path.exists():
        pd.DataFrame(
            columns=[
                "player_name",
                "club",
                "transfer_fee_eur",
                "transfer_year",
                "from_club",
                "to_club",
            ]
        ).to_csv(fees_path, index=False)

    if not injuries_path.exists():
        pd.DataFrame(
            columns=[
                "player_name",
                "club",
                "season",
                "injury_days",
                "injury_count",
            ]
        ).to_csv(injuries_path, index=False)

    return fees_path, injuries_path


def load_transfermarkt_fees(path: str | Path) -> pd.DataFrame:
    dataframe = pd.read_csv(path)
    expected = {"player_name", "club", "transfer_fee_eur", "transfer_year", "from_club", "to_club"}
    missing = expected.difference(dataframe.columns)
    if missing:
        raise ValueError(f"Missing fee columns: {sorted(missing)}")
    dataframe["transfer_fee_eur"] = pd.to_numeric(dataframe["transfer_fee_eur"], errors="coerce")
    dataframe["transfer_year"] = pd.to_numeric(dataframe["transfer_year"], errors="coerce").astype("Int64")
    return dataframe


def load_transfermarkt_injuries(path: str | Path) -> pd.DataFrame:
    dataframe = pd.read_csv(path)
    expected = {"player_name", "club", "season", "injury_days", "injury_count"}
    missing = expected.difference(dataframe.columns)
    if missing:
        raise ValueError(f"Missing injury columns: {sorted(missing)}")
    dataframe["injury_days"] = pd.to_numeric(dataframe["injury_days"], errors="coerce")
    dataframe["injury_count"] = pd.to_numeric(dataframe["injury_count"], errors="coerce")
    return dataframe


def combine_transfermarkt_data(fees_df: pd.DataFrame, injuries_df: pd.DataFrame) -> pd.DataFrame:
    injuries_agg = (
        injuries_df.groupby(["player_name", "club"], dropna=False, as_index=False)
        .agg(total_injury_days=("injury_days", "sum"), total_injury_count=("injury_count", "sum"))
    )

    fees_sorted = fees_df.sort_values(["player_name", "transfer_year"], ascending=[True, False])
    latest_fees = fees_sorted.drop_duplicates(subset=["player_name", "club"], keep="first")

    return latest_fees.merge(injuries_agg, on=["player_name", "club"], how="outer")
