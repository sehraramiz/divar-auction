import pytest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auction._types import PostToken, Rial, UserID
from auction.divar import mock_data as divar_mock_data
from auction.model import Auction, Bid
from auction.repo import SQLARepo


@pytest.mark.asyncio
async def test_add_auction(sqla_session: async_sessionmaker[AsyncSession]) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)
    created_auction = await repo.read_auction_by_id(auction_id=auction.uid)
    assert created_auction is not None
    assert created_auction.post_token == post_token


@pytest.mark.asyncio
async def test_remove_auction(sqla_session: async_sessionmaker[AsyncSession]) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)
    await repo.remove_auction(auction_id=auction.uid)
    created_auction = await repo.read_auction_by_id(auction_id=auction.uid)
    assert created_auction is None


@pytest.mark.asyncio
async def test_read_auction_by_post_token(
    sqla_session: async_sessionmaker[AsyncSession],
) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)
    found_auction = await repo.read_auction_by_post_token(post_token=auction.post_token)
    assert found_auction is not None
    assert found_auction.uid == auction.uid


@pytest.mark.asyncio
async def test_create_bid(sqla_session: async_sessionmaker[AsyncSession]) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)

    created_bid = await repo.read_bid_by_id(bid_id=bid.uid)
    assert created_bid is not None


@pytest.mark.asyncio
async def test_remove_bid(sqla_session: async_sessionmaker[AsyncSession]) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)
    await repo.remove_bid(bid_id=bid.uid)

    created_bid = await repo.read_bid_by_id(bid_id=bid.uid)
    assert created_bid is None


@pytest.mark.asyncio
async def test_remove_bids_by_auction_id(
    sqla_session: async_sessionmaker[AsyncSession],
) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)
    await repo.remove_bids_by_auction_id(auction_id=auction.uid)

    created_bid = await repo.read_bid_by_id(bid_id=bid.uid)
    assert created_bid is None


@pytest.mark.asyncio
async def test_select_bid(sqla_session: async_sessionmaker[AsyncSession]) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)
    await repo.select_bid(auction=auction, bid_id=bid.uid)

    updated_auction = await repo.read_auction_by_id(auction_id=auction.uid)
    assert updated_auction is not None
    assert updated_auction.selected_bid == bid.uid


@pytest.mark.asyncio
async def test_remove_select_bid(
    sqla_session: async_sessionmaker[AsyncSession],
) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)
    await repo.select_bid(auction=auction, bid_id=bid.uid)
    await repo.remove_selected_bid(bid_id=bid.uid)

    updated_auction = await repo.read_auction_by_id(auction_id=auction.uid)
    assert updated_auction is not None
    assert updated_auction.selected_bid is None


@pytest.mark.asyncio
async def test_change_bid_amount(
    sqla_session: async_sessionmaker[AsyncSession],
) -> None:
    repo = SQLARepo(session=sqla_session)

    post_token = PostToken("A")
    seller_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    new_bid_amount = Rial(15000)
    auction = Auction(
        post_token=post_token,
        post_title="title",
        seller_id=seller_id,
        starting_price=Rial(1000),
    )
    await repo.add_auction(auction)

    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000))
    await repo.add_bid(bid)
    await repo.change_bid_amount(bid=bid, amount=new_bid_amount)

    updated_bid = await repo.read_bid_by_id(bid_id=bid.uid)
    assert updated_bid is not None
    assert updated_bid.amount == new_bid_amount
