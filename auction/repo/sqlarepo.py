from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auction import db
from auction._types import AuctionID, BidID, PostToken, Rial, UserID
from auction.model import Auction, Bid
from auction.repo.base import AuctionRepo


class SQLARepo(AuctionRepo):
    """repository for sqlalchemy"""

    access_tokens: dict[UserID, list[dict]]
    _instance = None

    def __init__(self, session: async_sessionmaker[AsyncSession]) -> None:
        self.session = session

    def __new__(cls, *args, **kwargs) -> "SQLARepo":
        if cls._instance is None:
            cls.access_tokens = {}
            cls._instance = super().__new__(cls)
        return cls._instance

    async def add_auction(self, auction: Auction) -> Auction:
        async with self.session() as sess:
            sess.add(auction)
            await sess.commit()
            await sess.refresh(auction)
            sess.expunge(auction)
        return auction

    async def remove_auction(self, auction_id: AuctionID) -> None:
        async with self.session() as sess:
            query = delete(Auction).where(db.base.Auction.uid == auction_id)
            await sess.execute(query)
            await sess.commit()

    async def set_bidders_count(self, auction: Auction) -> Auction:
        count = 0
        async with self.session() as sess:
            query = select(func.count(db.base.Bid.uid)).where(
                db.base.Bid.auction_id == auction.uid,
            )
            res = await sess.execute(query)
            count = res.scalar() or 0
        auction.bids_count = count
        return auction

    async def set_bids_on_auction(self, auction: Auction) -> Auction:
        bids: list[Bid] = []
        async with self.session() as sess:
            query = select(Bid).where(
                db.base.Bid.auction_id == auction.uid,
            )
            res = await sess.execute(query)
            bids_res = res.scalars()
            if bids_res:
                sess.expunge_all()
                bids = list(bids_res)
        auction.bids = bids
        return auction

    async def add_bid(self, bid: Bid) -> Bid:
        async with self.session() as sess:
            sess.add(bid)
            await sess.commit()
            await sess.refresh(bid)
            sess.expunge(bid)
        return bid

    async def find_bid(self, auction_id: AuctionID, bidder_id: UserID) -> Bid | None:
        bid = None
        async with self.session() as sess:
            query = select(Bid).where(
                db.base.Bid.auction_id == auction_id,
                db.base.Bid.bidder_id == bidder_id,
            )
            res = await sess.execute(query)
            bid = res.scalar()
            if bid:
                sess.expunge(bid)
        return bid

    async def change_bid_amount(self, bid: Bid, amount: Rial) -> Bid:
        async with self.session() as sess:
            bid.amount = amount
            sess.add(bid)
            await sess.commit()
            await sess.refresh(bid)
            sess.expunge(bid)
            return bid

    async def remove_bid(self, bid_id: BidID) -> None:
        async with self.session() as sess:
            query = delete(Bid).where(db.base.Bid.uid == bid_id)
            await sess.execute(query)
            await sess.commit()

    async def remove_bids_by_auction_id(self, auction_id: AuctionID) -> None:
        async with self.session() as sess:
            query = delete(Bid).where(db.base.Bid.auction_id == auction_id)
            await sess.execute(query)
            await sess.commit()

    async def remove_selected_bid(self, bid_id: BidID) -> None:
        async with self.session() as sess:
            query = (
                update(db.base.Auction)
                .where(db.base.Auction.selected_bid == bid_id)
                .values({db.base.Auction.selected_bid: None})
            )
            await sess.execute(query)
            await sess.commit()

    async def select_bid(self, auction: Auction, bid_id: BidID) -> Auction:
        async with self.session() as sess:
            auction.selected_bid = bid_id
            sess.add(auction)
            await sess.commit()
            await sess.refresh(auction)
            sess.expunge(auction)
            return auction

    async def read_auction_by_post_token(self, post_token: PostToken) -> Auction | None:
        auction = None
        async with self.session() as sess:
            query = select(Auction).where(db.base.Auction.post_token == post_token)
            res = await sess.execute(query)
            auction = res.scalar()
            if auction:
                sess.expunge(auction)
                await self.set_bids_on_auction(auction)
                await self.set_bidders_count(auction)
        return auction

    async def read_auction_by_id(self, auction_id: AuctionID) -> Auction | None:
        auction = None
        async with self.session() as sess:
            query = select(Auction).where(db.base.Auction.uid == auction_id)
            res = await sess.execute(query)
            auction = res.scalar()
            if auction:
                sess.expunge(auction)
        return auction

    async def read_bid_by_id(self, bid_id: BidID) -> Bid | None:
        bid = None
        async with self.session() as sess:
            query = select(Bid).where(db.base.Bid.uid == bid_id)
            res = await sess.execute(query)
            bid = res.scalar()
            if bid:
                sess.expunge(bid)
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
