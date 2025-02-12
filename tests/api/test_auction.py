import html

from unittest import mock
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from auction import divar
from auction._types import AuctionID, PostToken, Rial, UserID
from auction.divar import mock_data as divar_mock_data
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
        post_title="Test Post",
    )
    auction = await auc_repo.add_auction(auction)
    return auction


async def start_auction_with_bids(auc_repo: AuctionRepo) -> Auction:
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
    await auc_repo.set_bids_on_auction(auction)
    return auction


@pytest.mark.asyncio
async def test_seller_start_auction(
    seller_client: TestClient, auc_repo: AuctionRepo
) -> None:
    post_token = PostToken("A")
    auction_start_input = AuctionStartInput(
        post_token=post_token, starting_price=Rial(1000)
    )
    response = seller_client.post(
        f"/auction/{post_token}/start",
        data=auction_start_input.model_dump(mode="json"),
        params={"hl": "en"},
    )
    assert response.status_code == 200
    auction = await auc_repo.read_auction_by_post_token(post_token=post_token)
    assert auction is not None


@pytest.mark.asyncio
async def test_seller_remove_auction(
    seller_client: TestClient, auc_repo: AuctionRepo
) -> None:
    divar_mock = divar.DivarClientMock()
    divar_mock.addon.delete_post_addon = mock.AsyncMock()
    seller_client.app.dependency_overrides[divar.get_divar_client] = lambda: divar_mock  # type: ignore

    auction = await start_auction_with_bids(auc_repo)

    response = seller_client.delete(
        f"/auction/{auction.post_token}",
        params={"hl": "en"},
    )

    removed_auction = await auc_repo.read_auction_by_post_token(
        post_token=auction.post_token
    )
    expected_addon_delete_input = divar.client.DeletePostAddonRequest(
        token=auction.post_token
    )
    first_bid = await auc_repo.read_bid_by_id(auction.bids[0].uid)

    assert response.status_code == 200
    assert removed_auction is None
    divar_mock.addon.delete_post_addon.assert_called_with(
        data=expected_addon_delete_input
    )
    assert first_bid is None


@pytest.mark.asyncio
async def test_bidder_place_bid(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    post_token = PostToken("A")
    bid_amount = Rial(auction.starting_price + auction.min_raise_amount)

    bid_data = PlaceBid(
        auction_id=auction.uid, post_token=post_token, amount=bid_amount
    )
    response = bidder_client.post(
        "/auction/bidding/",
        data=bid_data.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bid placed" in response.text


@pytest.mark.asyncio
async def test_bidder_place_bid_lower_than_starting_price(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    post_token = PostToken("A")

    bid_data = PlaceBid(auction_id=auction.uid, post_token=post_token, amount=Rial(10))
    response = bidder_client.post(
        "/auction/bidding/",
        data=bid_data.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )
    assert response.status_code == 400
    assert "Bid can't be lower than the starting price" in html.unescape(response.text)


@pytest.mark.asyncio
async def test_bidder_place_invalid_bid_amount(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    auction = await start_auction(auc_repo)
    post_token = PostToken("A")

    wrong_bid_amount = Rial(
        auction.starting_price + (auction.min_raise_amount) + Rial(1000)
    )
    bid_data = PlaceBid(
        auction_id=auction.uid, post_token=post_token, amount=wrong_bid_amount
    )
    response = bidder_client.post(
        "/auction/bidding/",
        data=bid_data.model_dump(mode="json"),
        params={"hl": "en"},
        follow_redirects=True,
    )
    assert response.status_code == 400
    assert (
        "Bid amount must starting price + multiple of min raise amount"
        in html.unescape(response.text)
    )


@pytest.mark.asyncio
async def test_bidder_sees_top_bids(
    bidder_client: TestClient, auc_repo: AuctionRepo
) -> None:
    await start_auction_with_bids(auc_repo)
    params = {"hl": "en", "post_token": "A", "return_url": "https://divar.ir"}
    response = bidder_client.get("/auction/", params=params, follow_redirects=True)

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
        f"/auction/{auction.post_token}/bids/select",
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
    bid_amount = Rial(auction.starting_price + auction.min_raise_amount)
    bid = Bid(bidder_id=bidder_id, auction_id=auction.uid, amount=bid_amount)
    await auc_repo.add_bid(bid)
    await auc_repo.select_bid(auction, bid_id=bid.uid)

    new_bid_amount = Rial(auction.starting_price + (2 * auction.min_raise_amount))
    bid_data = PlaceBid(
        auction_id=auction.uid, post_token=auction.post_token, amount=new_bid_amount
    )
    response = bidder_client.post(
        "/auction/bidding/",
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
        f"/auction/bidding/{auction.post_token}",
        params={"hl": "en"},
    )
    assert response.status_code == 200
    assert "Bid removed" in response.text
    remove_bid = await auc_repo.read_bid_by_id(bid_id=bid.uid)
    assert remove_bid is None
