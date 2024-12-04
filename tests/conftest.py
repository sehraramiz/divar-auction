import os

import pytest

from fastapi.testclient import TestClient

from auction._types import UserID
from auction.api_deps import get_repo
from auction.app import app
from auction.auth import (
    authorize_user_and_set_session,
    get_user_id_from_session,
    user_get_posts_permission,
)
from auction.divar import get_divar_client, get_divar_client_mock
from auction.repo import AuctionRepo


def get_test_repo() -> AuctionRepo:
    return AuctionRepo(db_file_name="db.test.json")


@pytest.fixture(scope="function")
def auc_repo() -> AuctionRepo:
    return AuctionRepo(db_file_name="db.test.json")


def authorize_seller_user() -> UserID:
    from auction.divar.mock_data import SELLER_PHONE_NUMBER

    return UserID(SELLER_PHONE_NUMBER)


def authorize_bidder_user() -> UserID:
    from auction.divar.mock_data import BIDDER_PHONE_NUMBER

    return UserID(BIDDER_PHONE_NUMBER)


def user_get_posts_permission_test() -> str:
    return "dummy access token"


@pytest.fixture
def seller_client(auc_repo: AuctionRepo):
    """Fixture to provide a test seller client with dependency overrides."""
    client = TestClient(app)
    app.dependency_overrides[get_divar_client] = get_divar_client_mock
    app.dependency_overrides[user_get_posts_permission] = user_get_posts_permission_test
    app.dependency_overrides[get_repo] = lambda: auc_repo
    app.dependency_overrides[authorize_user_and_set_session] = authorize_seller_user
    app.dependency_overrides[get_user_id_from_session] = authorize_seller_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def bidder_client(auc_repo: AuctionRepo):
    """Fixture to provide a test seller client with dependency overrides."""
    client = TestClient(app)
    app.dependency_overrides[get_divar_client] = get_divar_client_mock
    app.dependency_overrides[user_get_posts_permission] = user_get_posts_permission_test
    app.dependency_overrides[get_repo] = lambda: auc_repo
    app.dependency_overrides[authorize_user_and_set_session] = authorize_bidder_user
    app.dependency_overrides[get_user_id_from_session] = authorize_bidder_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def remove_db_file():
    db_file = "db.test.json"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Database file '{db_file}' removed before test.")
    yield
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Database file '{db_file}' removed after test.")
