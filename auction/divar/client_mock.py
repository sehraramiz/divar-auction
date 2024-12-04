from kenar import Client as DivarClient
from kenar import (
    ClientConfig,
    GetPostRequest,
    GetPostResponse,
    GetUserPostsRequest,
    GetUserPostsResponse,
    GetUserRequest,
    GetUserResponse,
)

from auction._types import PostToken
from auction.divar import mock_data

from .client import AuctionFinderService, Post, PostItemResponse


client_conf = ClientConfig(
    app_slug="auction-app-mock",
    api_key="api1234",
    oauth_secret="secret",
    oauth_redirect_url="http://127.0.0.1:8000",
)


class DivarClientMock(DivarClient):
    def __init__(self) -> None:
        super().__init__(conf=client_conf)


divar_client_mock = DivarClient(client_conf)


class AuctionFinderServiceMock(AuctionFinderService):
    """finder service mock"""

    def get_post(
        self,
        data: GetPostRequest,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetPostResponse | None:
        return PostItemResponse()

    def get_user(
        self,
        access_token: str,
        data: GetUserRequest = None,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetUserResponse:
        return GetUserResponse(phone_numbers=[mock_data.SELLER_PHONE_NUMBER])

    def get_user_posts(
        self,
        access_token: str,
        data: GetUserPostsRequest | None = None,
    ):
        post = GetUserPostsResponse.Post(
            token="token", title="Mock Post", images=[], category=""
        )
        return GetUserPostsResponse(posts=[post])

    async def validate_post(self, post_token: PostToken) -> PostItemResponse:
        return PostItemResponse.dummy(post_token=post_token)

    async def find_post_from_user_posts(
        self, post_token: PostToken, user_access_token: str
    ) -> Post | None:
        result = self.get_user_posts(access_token=user_access_token)
        return next((post for post in result.posts), None)


auction_finder = AuctionFinderServiceMock(client=divar_client_mock._client)
divar_client_mock.finder = auction_finder


async def get_divar_client_mock() -> DivarClientMock:
    return divar_client_mock
