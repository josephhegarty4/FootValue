from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

TABLE_BY_SOURCE = {
    "raw": "fbref_raw",
    "joined": "phase1_joined",
    "unmatched": "phase1_unmatched",
    "fees": "transfermarkt_fees",
    "injuries": "transfermarkt_injuries",
    "transfermarkt": "transfermarkt_combined",
}


def ensure_db_directory(db_path: str | Path) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_phase1_data(
    db_path: str | Path,
    fbref_df: pd.DataFrame,
    fees_df: pd.DataFrame,
    injuries_df: pd.DataFrame,
    transfermarkt_df: pd.DataFrame,
    joined_df: pd.DataFrame,
    unmatched_df: pd.DataFrame,
) -> Path:
    path = ensure_db_directory(db_path)
    with sqlite3.connect(path) as connection:
        fbref_df.to_sql(TABLE_BY_SOURCE["raw"], connection, if_exists="replace", index=False)
        fees_df.to_sql(TABLE_BY_SOURCE["fees"], connection, if_exists="replace", index=False)
        injuries_df.to_sql(TABLE_BY_SOURCE["injuries"], connection, if_exists="replace", index=False)
        transfermarkt_df.to_sql(TABLE_BY_SOURCE["transfermarkt"], connection, if_exists="replace", index=False)
        joined_df.to_sql(TABLE_BY_SOURCE["joined"], connection, if_exists="replace", index=False)
        unmatched_df.to_sql(TABLE_BY_SOURCE["unmatched"], connection, if_exists="replace", index=False)
    return path


def load_dataset(db_path: str | Path, source: str) -> pd.DataFrame:
    normalized = source.lower()
    table_name = TABLE_BY_SOURCE.get(normalized)
    if table_name is None:
        raise ValueError(f"Unsupported source '{source}'. Expected one of {sorted(TABLE_BY_SOURCE)}")

    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame()

    with sqlite3.connect(path) as connection:
        table_exists = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            connection,
            params=(table_name,),
        )
        if table_exists.empty:
            return pd.DataFrame()
        dataframe = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
    return dataframe
