"""Auction services"""

import logging

from auction import divar, exception
from auction._types import Rial
from auction.model import (
    Auction,
    AuctionBidderView,
    AuctionSellerView,
    AuctionStartInput,
    Bid,
    PlaceBid,
    PostToken,
    UserID,
)
from auction.repo import AuctionRepo


logger = logging.getLogger(__name__)

TOP_BIDS_COUNT = 3


async def auction_detail(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    user_id: UserID,
    post_token: PostToken,
    return_url: divar.DivarReturnUrl,
) -> Auction | AuctionBidderView | AuctionSellerView | None:
    """view auction detail"""
    post = await divar.validate_post(post_token=post_token)
    logger.info(f"post is valid\n{post}")

    auction = await auction_repo.read_acution_by_post_token(post_token=post_token)
    if auction is None:
        try:
            # show auction create page if post is legit
            return None
        except exception.PostNotFound as e:
            raise exception.AuctionNotFound() from e

    if auction.seller_id == user_id:
        return AuctionSellerView.model_validate(auction, from_attributes=True)
    else:
        last_bid = await auction_repo.find_bid(
            auction_id=auction.uid, bidder_id=user_id
        )
        last_bid_amount = last_bid.amount if last_bid else Rial(0)
        top_bids = sorted(auction.bids)[::-1][:TOP_BIDS_COUNT]
        return AuctionBidderView(
            post_token=post_token,
            starting_price=auction.starting_price,
            bids_count=auction.bids_count,
            uid=auction.uid,
            last_bid=last_bid_amount,
            return_url=return_url,
            top_bids=top_bids,
        )
    return auction


async def read_auction(auction_repo: AuctionRepo, post_token: PostToken) -> Auction:
    """view auction detail"""
    auction = await auction_repo.read_acution_by_post_token(post_token=post_token)
    if auction is None:
        raise exception.AuctionNotFound()
    return auction


async def place_bid(
    auction_repo: AuctionRepo, bid_data: PlaceBid, bidder_id: UserID
) -> Bid:
    """place a bid on an auction"""
    try:
        auction = await read_auction(
            auction_repo=auction_repo, post_token=bid_data.post_token
        )
        await divar.validate_post(post_token=bid_data.post_token)
    except (exception.AuctionNotFound, exception.PostNotFound) as e:
        raise e

    if auction.seller_id == bidder_id:
        raise exception.BidFromSellerNotAllowed()

    if bid_data.amount < auction.starting_price:
        raise exception.BidTooLow()

    bid = None
    last_bid = await auction_repo.find_bid(auction_id=auction.uid, bidder_id=bidder_id)
    if last_bid:
        bid = await auction_repo.change_bid_amount(bid=last_bid, amount=bid_data.amount)
    else:
        bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=bid_data.amount)
        await auction_repo.add_bid(bid=bid)

    # redirect to Divar
    # send BID_PLACED event (send new bid in chat, etc)
    return bid


async def select_bid(auction_repo: AuctionRepo, seller_id: UserID, bid_id: BidID) -> None:
    # check bid exists
    bid = await auction_repo.read_bid_by_id(bid_id=bid_id)
    if bid is None:
        raise exception.BidNotFound()
    # check sellr is auction owner
    # select bid
    return None


async def start_auction(
    auction_repo: AuctionRepo,
    divar_client: divar.DivarClient,
    seller_id: UserID,
    auction_data: AuctionStartInput,
    user_access_token: str,
) -> Auction:
    """start a new auction"""
    auction_is_started = await auction_repo.read_acution_by_post_token(
        post_token=auction_data.post_token
    )
    if auction_is_started:
        raise exception.AuctionAlreadyStarted()

    post = await divar.validate_post(post_token=auction_data.post_token)
    # verify seller id on Divar
    is_post_owner = await divar.is_post_owner(
        post_token=post.token, user_access_token=user_access_token
    )
    if not is_post_owner:
        raise exception.Forbidden()

    auction = Auction(**auction_data.model_dump(), seller_id=seller_id, bids=[])
    await auction_repo.add_auction(auction=auction)
    # redirect to Divar
    return auction


async def edit_auction() -> None: ...


async def remove_auction() -> None: ...


if __name__ == "__main__":
    pass
