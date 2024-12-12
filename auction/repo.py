import json

from pathlib import Path

from pydantic import TypeAdapter

from auction._types import AuctionID, BidID, PostToken, Rial, UserID
from auction.model import Auction, Bid


class AuctionRepo:
    auctions: list[Auction]
    bids: list[Bid]
    access_tokens: dict[UserID, list[dict]]
    db_file_name: str = "db.json"

    def __init__(self, db_file_name: str = "db.json") -> None:
        self.db_file_name = db_file_name
        self._load_db_file()

    def _load_db_file(self) -> None:
        db_path = Path(self.db_file_name)
        if db_path.exists():
            with open(db_path, "r") as db_file:
                db = json.load(db_file)
                auctions_adapter = TypeAdapter(list[Auction])
                self.auctions = auctions_adapter.validate_python(db["auctions"])
                bids_adapter = TypeAdapter(list[Bid])
                self.bids = bids_adapter.validate_python(db["bids"])
                self.access_tokens = {}
        else:
            self.auctions = []
            self.bids = []
            self.access_tokens = {}

    def _commit(self) -> None:
        db_path = Path(self.db_file_name)
        with open(db_path, "w") as db_file:
            auctions_adapter = TypeAdapter(list[Auction])
            auctions = auctions_adapter.dump_python(self.auctions, mode="json")
            bids_adapter = TypeAdapter(list[Bid])
            bids = bids_adapter.dump_python(self.bids, mode="json")
            db_data = {"auctions": auctions, "bids": bids}
            db_file.write(json.dumps(db_data))

    async def add_auction(self, auction: Auction) -> Auction:
        self.auctions.append(auction)
        self._commit()
        return auction

    async def set_bidders_count(self, auction: Auction) -> Auction:
        auction.bids_count = sum(
            [1 for bid in self.bids if bid.auction_id == auction.uid]
        )
        return auction

    async def set_bids_on_auction(self, auction: Auction) -> Auction:
        auction.bids = [bid for bid in self.bids if bid.auction_id == auction.uid]
        return auction

    async def add_bid(self, bid: Bid) -> Bid:
        self.bids.append(bid)
        self._commit()
        return bid

    async def find_bid(self, auction_id: AuctionID, bidder_id: UserID) -> Bid | None:
        bid = next(
            (
                bid
                for bid in self.bids
                if (bid.bidder_id == bidder_id and bid.auction_id == auction_id)
            ),
            None,
        )
        if not bid:
            return None
        return bid

    async def change_bid_amount(self, bid: Bid, amount: Rial) -> Bid:
        bid.amount = amount
        return bid

    async def select_bid(self, auction: Auction, bid_id: BidID) -> Auction:
        auction.selected_bid = bid_id
        self._commit()
        return auction

    async def read_auction_by_post_token(self, post_token: PostToken) -> Auction | None:
        auction = next(
            (auction for auction in self.auctions if auction.post_token == post_token),
            None,
        )
        if auction:
            await self.set_bidders_count(auction)
            await self.set_bids_on_auction(auction)
        return auction

    async def read_auction_by_id(self, auction_id: AuctionID) -> Auction | None:
        auction = next(
            (auction for auction in self.auctions if auction.uid == auction_id), None
        )
        if auction:
            await self.set_bidders_count(auction)
            await self.set_bids_on_auction(auction)
        return auction

    async def read_bid_by_id(self, bid_id: BidID) -> Bid | None:
        bid = next((bid for bid in self.bids if bid.uid == bid_id), None)
        return bid

    async def add_user_access_token(
        self, user_id: UserID, access_token_data: dict
    ) -> None:
        db_data: list[dict] = self.access_tokens.get(user_id, [])
        if db_data:
            db_data.append(access_token_data)
            return
        self.access_tokens[user_id] = [access_token_data]

    async def get_user_access_token_by_scope(
        self, user_id: UserID, scope: str
    ) -> dict | None:
        user_access_tokens = self.access_tokens.get(user_id)
        if user_access_tokens is None:
            return None
        return next(
            (data for data in user_access_tokens if scope in data["scope"]), None
        )

    async def get_user_access_token_by_scopes(
        self, user_id: UserID, scopes: list[str]
    ) -> dict | None:
        user_access_tokens = self.access_tokens.get(user_id)
        if user_access_tokens is None:
            return None
        for data in user_access_tokens:
            found_all = True
            for scope in scopes:
                if scope not in data["scope"]:
                    found_all = False
                    break
            if found_all:
                return data
        return None


auction_repo = AuctionRepo()
