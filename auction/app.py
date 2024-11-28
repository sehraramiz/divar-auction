"""HTTP API for auction app"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import auction_router


app = FastAPI()
app.include_router(auction_router)

app.mount("/static", StaticFiles(directory="auction/static"), name="static")
