"""HTTP API for auction app"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic.networks import AnyHttpUrl

from auction import auth, divar, exception, service
from auction._types import PostToken, UserID
from auction.api_deps import get_repo, get_return_url
from auction.i18n import gettext as _
from auction.model import AuctionStartInput, PlaceBid, SelectBid
from auction.pages.template import templates
from auction.repo import AuctionRepo


auction_router = APIRouter(prefix="/auction")


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
    """
    Oauth2 provider (divar) redirects user to this path
    and we validate provided state and guide user back to their original path
    with their original query parameters
    """
    return RedirectResponse(str(redirect_url), status_code=status.HTTP_302_FOUND)


@auction_router.get("/intro")
async def auction_intro(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    """
    Intro page to provide information about the auction service
    and requested post auction (if existing) and give options to user
    to start an auction or participate in an already started auction.
    This is the first page we show every enduser (seller or bidder).
    """
    auction = await service.auction_intro(
        auction_repo=auction_repo,
        divar_client=divar_client,
        post_token=post_token,
    )
    return templates.TemplateResponse(
        request=request,
        name="auction_intro.html",
        context={
            "auction": auction,
            "post_token": post_token,
            "return_url": return_url,
        },
    )


@auction_router.get("/")
async def auctions(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> RedirectResponse:
    """
    Validate Auction and Post and redirect seller users to auction management
    and bidder users to bidding page
    """
    is_auction_seller = await service.is_auction_seller(
        auction_repo=auction_repo,
        divar_client=divar_client,
        user_id=user_id,
        post_token=post_token,
        return_url=return_url,
    )
    if is_auction_seller:
        redirect_url = (
            str(request.url_for("auction_management", post_token=post_token))
            + f"?return_url={return_url}"
        )
        return RedirectResponse(redirect_url)
    else:
        redirect_url = (
            str(request.url_for("auction_bidding"))
            + f"?post_token={post_token}&return_url={return_url}"
        )
        return RedirectResponse(redirect_url)


@auction_router.get("/bidding", tags=["Bidding"])
async def auction_bidding(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.authorize_user_and_set_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> Response:
    auction = await service.auction_bidding(
        auction_repo=auction_repo,
        divar_client=divar_client,
        user_id=user_id,
        post_token=post_token,
        return_url=return_url,
    )
    return templates.TemplateResponse(
        request=request,
        name="auction_bidder.html",
        context={"auction": auction},
    )


@auction_router.post("/bidding/", tags=["Bidding"])
async def place_bid(
    request: Request,
    bid_data: Annotated[PlaceBid, Form()],
    user_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
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


@auction_router.delete("/bidding/{post_token}", tags=["Bidding"])
async def remove_bid(
    request: Request,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
) -> HTMLResponse:
    await service.remove_bid(
        auction_repo=auction_repo,
        bidder_id=user_id,
        post_token=post_token,
    )
    auction_repo._commit()
    redirect_url = f"https://divar.ir/v/{post_token}"
    return templates.TemplateResponse(
        request=request,
        name="redirect_with_message.html",
        context={
            "message": _("Bid removed successfully!"),
            "redirect_url": redirect_url,
        },
    )


@auction_router.get("/management/{post_token}", tags=["Auction Management"])
async def auction_management(
    request: Request,
    return_url: divar.DivarReturnUrl,
    post_token: PostToken,
    user_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.auction_management_access)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
) -> HTMLResponse:
    auction = await service.auction_management(
        auction_repo=auction_repo, user_id=user_id, post_token=post_token
    )
    return templates.TemplateResponse(
        request=request,
        name="auction_seller.html",
        context={"auction": auction, "return_url": return_url},
    )


@auction_router.get("/management/start/{post_token}", tags=["Auction Management"])
async def start_auction_view(
    request: Request,
    post_token: PostToken,
    return_url: Annotated[divar.DivarReturnUrl, Depends(get_return_url)],
    user_access_token: Annotated[UserID, Depends(auth.auction_management_access)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    """
    Show auction start page for seller and prevent others from
    starting an auction on someone else's post
    """
    post = await divar_client.finder.find_post_from_user_posts(
        post_token=post_token, user_access_token=user_access_token
    )
    if post is None:
        # FIXME: show proper auction start not allowed error page
        raise exception.Forbidden()
    return templates.TemplateResponse(
        request=request,
        name="auction_start.html",
        context={"post": post, "return_url": return_url},
    )


@auction_router.post("/management/start/{post_token}", tags=["Auction Management"])
async def start_auction(
    request: Request,
    post_token: PostToken,
    auction_data: Annotated[AuctionStartInput, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.auction_management_access)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> HTMLResponse:
    """
    Start a new auction by seller user and create auction widget for them
    user must be the post owner
    """
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


@auction_router.post("/management/select-bid/{post_token}", tags=["Auction Management"])
async def select_bid(
    request: Request,
    post_token: PostToken,
    select_bid_data: Annotated[SelectBid, Form()],
    seller_id: Annotated[UserID, Depends(auth.get_user_id_from_session)],
    user_access_token: Annotated[UserID, Depends(auth.auction_management_access)],
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    divar_client: Annotated[divar.DivarClient, Depends(divar.get_divar_client)],
) -> RedirectResponse:
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
