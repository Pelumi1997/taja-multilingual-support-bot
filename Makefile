.PHONY: install dev test lint format run validate docker-up docker-down

install:
	python -m pip install -e .

dev:
	python -m pip install -e ".[dev,redis]"

test:
	pytest --cov=taja_bot --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

run:
	uvicorn taja_bot.api:app --reload --host 0.0.0.0 --port 8000

validate:
	python scripts/validate_faqs.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
