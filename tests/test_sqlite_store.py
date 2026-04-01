from pathlib import Path

import pandas as pd

from src.db.sqlite_store import load_dataset, save_phase1_data


def test_save_and_load_phase1_datasets(tmp_path: Path) -> None:
    db_path = tmp_path / "footvalue.db"

    fbref_df = pd.DataFrame([{"player_name": "Bukayo Saka", "club": "Arsenal", "season": "2022-2023"}])
    fees_df = pd.DataFrame([{"player_name": "Bukayo Saka", "transfer_fee_eur": 0, "transfer_year": 2019}])
    injuries_df = pd.DataFrame([{"player_name": "Bukayo Saka", "injury_days": 7, "injury_count": 1}])
    transfermarkt_df = pd.DataFrame([{"player_name": "Bukayo Saka", "club": "Arsenal"}])
    joined_df = pd.DataFrame([{"player_name": "Bukayo Saka", "matched_name": "Bukayo Saka", "match_method": "exact-normalized"}])
    unmatched_df = pd.DataFrame(columns=["source_name", "matched_name", "match_score", "match_method"])

    save_phase1_data(
        db_path=db_path,
        fbref_df=fbref_df,
        fees_df=fees_df,
        injuries_df=injuries_df,
        transfermarkt_df=transfermarkt_df,
        joined_df=joined_df,
        unmatched_df=unmatched_df,
    )

    loaded_raw = load_dataset(db_path=db_path, source="raw")
    loaded_joined = load_dataset(db_path=db_path, source="joined")

    assert len(loaded_raw) == 1
    assert loaded_raw.iloc[0]["player_name"] == "Bukayo Saka"
    assert len(loaded_joined) == 1
    assert loaded_joined.iloc[0]["match_method"] == "exact-normalized"
