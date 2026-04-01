.PHONY: venv312 install312 test phase1 phase1-soccerdata-strict phase1-soccerdata-mirror phase1-soccerdata-mirror-safe phase1-season phase1-season-auto kaggle-import frontend

venv312:
	/opt/homebrew/bin/python3.12 -m venv .venv312

install312:
	. .venv312/bin/activate && python -m pip install -U pip && python -m pip install -r requirements.txt

test:
	. .venv312/bin/activate && python -m pytest -q

phase1:
	. .venv312/bin/activate && python -m src.pipeline_phase1

phase1-season:
	@if [ -z "$(SEASON)" ]; then \
		echo "Usage: make phase1-season SEASON=2024-2025 MIRROR=/absolute/path/to/file.csv"; \
		exit 1; \
	fi
	@if [ -z "$(MIRROR)" ]; then \
		echo "Usage: make phase1-season SEASON=2024-2025 MIRROR=/absolute/path/to/file.csv"; \
		exit 1; \
	fi
	. .venv312/bin/activate && python -m src.pipeline_phase1 --season "$(SEASON)" --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv "$(MIRROR)" --min-fbref-rows 400 --db-path src/data/footvalue.db

phase1-season-auto:
	@if [ -z "$(SEASON)" ]; then \
		echo "Usage: make phase1-season-auto SEASON=2024-2025 [INCOMING=src/data/raw/incoming]"; \
		exit 1; \
	fi
	. .venv312/bin/activate && python -m src.pipeline_phase1 --season "$(SEASON)" --strict-soccerdata --force-refresh-fbref --auto-fbref-mirror --incoming-dir "$(if $(INCOMING),$(INCOMING),src/data/raw/incoming)" --min-fbref-rows 400 --db-path src/data/footvalue.db

kaggle-import:
	@if [ -z "$(DATASET)" ]; then \
		echo "Usage: make kaggle-import DATASET=owner/dataset [FILE=filename.csv] [BACKEND=kagglehub|kaggle-cli]"; \
		exit 1; \
	fi
	. .venv312/bin/activate && python -m src.data.kaggle_import --dataset "$(DATASET)" --output-dir src/data/raw/incoming $(if $(FILE),--file-name "$(FILE)") --backend "$(if $(BACKEND),$(BACKEND),kagglehub)"

phase1-db:
	. .venv312/bin/activate && python -m src.pipeline_phase1 --db-path src/data/footvalue.db

phase1-soccerdata-strict:
	. .venv312/bin/activate && python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref

phase1-soccerdata-mirror:
	@if [ -z "$(MIRROR)" ]; then \
		echo "Usage: make phase1-soccerdata-mirror MIRROR=/absolute/path/to/fbref_mirror.csv"; \
		exit 1; \
	fi
	. .venv312/bin/activate && python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv "$(MIRROR)"

phase1-soccerdata-mirror-safe:
	@if [ -z "$(MIRROR)" ]; then \
		echo "Usage: make phase1-soccerdata-mirror-safe MIRROR=/absolute/path/to/fbref_mirror.csv MIN_ROWS=400"; \
		exit 1; \
	fi
	@if [ -z "$(MIN_ROWS)" ]; then \
		echo "Usage: make phase1-soccerdata-mirror-safe MIRROR=/absolute/path/to/fbref_mirror.csv MIN_ROWS=400"; \
		exit 1; \
	fi
	. .venv312/bin/activate && python -m src.pipeline_phase1 --strict-soccerdata --force-refresh-fbref --fbref-mirror-csv "$(MIRROR)" --min-fbref-rows "$(MIN_ROWS)"

frontend:
	. .venv312/bin/activate && python -m src.web.app
