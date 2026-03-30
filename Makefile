.PHONY: venv312 install312 test phase1 phase1-soccerdata-strict phase1-soccerdata-mirror phase1-soccerdata-mirror-safe frontend

venv312:
	/opt/homebrew/bin/python3.12 -m venv .venv312

install312:
	. .venv312/bin/activate && python -m pip install -U pip && python -m pip install -r requirements.txt

test:
	. .venv312/bin/activate && python -m pytest -q

phase1:
	. .venv312/bin/activate && python -m src.pipeline_phase1

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
