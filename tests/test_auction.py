from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from auction._types import AuctionID, PostToken, Rial, UserID
from auction.divar import mock_data as divar_mock_data
from auction.i18n import gettext as _
from auction.model import Auction, AuctionStartInput, Bid, PlaceBid, SelectBid
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
        post_title=_("Test Post"),
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
async def test_seller_start_auction(
    seller_client: TestClient, auc_repo: AuctionRepo
) -> None:
    post_token = PostToken("A")
    auction_start_input = AuctionStartInput(
        post_token=post_token, starting_price=Rial(1000)
    )
    response = seller_client.post(
        f"/auction/management/start/{post_token}",
        data=auction_start_input.model_dump(mode="json"),
        params={"hl": "en"},
    )
    assert response.status_code == 200
    auction = await auc_repo.read_auction_by_post_token(post_token=post_token)
    assert auction is not None


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
        "/auction/bidding/place-bid",
        data=bid_data.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bid placed" in response.text


@pytest.mark.asyncio
async def test_bidder_sees_top_bids(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    await start_auction_with_bids(auc_repo)
    params = {"hl": "en", "post_token": "A", "return_url": "https://divar.ir"}
    response = bidder_client.get("/auction", params=params, follow_redirects=True)

    assert "14000" in response.text
    assert "13000" in response.text
    assert "12000" in response.text
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_seller_select_bid(
    seller_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(1000000))
    await auc_repo.add_bid(bid)

    select_bid = SelectBid(bid_id=bid.uid)
    response = seller_client.post(
        f"/auction/management/select-bid/{auction.post_token}",
        data=select_bid.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    auction_updated = await auc_repo.read_auction_by_id(auction_id=auction.uid)
    assert auction_updated is not None
    assert auction_updated.selected_bid == bid.uid


@pytest.mark.asyncio
async def test_remove_selected_bid_after_bidder_changes_amount(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(1000000))
    await auc_repo.add_bid(bid)
    await auc_repo.select_bid(auction, bid_id=bid.uid)

    bid_data = PlaceBid(
        auction_id=auction.uid, post_token=auction.post_token, amount=Rial(2000000)
    )
    response = bidder_client.post(
        "/auction/bidding/place-bid",
        data=bid_data.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bid placed" in response.text
    updated_auction = await auc_repo.read_auction_by_id(auction_id=auction.uid)
    assert updated_auction is not None
    assert updated_auction.selected_bid is None


@pytest.mark.asyncio
async def test_bidder_remove_bid(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    bidder_id = UserID(divar_mock_data.BIDDER_PHONE_NUMBER)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=Rial(1000000))
    await auc_repo.add_bid(bid)
    await auc_repo.select_bid(auction, bid_id=bid.uid)

    response = bidder_client.delete(
        f"/auction/bidding/remove-bid/{auction.post_token}",
        params={"hl": "en"},
    )
    assert response.status_code == 200
    assert "Bid removed" in response.text
    remove_bid = await auc_repo.read_bid_by_id(bid_id=bid.uid)
    assert remove_bid is None
