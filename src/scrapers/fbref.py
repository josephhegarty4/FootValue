from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import requests
try:
    import soccerdata as sd
except Exception:
    sd = None


def _flatten_columns(columns: pd.Index) -> list[str]:
    if isinstance(columns, pd.MultiIndex):
        flattened: list[str] = []
        for parts in columns.tolist():
            cleaned_parts = [str(part).strip() for part in parts if str(part) not in {"", "nan"}]
            flattened.append("_".join(cleaned_parts))
        return flattened
    return [str(column).strip() for column in columns]


def _empty_fbref_frame(season: str) -> pd.DataFrame:
    dataframe = pd.DataFrame(
        columns=[
            "player_name",
            "club",
            "nation",
            "position",
            "age",
            "birth_year",
            "minutes_90s",
            "goals",
            "assists",
            "expected_goals",
            "expected_assists",
            "league",
            "season",
        ]
    )
    dataframe["league"] = "EPL"
    dataframe["season"] = season
    return dataframe


def _normalize_fbref_columns(dataframe: pd.DataFrame, season: str) -> pd.DataFrame:
    rename_map = {
        "Player": "player_name",
        "Squad": "club",
        "Team": "club",
        "Nation": "nation",
        "Position": "position",
        "Pos": "position",
        "Age": "age",
        "Born": "birth_year",
        "Minutes": "minutes",
        "90s": "minutes_90s",
        "Goals": "goals",
        "Gls": "goals",
        "Assists": "assists",
        "Ast": "assists",
        "Expected Goals (xG)": "expected_goals",
        "xG": "expected_goals",
        "Expected Assists (xAG)": "expected_assists",
        "xAG": "expected_assists",
    }
    dataframe = dataframe.rename(columns={key: value for key, value in rename_map.items() if key in dataframe.columns})

    # Keep all available stat columns while normalizing names.
    seen: dict[str, int] = {}
    normalized_columns: list[str] = []
    for column in dataframe.columns:
        base = str(column).strip().lower()
        base = re.sub(r"[^a-z0-9]+", "_", base)
        base = re.sub(r"_+", "_", base).strip("_") or "column"
        if base in seen:
            seen[base] += 1
            normalized = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
            normalized = base
        normalized_columns.append(normalized)
    dataframe.columns = normalized_columns

    if "minutes_90s" not in dataframe.columns and "minutes" in dataframe.columns:
        minutes = pd.to_numeric(dataframe["minutes"], errors="coerce")
        dataframe["minutes_90s"] = minutes / 90.0

    required_columns = [
        "player_name",
        "club",
        "nation",
        "position",
        "age",
        "birth_year",
        "minutes_90s",
        "goals",
        "assists",
        "expected_goals",
        "expected_assists",
    ]
    for column in required_columns:
        if column not in dataframe.columns:
            dataframe[column] = pd.NA

    # Ensure required columns come first but keep every other stat column too.
    additional_columns = [column for column in dataframe.columns if column not in required_columns]
    dataframe = dataframe[required_columns + additional_columns].copy()
    dataframe["league"] = "EPL"
    dataframe["season"] = season
    return dataframe


def _fetch_with_soccerdata(season: str) -> pd.DataFrame:
    if sd is None:
        raise ImportError("soccerdata is not available in this environment")
    season_start_year = int(season.split("-")[0])
    fbref = sd.FBref(leagues="ENG-Premier League", seasons=[season_start_year])
    dataframe = fbref.read_player_season_stats(stat_type="standard")
    if dataframe is None or dataframe.empty:
        return _empty_fbref_frame(season)

    dataframe = dataframe.reset_index()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    dataframe = dataframe[dataframe.get("Player", "").astype(str).str.lower() != "player"].copy()
    dataframe = _normalize_fbref_columns(dataframe, season)
    return dataframe


def _fetch_with_read_html(url: str, season: str) -> pd.DataFrame:
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        timeout=30,
    )
    response.raise_for_status()
    tables = pd.read_html(response.text)
    if not tables:
        raise RuntimeError(f"No tables found on {url}")

    dataframe = tables[0].copy()
    dataframe.columns = _flatten_columns(dataframe.columns)
    dataframe = dataframe[dataframe.get("Player", "").astype(str).str.lower() != "player"].copy()
    return _normalize_fbref_columns(dataframe, season)


def fetch_fbref_player_stats(
    league: str = "EPL",
    season: str = "2022-2023",
    raw_dir: str | Path = "src/data/raw",
    force_refresh: bool = False,
    strict_soccerdata: bool = False,
    mirror_csv_source: str | Path | None = None,
) -> pd.DataFrame:
    if league != "EPL":
        raise ValueError("Phase 1 starter currently supports only EPL")

    raw_directory = Path(raw_dir)
    raw_directory.mkdir(parents=True, exist_ok=True)
    cache_path = raw_directory / f"fbref_{league.lower()}_{season}_players.csv"

    if cache_path.exists() and not force_refresh and not strict_soccerdata:
        return pd.read_csv(cache_path)

    url = (
        "https://fbref.com/en/comps/9/"
        f"{season}/stats/players/{season}-Premier-League-Stats"
    )

    def _fetch_with_mirror(source: str | Path) -> pd.DataFrame:
        mirror_frame = pd.read_csv(source)
        return _normalize_fbref_columns(mirror_frame, season)

    if mirror_csv_source is not None:
        try:
            dataframe = _fetch_with_mirror(mirror_csv_source)
            dataframe.to_csv(cache_path, index=False)
            return dataframe
        except Exception:
            if strict_soccerdata:
                raise

    try:
        dataframe = _fetch_with_soccerdata(season=season)
    except Exception as soccerdata_error:
        if mirror_csv_source is not None:
            try:
                dataframe = _fetch_with_mirror(mirror_csv_source)
            except Exception:
                if strict_soccerdata:
                    raise soccerdata_error
                dataframe = _empty_fbref_frame(season)
        elif strict_soccerdata:
            raise soccerdata_error
        else:
            try:
                dataframe = _fetch_with_read_html(url=url, season=season)
            except Exception:
                if cache_path.exists():
                    return pd.read_csv(cache_path)
                dataframe = _empty_fbref_frame(season)

    dataframe.to_csv(cache_path, index=False)
    return dataframe
