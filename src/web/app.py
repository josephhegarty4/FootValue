from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

from src.db.sqlite_store import load_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "src/data/raw/fbref_epl_2022-2023_players.csv"
JOINED_CSV = PROJECT_ROOT / "src/data/processed/phase1_joined_epl_2022-2023.csv"
DATABASE_PATH = PROJECT_ROOT / "src/data/footvalue.db"

app = Flask(__name__, template_folder="templates")


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    dataframe = pd.read_csv(path)
    return dataframe.fillna("")


def _dataset_from_source(source: str) -> pd.DataFrame:
    database_df = load_dataset(DATABASE_PATH, source)
    if not database_df.empty:
        return database_df.fillna("")

    if source == "joined":
        return _load_csv(JOINED_CSV)
    return _load_csv(RAW_CSV)


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/players")
def players() -> tuple[object, int] | object:
    source = request.args.get("source", "raw").lower()
    search = request.args.get("search", "").strip().lower()
    limit = min(int(request.args.get("limit", "200")), 1000)

    dataframe = _dataset_from_source(source)
    if dataframe.empty:
        return jsonify({"source": source, "count": 0, "columns": [], "rows": []})

    if search:
        text_frame = dataframe.astype(str).apply(lambda col: col.str.lower())
        mask = text_frame.apply(lambda row: row.str.contains(search, regex=False)).any(axis=1)
        dataframe = dataframe[mask]

    result = dataframe.head(limit)
    return jsonify(
        {
            "source": source,
            "count": int(len(dataframe)),
            "columns": result.columns.tolist(),
            "rows": result.to_dict(orient="records"),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
