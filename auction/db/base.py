from uuid import uuid4

from sqlalchemy import BigInteger, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column
from sqlalchemy.schema import PrimaryKeyConstraint

from auction import _types, model


__all__ = ["Base", "Auction"]


class Base(DeclarativeBase, MappedAsDataclass):
    type_annotation_map = {
        _types.AuctionID: Uuid,
        _types.PostToken: String(20),
        _types.UserID: String(16),
        _types.Rial: BigInteger,
        _types.BidID: Uuid,
    }


class Auction(Base):
    __tablename__ = "auctions"
    __table_args__ = (PrimaryKeyConstraint("uid", name="auction_pk"),)

    post_token: Mapped[_types.PostToken]
    seller_id: Mapped[_types.UserID]
    selected_bid: Mapped[_types.BidID | None]
    starting_price: Mapped[_types.Rial] = mapped_column(default=0)
    post_title: Mapped[str] = mapped_column(String(100), default="")
    uid: Mapped[_types.AuctionID] = mapped_column(default_factory=uuid4)


class Bid(Base):
    __tablename__ = "bids"
    __table_args__ = (PrimaryKeyConstraint("uid", name="bid_pk"),)

    auction_id: Mapped[_types.AuctionID]
    bidder_id: Mapped[_types.UserID]
    amount: Mapped[_types.Rial]
    uid: Mapped[_types.BidID] = mapped_column(default_factory=uuid4)


Base.registry.map_imperatively(model.Auction, local_table=Auction.__table__)
Base.registry.map_imperatively(model.Bid, local_table=Bid.__table__)
