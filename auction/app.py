"""HTTP API for auction app"""

from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
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


session_middleware_kwargs = {"secret_key": config.secret_key, "https_only": True}
if config.debug:
    session_middleware_kwargs["https_only"] = False
session_middleware = Middleware(SessionMiddleware, **session_middleware_kwargs)
correlation_id_middleware = Middleware(CorrelationIdMiddleware)

app = FastAPI(
    lifespan=lifespan,
    middleware=[session_middleware, correlation_id_middleware],
    openapi_url=config.openapi_url,
    docs_url=config.docs_url,
    redoc_url=None,
    exception_handlers=exception.exception_handlers,  # type: ignore
)
app.include_router(auction_router)

app.mount("/static", StaticFiles(directory="auction/static"), name="static")


@app.middleware("http")
async def set_locale(request: Request, call_next):
    lang_code = request.query_params.get("hl", "fa")
    i18n.set_lang_code(lang_code)
    response = await call_next(request)
    response.headers["Content-Language"] = lang_code
    return response
