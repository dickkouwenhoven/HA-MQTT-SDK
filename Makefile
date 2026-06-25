.PHONY: install test lint format format-check type clean check ci

# ── Setup ─────────────────────────────────────────────────────────────────────

install:
	pip install -e ".[dev]"

# ── Quality ───────────────────────────────────────────────────────────────────

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format . --check --diff

type:
	mypy src/ha_mqtt_sdk

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	pytest --cov=ha_mqtt_sdk --cov-report=term-missing --cov-fail-under=100

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

# ── CI pipeline (read-only — no file changes) ─────────────────────────────────

ci: lint format-check type test
