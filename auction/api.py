"""HTTP API for auction app"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic.networks import AnyHttpUrl

from auction import auth, divar, exception, service
from auction._types import PostToken, UserID
from auction.api_deps import get_repo
from auction.i18n import gettext as _
from auction.model import (
    AuctionBidderView,
    AuctionSellerView,
    AuctionStartInput,
    PlaceBid,
    SelectBid,
)
from auction.pages.template import templates
from auction.repo import AuctionRepo


auction_router = APIRouter(prefix="/auc")


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


@auction_router.get("/intro")
async def auction_intro(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    auction = await service.auction_intro(
        auction_repo=auction_repo,
        divar_client=divar_client,
        post_token=post_token,
    )

    return templates.TemplateResponse(
        request=request,
        name="auction_intro.html",
        context={"auction": auction, "return_url": return_url},
    )


@auction_router.get("/")
async def auctions(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    result = await service.auction_detail(
        auction_repo=auction_repo,
        divar_client=divar_client,
        user_id=user_id,
        post_token=post_token,
        return_url=return_url,
    )
    if type(result) is AuctionBidderView:
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
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    post = await divar_client.finder.find_post_from_user_posts(
        post_token=post_token, user_access_token=user_access_token
    )
    if post is None:
        # FIXME: show proper auction start not allowed error page
        raise exception.Forbidden()
    return templates.TemplateResponse(
        request=request,
        name="auction_start.html",
        context={"post": post},
    )


@auction_router.post("/start")
async def start_auction(
    request: Request,
    auction_data: Annotated[AuctionStartInput, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    result = await service.start_auction(
        auction_repo=auction_repo,
        divar_client=divar_client,
        seller_id=seller_id,
        auction_data=auction_data,
        user_access_token=user_access_token,
    )
    auction_repo._commit()
    redirect_url = f"https://divar.ir/v/{result.post_token}"
    return templates.TemplateResponse(
        request=request,
        name="redirect_with_message.html",
        context={
            "message": _("Auction started successfully!"),
            "redirect_url": redirect_url,
        },
    )


@auction_router.post("/place-bid")
async def place_bid(
    request: Request,
    bid_data: Annotated[PlaceBid, Form()],
    user_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    # TODO: add csrf protection
    await service.place_bid(
        auction_repo=auction_repo,
        divar_client=divar_client,
        bid_data=bid_data,
        bidder_id=user_id,
    )
    auction_repo._commit()
    redirect_url = f"https://divar.ir/v/{bid_data.post_token}"
    return templates.TemplateResponse(
        request=request,
        name="redirect_with_message.html",
        context={
            "message": _("Bid placed successfully!"),
            "redirect_url": redirect_url,
        },
    )


@auction_router.post("/select-bid")
async def select_bid(
    request: Request,
    select_bid_data: Annotated[SelectBid, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.user_get_posts_permission)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> RedirectResponse:
    # TODO: add csrf protection
    auction = await service.select_bid(
        auction_repo=auction_repo,
        divar_client=divar_client,
        seller_id=seller_id,
        bid_id=select_bid_data.bid_id,
        user_access_token=user_access_token,
    )
    redirect_url = str(
        request.url_for("auctions")
    ) + "?post_token={}&return_url={}".format(auction.post_token, "https://divar.ir")
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
