from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from auction._types import AuctionID, PostToken, Rial, UserID
from auction.divar import mock_data as divar_mock_data
from auction.model import Auction, Bid, PlaceBid
from auction.repo import AuctionRepo


async def start_auction(auc_repo: AuctionRepo) -> Auction:
    auction_id = AuctionID(uuid4())
    user_id = UserID(divar_mock_data.SELLER_PHONE_NUMBER)
    auction = Auction(
        uid=auction_id,
        post_token=PostToken("A"),
        seller_id=user_id,
        starting_price=Rial(1000),
        bids=[],
        title="Test Post",
    )
    await auc_repo.add_auction(auction)
    return auction


async def start_auction_with_bids(auc_repo: AuctionRepo) -> None:
    auction = await start_auction(auc_repo)
    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bids = [
        Bid(bidder_id=UserID("2"), auction_id=auction.uid, amount=Rial(11000)),
        Bid(bidder_id=UserID("3"), auction_id=auction.uid, amount=Rial(12000)),
        Bid(bidder_id=UserID("4"), auction_id=auction.uid, amount=Rial(13000)),
        Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(14000)),
    ]
    for bid in bids:
        await auc_repo.add_bid(bid)


@pytest.mark.asyncio
async def test_seller_start_auction() -> None:
    assert True


@pytest.mark.asyncio
async def test_bidder_place_bid(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    await start_auction(auc_repo)
    post_token = PostToken("A")
    auction = await auc_repo.read_auction_by_post_token(post_token=post_token)
    assert auction is not None

    bid_data = PlaceBid(
        auction_id=auction.uid, post_token=post_token, amount=Rial(11000)
    )
    response = bidder_client.post(
        "/auc/place-bid",
        data=bid_data.model_dump(mode="json"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bid placed" in response.text


@pytest.mark.asyncio
async def test_bidder_sees_top_bids(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    await start_auction_with_bids(auc_repo)
    params = {"post_token": "A", "return_url": "https://divar.ir"}
    response = bidder_client.get("/auc", params=params, follow_redirects=True)

    assert "14000" in response.text
    assert "13000" in response.text
    assert "12000" in response.text
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_seller_select_bid() -> None:
    assert True
