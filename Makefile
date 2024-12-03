test:
	uv run pytest -v .
format:
	uv run ruff format auction tests
check:
	uv run ruff check auction tests --fix
	uv run mypy .
