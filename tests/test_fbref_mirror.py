from pathlib import Path

import pandas as pd

from src.scrapers.fbref import fetch_fbref_player_stats


def test_strict_soccerdata_with_mirror_csv(tmp_path: Path) -> None:
    mirror_path = tmp_path / "fbref_mirror.csv"
    pd.DataFrame(
        [
            {
                "Player": "Martin Odegaard",
                "Squad": "Arsenal",
                "Nation": "NOR",
                "Pos": "MF",
                "Age": 24,
                "Born": 1998,
                "90s": 35.0,
                "Gls": 15,
                "Ast": 7,
                "xG": 10.5,
                "xAG": 6.3,
            }
        ]
    ).to_csv(mirror_path, index=False)

    result = fetch_fbref_player_stats(
        league="EPL",
        season="2022-2023",
        raw_dir=tmp_path,
        force_refresh=True,
        strict_soccerdata=True,
        mirror_csv_source=mirror_path,
    )

    assert len(result) == 1
    assert result.iloc[0]["player_name"] == "Martin Odegaard"
    assert result.iloc[0]["club"] == "Arsenal"
    assert result.iloc[0]["season"] == "2022-2023"
