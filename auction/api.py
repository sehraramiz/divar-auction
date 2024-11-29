"""HTTP API for auction app"""

from typing import Annotated

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from model import (
    AuctionStartInput,
    Auction,
    PlaceBid,
    Bid,
    AuctionSellerView,
    AuctionBidderView,
)
from _types import AuctionID, UserID, PostToken
from repo import auction_repo
import service
import exception
from divar import divar_client, DivarReturnUrl
import auth


auction_router = APIRouter(prefix="/auction")
templates = Jinja2Templates(directory="auction/pages")


async def get_user_id(token: str) -> str:
    """get user id from Divar using user token"""
    return ""


@auction_router.get("/")
async def auctions(
    request: Request,
    post_token: PostToken,
    return_url: DivarReturnUrl,
    user_ids: list[UserID] = Depends(auth.authorize_user),
) -> HTMLResponse:
    result = await service.auction_detail(
        auction_repo=auction_repo,
        divar_client=divar_client,
        user_ids=user_ids,
        post_token=post_token,
    )
    request.session["user_id"] = user_ids[0]
    if result is None:
        # show auction create page
        return templates.TemplateResponse(
            request=request,
            name="auction_start.html",
            context={"post_token": post_token},
        )
    elif type(result) is AuctionBidderView:
        # TODO: set user session cookie
        return templates.TemplateResponse(
            request=request,
            name="auction_bidder.html",
            context={"auction": result, "user_id": user_ids[0]},
        )
    elif type(result) is AuctionSellerView:
        # TODO: set user session cookie
        return templates.TemplateResponse(
            request=request,
            name="auction_seller.html",
            context={"auction": result},
        )

    return templates.TemplateResponse(
        request=request,
        name="auctions.html",
        context={"auctions": []},
    )


@auction_router.post("/start")
async def start_auction(
    request: Request,
    auction_data: Annotated[AuctionStartInput, Form()],
    seller_id: UserID = Depends(auth.get_user_id_from_session),
) -> RedirectResponse:
    result = await service.start_auction(
        auction_repo=auction_repo,
        divar_client=divar_client,
        seller_id=seller_id,
        auction_data=auction_data,
    )
    auction_repo._commit()
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&user_id={}&return_url={}".format(
        result.post_token, result.seller_id, "https://divar.ir"
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@auction_router.get("/info/{post_token}")
async def auction_detail(post_token: PostToken) -> Auction:
    result = await service.read_auction(
        auction_repo=auction_repo, post_token=post_token
    )
    return result


@auction_router.post("/place-bid")
async def place_bid(
    request: Request,
    bid_data: Annotated[PlaceBid, Form()],
    user_id: UserID = Depends(auth.get_user_id_from_session),
) -> Bid | None:
    # TODO: add csrf protection
    result = await service.place_bid(
        auction_repo=auction_repo, bid_data=bid_data, bidder_id=user_id
    )
    auction_repo._commit()
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&user_id={}&return_url={}".format(
        bid_data.post_token, result.bidder_id, "https://divar.ir"
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@auction_router.get("/{auction_id}")
async def read_auction(auction_id: AuctionID) -> Auction:
    auction = await auction_repo.read_acution_by_id(auction_id=auction_id)
    if auction is None:
        raise exception.AuctionNotFound()
    return auction
