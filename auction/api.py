"""HTTP API for auction app"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from model import AuctionStartInput, Auction, PlaceBid, Bid
from _types import AuctionID, UserID, PostToken
from repo import auction_repo
import service
import exception
from divar import divar_client, GetPostRequest


auction_router = APIRouter(prefix="/auction")
templates = Jinja2Templates(directory="auction/pages")


async def get_user_id(token: str) -> str:
    """get user id from Divar using user token"""
    return ""


@auction_router.get("/")
async def auctions(request: Request, post_token: PostToken) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="auctions.html",
        context={"auctions": auction_repo.auctions},
    )


@auction_router.get("/start/{post_token}")
async def new_auction(
    request: Request, post_token: PostToken, seller_id: UserID
) -> HTMLResponse:
    post = divar_client.finder.get_post(GetPostRequest(token=post_token))
    if post is None:
        raise exception.PostNotFound()
    return templates.TemplateResponse(
        request=request,
        name="start_auction.html",
        context={"seller_id": seller_id},
    )


@auction_router.post("/start")
async def start_auction(seller_id: UserID, auction_data: AuctionStartInput) -> Auction:
    result = await service.start_auction(
        auction_repo=auction_repo,
        divar_client=divar_client,
        seller_id=seller_id,
        auction_data=auction_data,
    )
    auction_repo._commit()
    return result


@auction_router.get("/{auction_id}")
async def read_auction(auction_id: AuctionID) -> Auction:
    auction = await auction_repo.read_acution_by_id(auction_id=auction_id)
    if auction is None:
        raise exception.AuctionNotFound()
    return auction


@auction_router.get("/info/{post_token}")
async def auction_detail(post_token: PostToken) -> Auction:
    result = await service.read_auction(
        auction_repo=auction_repo, post_token=post_token
    )
    return result


@auction_router.post("/place-bid")
async def place_bid(bidder_id: UserID, bid_data: PlaceBid) -> Bid:
    result = await service.place_bid(
        auction_repo=auction_repo, bid_data=bid_data, bidder_id=bidder_id
    )
    auction_repo._commit()
    return result
