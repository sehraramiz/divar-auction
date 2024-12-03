"""HTTP API for auction app"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic.networks import AnyHttpUrl

from auction import auth, divar, exception, service
from auction._types import AuctionID, PostToken, UserID
from auction.api_deps import get_repo
from auction.config import config
from auction.model import (
    Auction,
    AuctionBidderView,
    AuctionSellerView,
    AuctionStartInput,
    PlaceBid,
    SelectBid,
)
from auction.repo import AuctionRepo, auction_repo


auction_router = APIRouter(prefix="/auc")
templates = Jinja2Templates(directory=config.templates_dir_path)


@auction_router.get("/home")
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@auction_router.get("/auth")
async def auth_management(
    redirect_url: Annotated[AnyHttpUrl, Depends(auth.redirect_oauth)],
) -> RedirectResponse:
    return RedirectResponse(str(redirect_url), status_code=status.HTTP_302_FOUND)


@auction_router.get("/")
async def auctions(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
) -> HTMLResponse:
    result = await service.auction_detail(
        auction_repo=auction_repo,
        divar_client=divar.divar_client,
        user_id=user_id,
        post_token=post_token,
        return_url=return_url,
    )
    if result is None:
        return templates.TemplateResponse(
            request=request,
            name="auction_intro.html",
            context={"post_token": post_token, "return_url": return_url},
        )
    elif type(result) is AuctionBidderView:
        return templates.TemplateResponse(
            request=request,
            name="auction_bidder.html",
            context={"auction": result, "user_id": user_id},
        )
    elif type(result) is AuctionSellerView:
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


@auction_router.get("/start")
async def start_auction_view(
    request: Request,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
    post_token: PostToken,
) -> HTMLResponse:
    is_post_owner = await divar.is_post_owner(
        post_token=post_token, user_access_token=user_access_token
    )
    if not is_post_owner:
        # FIXME: show proper auction start not allowed error page
        raise exception.Forbidden()
    return templates.TemplateResponse(
        request=request,
        name="auction_start.html",
        context={"post_token": post_token},
    )


@auction_router.post("/start")
async def start_auction(
    request: Request,
    auction_data: Annotated[AuctionStartInput, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
) -> RedirectResponse:
    result = await service.start_auction(
        auction_repo=auction_repo,
        divar_client=divar.divar_client,
        seller_id=seller_id,
        auction_data=auction_data,
        user_access_token=user_access_token,
    )
    auction_repo._commit()
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&return_url={}".format(
        result.post_token, "https://divar.ir"
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
    user_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
) -> RedirectResponse:
    # TODO: add csrf protection
    await service.place_bid(
        auction_repo=auction_repo, bid_data=bid_data, bidder_id=user_id
    )
    auction_repo._commit()
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&return_url={}".format(bid_data.post_token, "https://divar.ir")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@auction_router.post("/select-bid")
async def select_bid(
    request: Request,
    select_bid_data: Annotated[SelectBid, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
) -> RedirectResponse:
    # TODO: add csrf protection
    auction = await service.select_bid(
        auction_repo=auction_repo,
        seller_id=seller_id,
        bid_id=select_bid_data.bid_id,
        user_access_token=user_access_token,
    )
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&return_url={}".format(auction.post_token, "https://divar.ir")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@auction_router.get("/{auction_id}")
async def read_auction(auction_id: AuctionID) -> Auction:
    auction = await auction_repo.read_acution_by_id(auction_id=auction_id)
    if auction is None:
        raise exception.AuctionNotFound()
    return auction
