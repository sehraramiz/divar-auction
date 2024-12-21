import os

from typing import AsyncGenerator

import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auction import db
from auction._types import UserID
from auction.api_deps import get_repo
from auction.app import app
from auction.auth import (
    auction_management_access,
    authorize_user_and_set_session,
    get_user_id_from_session,
)
from auction.divar import get_divar_client, get_divar_client_mock
from auction.repo import AuctionRepo, SQLARepo


def get_test_repo() -> AuctionRepo:
    return SQLARepo(session=sqla_session)


@pytest.fixture(scope="function")
def auc_repo(sqla_session: async_sessionmaker[AsyncSession]) -> AuctionRepo:
    return SQLARepo(session=sqla_session)


@pytest_asyncio.fixture(scope="function")
async def sqla_session() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    database_url = "sqlite+aiosqlite:///./test.db"
    engine = db.get_engine(database_url=database_url)

    async with engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.drop_all)
        await conn.run_sync(db.Base.metadata.create_all)

    sessionmaker = db.get_session(engine=engine)
    yield sessionmaker


def authorize_seller_user() -> UserID:
    from auction.divar.mock_data import SELLER_PHONE_NUMBER

    return UserID(SELLER_PHONE_NUMBER)


def authorize_bidder_user() -> UserID:
    from auction.divar.mock_data import BIDDER_PHONE_NUMBER

    return UserID(BIDDER_PHONE_NUMBER)


def auction_management_access_test() -> str:
    return "dummy access token"


@pytest.fixture
def seller_client(auc_repo: AuctionRepo):
    """Fixture to provide a test seller client with dependency overrides."""
    client = TestClient(app)
    app.dependency_overrides[get_divar_client] = get_divar_client_mock
    app.dependency_overrides[auction_management_access] = auction_management_access_test
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
    app.dependency_overrides[auction_management_access] = auction_management_access_test
    app.dependency_overrides[get_repo] = lambda: auc_repo
    app.dependency_overrides[authorize_user_and_set_session] = authorize_bidder_user
    app.dependency_overrides[get_user_id_from_session] = authorize_bidder_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def remove_db_file():
    db_file = "test.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield
    if os.path.exists(db_file):
        os.remove(db_file)
