"""Auction services"""

from model import AuctionStartInput, Auction, AdID, Bid, PlaceBid, UserID
from repo import AuctionRepo
from exception import (
    AuctionNotFound,
    AuctionAlreadyStarted,
    BidFromSellerNotAllowed,
    AdNotFound,
)
from divar import PostItemResponse, divar_client


async def auction_info() -> None:
    # get auction bids
    # select top 3
    # show auction widget intro page on Divar
    return


async def read_auction(auction_repo: AuctionRepo, ad_id: AdID) -> Auction:
    """view auction detail"""
    auction = await auction_repo.read_acution_by_ad_id(ad_id=ad_id)
    if auction is None:
        raise AuctionNotFound()
    # find, verify ad on Divar
    return auction


async def place_bid(
    auction_repo: AuctionRepo, bid_data: PlaceBid, bidder_id: UserID
) -> Bid:
    """place a bid on an auction"""
    try:
        auction = await read_auction(auction_repo=auction_repo, ad_id=bid_data.ad_id)
        # get ad info from divar
    except AuctionNotFound as e:
        raise e

    if auction.uid == bidder_id:
        raise BidFromSellerNotAllowed()

    bid = None
    last_bid = await auction_repo.find_bid(auction_id=auction.uid, bidder_id=bidder_id)
    if last_bid:
        bid = await auction_repo.change_bid_amount(bid=last_bid, amount=bid_data.amount)
    else:
        bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=bid_data.amount)
        await auction_repo.add_bid_to_auction(bid=bid, auction=auction)

    # redirect to Divar
    # send BID_PLACED event (send new bid in chat, etc)
    return bid


async def start_auction(
    auction_repo: AuctionRepo, seller_id: UserID, auction_data: AuctionStartInput
) -> Auction:
    """start a new auction"""
    auction_is_started = await auction_repo.read_acution_by_ad_id(
        ad_id=auction_data.ad_id
    )
    if auction_is_started:
        raise AuctionAlreadyStarted()

    ad = divar_client.finder.get_post(PostItemResponse(token=auction_data.ad_id))
    if ad is None:
        raise AdNotFound()
    # verify seller id on Divar

    auction = Auction(**auction_data.model_dump(), seller_id=seller_id, bids=[])
    await auction_repo.add_auction(auction=auction)
    # redirect to Divar
    return auction


async def edit_auction() -> None: ...


async def remove_auction() -> None: ...


if __name__ == "__main__":
    pass
