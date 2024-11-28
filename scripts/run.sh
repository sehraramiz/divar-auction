#!/bin/bash -ex

uv run fastapi run auction/app.py --port ${PORT:-8000} --reload
