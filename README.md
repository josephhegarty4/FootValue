# FootValue
Algorithm platform for calculating real life player values.

## Phase 1 kickoff (week 1-2)

Start narrow: **EPL 2022/23 only**.

### Scope
- Source 1: FBref player stats (scraped + cached)
- Source 2: Transfermarkt fees + injury history (starter CSV templates)
- Join key: fuzzy player name matching + manual corrections
- Output: joined and unmatched CSVs in `src/data/processed` + SQLite DB in `src/data/footvalue.db`

### Current structure
```
src/
├── scrapers/
│   ├── fbref.py
│   └── transfermarkt.py
├── data/
│   ├── raw/
│   └── processed/
├── utils/
│   ├── name_matching.py
│   └── inflation.py
└── pipeline_phase1.py
```

### First run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline_phase1
```

### FBref backend notes
- The scraper in `src/scrapers/fbref.py` is **soccerdata-first when available** and falls back to `requests + pandas.read_html`.
- On this machine (`Python 3.14`), current `soccerdata` releases are not installable due dependency constraints.
- To force soccerdata usage, run the project in Python `3.12` or `3.13` and install `soccerdata` in that environment.

### True soccerdata mode (strict)
Use this when you want the run to fail unless FBref data is coming from `soccerdata`.

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref
```

If FBref returns `403` from your network, strict mode will fail fast by design.
In that case, either run from a different network/IP or temporarily omit `--strict-soccerdata` so fallback scraping/cache can proceed.

### Makefile shortcuts
```bash
make venv312
make install312
make test
make phase1-soccerdata-strict
make phase1-db
make kaggle-import DATASET=owner/dataset
make phase1-season SEASON=2024-2025 MIRROR=/absolute/path/to/file.csv
make phase1-season-auto SEASON=2024-2025
```

### Kaggle import flow (for 2024-2025)
1. Configure Kaggle API credentials (`~/.kaggle/kaggle.json`).
2. Import dataset files into `src/data/raw/incoming`.
3. Run the pipeline with explicit season and mirror path.

```bash
source .venv312/bin/activate
python -m src.data.kaggle_import --dataset owner/dataset --output-dir src/data/raw/incoming --backend kagglehub
python -m src.pipeline_phase1 --season 2024-2025 --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv /absolute/path/to/imported_2024_2025.csv --min-fbref-rows 400 --db-path src/data/footvalue.db
```

Auto-detect latest imported CSV (no filename typing):

```bash
source .venv312/bin/activate
python -m src.pipeline_phase1 --season 2024-2025 --strict-soccerdata --force-refresh-fbref --auto-fbref-mirror --incoming-dir src/data/raw/incoming --min-fbref-rows 400 --db-path src/data/footvalue.db
```

If you want to use your exact snippet style, this is now supported through `kagglehub`:

```python
import kagglehub

path = kagglehub.dataset_download("eduardopalmieri/premier-league-player-stats-season-2425")
print("Path to dataset files:", path)
```

### Strict mode with mirror CSV fallback
If strict mode is blocked by FBref `403`, provide a mirror CSV (same schema as FBref standard player table columns).

```bash
make phase1-soccerdata-mirror MIRROR=/absolute/path/to/fbref_mirror.csv
```

Equivalent direct command:
```bash
source .venv312/bin/activate
python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv /absolute/path/to/fbref_mirror.csv
```

Recommended safe command (rejects tiny/demo files):
```bash
source .venv312/bin/activate
python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv /absolute/path/to/full_fbref_epl_2022_2023.csv --min-fbref-rows 400
```

### Temporary frontend data viewer
Use this to quickly verify imported players are present.

```bash
source .venv312/bin/activate
pip install -r requirements.txt
python -m src.web.app
```

Then open:
- `http://127.0.0.1:8000`

API endpoint:
- `http://127.0.0.1:8000/api/players?source=raw`
- `http://127.0.0.1:8000/api/players?source=joined`

The frontend now reads from SQLite first (`src/data/footvalue.db`) and falls back to CSV if DB is missing.

### What the first run does
1. Scrapes FBref EPL 2022/23 player stats and caches to `src/data/raw`.
2. Creates Transfermarkt starter templates if missing:
	- `src/data/raw/transfermarkt_fees_epl_2022_2023.csv`
	- `src/data/raw/transfermarkt_injuries_epl_2022_2023.csv`
3. Tries to join FBref and Transfermarkt player names using `rapidfuzz`.
4. Writes outputs:
	- `src/data/processed/phase1_joined_epl_2022-2023.csv`
	- `src/data/processed/phase1_unmatched_epl_2022-2023.csv`

### Manual name correction workflow
Maintain mappings in `src/data/raw/manual_name_corrections.json` from day one.

Example:
```json
{
  "m odegaard": "Martin Odegaard",
  "diogo jota": "Diogo Jota"
}
```

The pipeline always prioritizes manual corrections before fuzzy matching.

### Recommended execution order
1. Run pipeline once to generate initial unmatched names.
2. Fill Transfermarkt templates with confirmed fees + injury history.
3. Add manual corrections for recurring name mismatches.
4. Re-run until unmatched count is acceptable.
