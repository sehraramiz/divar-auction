from uuid import uuid4

from pydantic import BaseModel, Field

from auction._types import AuctionID, BidID, PostToken, Rial, UserID
from auction.divar import DivarReturnUrl


class Bid(BaseModel):
    bidder_id: UserID
    auction_id: AuctionID
    amount: Rial
    uid: BidID = Field(default_factory=uuid4)  # type: ignore

    def __lt__(self, other):
        if not isinstance(other, Bid):
            return NotImplemented
        return self.amount < other.amount


class Auction(BaseModel):
    post_token: PostToken
    post_title: str | None = None
    seller_id: UserID
    starting_price: Rial
    bids: list[Bid]
    uid: AuctionID = Field(default_factory=uuid4)  # type: ignore
    bids_count: int = 0
    selected_bid: BidID | None = None

    @property
    def top_bids(self) -> list[Bid]:
        return sorted(self.bids)[::-1][:3]

    @property
    def min_raise_amount(self) -> Rial:
        raise_floor = Rial(500000)
        raise_min = int(self.starting_price * 0.05)
        return Rial(max(raise_floor, raise_min))


class AuctionSellerView(Auction): ...


class AuctionBidderView(BaseModel):
    post_token: PostToken
    post_title: str | None = None
    starting_price: Rial
    bids_count: int = 0
    uid: AuctionID
    last_bid: Rial = Rial(0)
    return_url: DivarReturnUrl
    top_bids: list[Bid] = Field(default_factory=list)
    min_raise_amount: Rial


class AuctionStartInput(BaseModel):
    post_token: PostToken
    starting_price: Rial


class PlaceBid(BaseModel):
    post_token: PostToken
    auction_id: AuctionID
    amount: Rial


class RemoveBid(BaseModel):
    post_token: PostToken
    auction_id: AuctionID


class SelectBid(BaseModel):
    bid_id: BidID
