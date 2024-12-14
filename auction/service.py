"""Auction services"""

from auction import divar, exception
from auction._types import BidID, Rial
from auction.config import config
from auction.i18n import gettext as _
from auction.model import (
    Auction,
    AuctionBidderView,
    AuctionStartInput,
    Bid,
    PlaceBid,
    PostToken,
    UserID,
)
from auction.repo import AuctionRepo


TOP_BIDS_COUNT = 3


async def auction_intro(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    post_token: PostToken,
) -> Auction | None:
    try:
        await divar_client.finder.validate_post(post_token=post_token)
    except exception.PostNotFound as e:
        raise exception.AuctionNotFound() from e
    return await auction_repo.read_auction_by_post_token(post_token=post_token)


async def is_auction_seller(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    user_id: UserID,
    post_token: PostToken,
    return_url: divar.DivarReturnUrl,
) -> bool:
    await divar_client.finder.validate_post(post_token=post_token)

    auction = await auction_repo.read_auction_by_post_token(post_token=post_token)
    if auction is None:
        raise exception.AuctionNotFound()

    return auction.seller_id == user_id


async def auction_bidding(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    user_id: UserID,
    post_token: PostToken,
    return_url: divar.DivarReturnUrl,
) -> AuctionBidderView:
    auction = await auction_repo.read_auction_by_post_token(post_token=post_token)
    if auction is None:
        raise exception.AuctionNotFound()
    if auction.seller_id == user_id:
        raise exception.BidFromSellerNotAllowed()

    last_bid = await auction_repo.find_bid(auction_id=auction.uid, bidder_id=user_id)
    last_bid_amount = last_bid.amount if last_bid else Rial(0)
    top_bids = sorted(auction.bids)[::-1][:TOP_BIDS_COUNT]
    return AuctionBidderView(
        post_token=post_token,
        post_title=auction.post_title,
        starting_price=auction.starting_price,
        bids_count=auction.bids_count,
        uid=auction.uid,
        last_bid=last_bid_amount,
        return_url=return_url,
        top_bids=top_bids,
    )


async def auction_management(
    auction_repo: AuctionRepo,
    user_id: UserID,
    post_token: PostToken,
) -> Auction:
    auction = await auction_repo.read_auction_by_post_token(post_token=post_token)
    if auction is None:
        raise exception.AuctionNotFound()
    if auction.seller_id != user_id:
        raise exception.Forbidden()
    return auction


async def place_bid(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    bid_data: PlaceBid,
    bidder_id: UserID,
) -> Bid:
    """place a bid on an auction"""
    auction = await auction_repo.read_auction_by_post_token(
        post_token=bid_data.post_token
    )
    if auction is None:
        raise exception.AuctionNotFound()

    await divar_client.finder.validate_post(post_token=bid_data.post_token)

    if auction.seller_id == bidder_id:
        raise exception.BidFromSellerNotAllowed()

    if bid_data.amount < auction.starting_price:
        raise exception.BidTooLow()

    bid = None
    last_bid = await auction_repo.find_bid(auction_id=auction.uid, bidder_id=bidder_id)
    if last_bid:
        bid = await auction_repo.change_bid_amount(bid=last_bid, amount=bid_data.amount)
        await auction_repo.remove_selected_bid(last_bid.uid)
    else:
        bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=bid_data.amount)
        await auction_repo.add_bid(bid=bid)

    # send BID_PLACED event (send new bid in chat, etc)
    return bid


async def create_auction_addon(
    divar_client: divar.DivarClient,
    user_access_token: str,
    post_token: PostToken,
    auction: Auction,
) -> None:
    from kenar import CreatePostAddonRequest
    from kenar.widgets import DescriptionRow, TitleRow, WideButtonBar  # type: ignore

    # access token must have USER_ADDON_CREATE scope access
    return_url = f"https://divar.ir/v/{post_token}"
    auction_button_link = (
        str(config.project_url).strip("/")
        + "/intro"
        + f"?post_token={post_token}&return_url={return_url}"
    )
    button = WideButtonBar.Button(title=_("Enter Auction"), link=auction_button_link)
    description = _(
        "This post has an ongoing auction starting"
        " at {starting_price} you can bid on"
    ).format(starting_price=auction.starting_price)

    auction_widgets = [
        TitleRow(text=_("Auction Available")),
        DescriptionRow(text=description),
        WideButtonBar(button=button),
    ]
    create_addon_data = CreatePostAddonRequest(
        token=post_token, widgets=auction_widgets
    )
    divar_client.addon.create_post_addon(
        access_token=user_access_token, data=create_addon_data
    )


async def start_auction(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    seller_id: UserID,
    auction_data: AuctionStartInput,
    user_access_token: str,
) -> Auction:
    """start a new auction"""
    auction_is_started = await auction_repo.read_auction_by_post_token(
        post_token=auction_data.post_token
    )
    if auction_is_started:
        raise exception.AuctionAlreadyStarted()

    await divar_client.finder.validate_post(post_token=auction_data.post_token)
    post = await divar_client.finder.find_post_from_user_posts(
        post_token=auction_data.post_token, user_access_token=user_access_token
    )
    if post is None:
        raise exception.Forbidden()

    auction = Auction(
        **auction_data.model_dump(),
        seller_id=seller_id,
        bids=[],
        post_title=post.title,
    )
    await auction_repo.add_auction(auction=auction)

    await create_auction_addon(
        divar_client=divar_client,
        user_access_token=user_access_token,
        post_token=auction_data.post_token,
        auction=auction,
    )
    return auction


async def select_bid(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    seller_id: UserID,
    bid_id: BidID,
    user_access_token: str,
) -> Auction:
    bid = await auction_repo.read_bid_by_id(bid_id=bid_id)
    if bid is None:
        raise exception.BidNotFound()

    auction = await auction_repo.read_auction_by_id(auction_id=bid.auction_id)
    if auction is None:
        raise exception.AuctionNotFound()

    is_post_owner = await divar_client.finder.find_post_from_user_posts(
        post_token=auction.post_token, user_access_token=user_access_token
    )
    if not is_post_owner:
        raise exception.Forbidden()

    await auction_repo.select_bid(auction, bid_id=bid_id)
    # send BID_SELECTED event
    return auction
