.PHONY: fetch clean extract docs check

fetch:
	uv run python scripts/fetch.py

clean:
	uv run python scripts/clean.py
	uv run python scripts/make_prep_inputs.py

extract:
	uv run python scripts/build_hyper.py
	uv run python scripts/build_workbook.py

docs:
	uv run python scripts/metrics.py
	uv run python scripts/write_readme.py

check:
	uv run python scripts/check.py
