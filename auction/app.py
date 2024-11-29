"""HTTP API for auction app"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from api import auction_router
from config import config


session_middleware = Middleware(
    SessionMiddleware, secret_key=config.secret_key, https_only=True
)
if config.debug:
    session_middleware = Middleware(
        SessionMiddleware, secret_key=config.secret_key, https_only=False
    )

app = FastAPI(middleware=[session_middleware])
app.include_router(auction_router)

app.mount("/static", StaticFiles(directory="auction/static"), name="static")
