#!/bin/bash -ex

uv run fastapi run auction/api/app.py --port ${PORT:-8000} --reload
