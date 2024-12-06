"""HTTP API for auction app"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from auction import exception, i18n
from auction.api import auction_router
from auction.config import config
from auction.log import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


session_middleware = Middleware(
    SessionMiddleware, secret_key=config.secret_key, https_only=True
)
if config.debug:
    session_middleware = Middleware(
        SessionMiddleware, secret_key=config.secret_key, https_only=False
    )

app = FastAPI(
    lifespan=lifespan,
    middleware=[session_middleware],
    openapi_url=config.openapi_url,
    docs_url=config.docs_url,
    redoc_url=None,
    exception_handlers=exception.exception_handlers,  # type: ignore
)
app.include_router(auction_router)

app.mount("/static", StaticFiles(directory="auction/static"), name="static")


@app.middleware("http")
async def set_locale(request: Request, call_next):
    accept_language = request.headers.get("accept-language", "en")
    lang_code_header = accept_language.split(",")[0].split(";")[0][:2]
    lang_code = request.query_params.get("hl", lang_code_header)
    i18n.set_lang_code(lang_code)
    response = await call_next(request)
    response.headers["Content-Language"] = lang_code
    return response
