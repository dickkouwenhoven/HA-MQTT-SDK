install:
	pip install -r requirements-dev.txt

test:
	pytest --cov=ha_mqtt_sdk

lint:
	ruff check .

format:
	ruff format .

type:
	mypy ha_mqtt_sdk

ci:
	ruff check . && mypy ha_mqtt_sdk && pytest
