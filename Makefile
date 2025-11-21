PYTHON ?= python3

.PHONY: install lint test up

install:
	poetry install

lint:
	poetry run ruff check .

test:
	poetry run pytest

up:
	docker compose up --build -d
