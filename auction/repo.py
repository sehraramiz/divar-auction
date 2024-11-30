import json
from pathlib import Path

from pydantic import TypeAdapter

from model import Auction, Bid
from _types import PostToken, AuctionID, UserID, Rial


class AuctionRepo:
    auctions: list[Auction]
    bids: list[Bid]
    sessions: dict[str, dict]  # TODO: create schema with predefined data types

    def __init__(self) -> None:
        self._load_db_file()

    def _load_db_file(self) -> None:
        db_path = Path("./db.json")
        if db_path.exists():
            with open(db_path, "r") as db_file:
                db = json.load(db_file)
                auctions_adapter = TypeAdapter(list[Auction])
                self.auctions = auctions_adapter.validate_python(db["auctions"])
                bids_adapter = TypeAdapter(list[Bid])
                self.bids = bids_adapter.validate_python(db["bids"])
                self.sessions = db["sessions"]
        else:
            self.auctions = []

    def _commit(self) -> None:
        db_path = Path("./db.json")
        with open(db_path, "w") as db_file:
            auctions_adapter = TypeAdapter(list[Auction])
            auctions = auctions_adapter.dump_python(self.auctions, mode="json")
            bids_adapter = TypeAdapter(list[Bid])
            bids = bids_adapter.dump_python(self.bids, mode="json")
            db_data = {"auctions": auctions, "bids": bids, "sessions": self.sessions}
            db_file.write(json.dumps(db_data))

    async def add_auction(self, auction: Auction) -> Auction:
        self.auctions.append(auction)
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

    async def read_acution_by_post_token(self, post_token: PostToken) -> Auction | None:
        auction = next(
            (auction for auction in self.auctions if auction.post_token == post_token),
            None,
        )
        if auction:
            await self.set_bidders_count(auction)
            await self.set_bids_on_auction(auction)
        return auction

    async def read_acution_by_id(self, auction_id: AuctionID) -> Auction | None:
        auction = next(
            (auction for auction in self.auctions if auction.uid == auction_id), None
        )
        if auction:
            await self.set_bidders_count(auction)
            await self.set_bids_on_auction(auction)
        return auction

    async def save_session_data(self, state: str, data: dict) -> None:
        self.sessions[state] = data
        self._commit()

    async def get_session_data(self, state: str) -> dict:
        return self.sessions.get(state, {})


auction_repo = AuctionRepo()
