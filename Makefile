ifndef LANG
override LANG = fa
endif
MSGDIR = auction/locales/$(LANG)/LC_MESSAGES
MSGFILE = auction/locales/$(LANG)/LC_MESSAGES/messages.po
MSGBASE = auction/messages.pot
BASEDIR = auction

test:
	uv run pytest -s .
format:
	uv run ruff format auction tests
check:
	uv run ruff check auction tests --fix
	uv run mypy .
makemigrations:
	uv run alembic revision --autogenerate
migrate:
	uv run alembic upgrade head
makemessages:
	uv run pybabel extract -F babel.cfg -o $(MSGBASE) $(BASEDIR)
	sed -i -e 's/CHARSET/UTF-8/g' $(MSGBASE)
	mkdir -p $(MSGDIR)
	- cp -n $(MSGBASE) $(MSGFILE)
	msgmerge --update $(MSGFILE) $(MSGBASE)
compilemessages:
	uv run pybabel compile -f -o $(MSGDIR)/messages.mo -i $(MSGFILE)
build-docker:
	docker compose build auction
run-docker: build-docker
	docker compose up -d auction
