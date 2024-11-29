from uuid import uuid4, UUID
from typing import cast

from pydantic import BaseModel

from _types import UserID, AuctionID, Rial, PostToken


class Bid(BaseModel):
    bidder_id: UserID
    auction_id: AuctionID
    amount: Rial
    uid: UUID = uuid4()


class Auction(BaseModel):
    post_token: PostToken
    seller_id: UserID
    starting_price: Rial
    bids: list[Bid]
    uid: AuctionID = cast(AuctionID, uuid4())

    @property
    def bids_count(self) -> int:
        return len(self.bids)


class AuctionStartInput(BaseModel):
    post_token: PostToken
    starting_price: Rial


class PlaceBid(BaseModel):
    post_token: PostToken
    auction_id: AuctionID
    amount: Rial
