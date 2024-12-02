"""HTTP API for auction app"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from api import auction_router
from config import config
import exception


session_middleware = Middleware(
    SessionMiddleware, secret_key=config.secret_key, https_only=True
)
if config.debug:
    session_middleware = Middleware(
        SessionMiddleware, secret_key=config.secret_key, https_only=False
    )

app = FastAPI(
    middleware=[session_middleware],
    openapi_url=config.openapi_url,
    docs_url=config.docs_url,
    redoc_url=None,
    exception_handlers=exception.exception_handlers,  # type: ignore
)
app.include_router(auction_router)

app.mount("/static", StaticFiles(directory="auction/static"), name="static")
