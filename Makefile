.PHONY: install lint format test help

install:
	python3 -m pip install --upgrade pip
	python3 -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

test:
	pytest

help:
	hiring-radar --help
