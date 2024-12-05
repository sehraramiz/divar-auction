ifndef LANG
override LANG = fa
endif
MSGDIR = auction/locales/$(LANG)/LC_MESSAGES
MSGFILE = auction/locales/$(LANG)/LC_MESSAGES/messages.po
MSGBASE = auction/messages.pot
BASEDIR = auction

test:
	uv run pytest -v .
format:
	uv run ruff format auction tests
check:
	uv run ruff check auction tests --fix
	uv run mypy .
makemessages:
	uv run pybabel extract -F babel.cfg -o $(MSGBASE) $(BASEDIR)
	sed -i -e 's/CHARSET/UTF-8/g' $(MSGBASE)
	mkdir -p $(MSGDIR)
	- cp -n $(MSGBASE) $(MSGFILE)
	msgmerge --update $(MSGFILE) $(MSGBASE)
compilemessages:
	msgfmt -o $(MSGDIR)/messages.mo $(MSGFILE)
