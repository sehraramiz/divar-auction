"""Auction services"""

from model import (
    AuctionStartInput,
    Auction,
    PostToken,
    Bid,
    PlaceBid,
    UserID,
    AuctionBidderView,
    AuctionSellerView,
)
from repo import AuctionRepo
from exception import (
    AuctionNotFound,
    AuctionAlreadyStarted,
    BidFromSellerNotAllowed,
    PostNotFound,
)
from divar import DivarClient, validate_post


async def auction_info() -> None:
    # get auction bids
    # select top 3
    # show auction widget intro page on Divar
    return


async def auction_detail(
    auction_repo: AuctionRepo,
    divar_client: DivarClient,
    user_ids: list[UserID],
    post_token: PostToken,
) -> Auction | AuctionBidderView | AuctionSellerView | None:
    """view auction detail"""
    auction = await auction_repo.read_acution_by_post_token(post_token=post_token)
    if auction is None:
        try:
            post = validate_post(post_token=post_token)
            print(post)
            # show auction create page if post is legit
            return None
        except PostNotFound as e:
            raise AuctionNotFound() from e

    if auction.seller_id in user_ids:
        return AuctionSellerView.model_validate(auction, from_attributes=True)
    else:
        return AuctionBidderView(
            post_token=post_token,
            starting_price=auction.starting_price,
            bids_count=auction.bids_count,
        )
    return auction


async def read_auction(auction_repo: AuctionRepo, post_token: PostToken) -> Auction:
    """view auction detail"""
    auction = await auction_repo.read_acution_by_post_token(post_token=post_token)
    if auction is None:
        raise AuctionNotFound()
    return auction


async def place_bid(
    auction_repo: AuctionRepo, bid_data: PlaceBid, bidder_id: UserID
) -> Bid:
    """place a bid on an auction"""
    try:
        auction = await read_auction(
            auction_repo=auction_repo, post_token=bid_data.post_token
        )
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
    auction_repo: AuctionRepo,
    divar_client: DivarClient,
    seller_id: UserID,
    auction_data: AuctionStartInput,
) -> Auction:
    """start a new auction"""
    auction_is_started = await auction_repo.read_acution_by_post_token(
        post_token=auction_data.post_token
    )
    if auction_is_started:
        raise AuctionAlreadyStarted()

    post = await validate_post(post_token=auction_data.post_token)
    print(post)
    # verify seller id on Divar

    auction = Auction(**auction_data.model_dump(), seller_id=seller_id, bids=[])
    await auction_repo.add_auction(auction=auction)
    # redirect to Divar
    return auction


async def edit_auction() -> None: ...


async def remove_auction() -> None: ...


if __name__ == "__main__":
    pass
