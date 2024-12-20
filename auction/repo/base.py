from abc import ABC, abstractmethod

from auction._types import AuctionID, BidID, PostToken, Rial, UserID
from auction.model import Auction, Bid


class AuctionRepo(ABC):
    @abstractmethod
    async def add_auction(self, auction: Auction) -> Auction: ...

    @abstractmethod
    async def remove_auction(self, auction_id: AuctionID) -> None: ...

    @abstractmethod
    async def set_bidders_count(self, auction: Auction) -> Auction: ...

    @abstractmethod
    async def set_bids_on_auction(self, auction: Auction) -> Auction: ...

    @abstractmethod
    async def add_bid(self, bid: Bid) -> Bid: ...

    @abstractmethod
    async def find_bid(
        self, auction_id: AuctionID, bidder_id: UserID
    ) -> Bid | None: ...

    @abstractmethod
    async def change_bid_amount(self, bid: Bid, amount: Rial) -> Bid: ...

    @abstractmethod
    async def remove_bid(self, bid_id: BidID) -> None: ...

    @abstractmethod
    async def remove_bids_by_auction_id(self, auction_id: AuctionID) -> None: ...

    @abstractmethod
    async def remove_selected_bid(self, bid_id: BidID) -> None: ...

    @abstractmethod
    async def select_bid(self, auction: Auction, bid_id: BidID) -> Auction: ...

    @abstractmethod
    async def read_auction_by_post_token(
        self, post_token: PostToken
    ) -> Auction | None: ...

    @abstractmethod
    async def read_auction_by_id(self, auction_id: AuctionID) -> Auction | None: ...

    @abstractmethod
    async def read_bid_by_id(self, bid_id: BidID) -> Bid | None: ...

    @abstractmethod
    async def add_user_access_token(
        self, user_id: UserID, access_token_data: dict
    ) -> None: ...

    @abstractmethod
    async def get_user_access_token_by_scope(
        self, user_id: UserID, scope: str
    ) -> dict | None: ...

    @abstractmethod
    async def get_user_access_token_by_scopes(
        self, user_id: UserID, scopes: list[str]
    ) -> dict | None: ...
