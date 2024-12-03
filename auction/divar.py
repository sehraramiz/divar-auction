import logging

from typing import Annotated

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
from kenar.app import ACCESS_TOKEN_HEADER_NAME, FinderService
from pydantic import AfterValidator, HttpUrl, UrlConstraints

from auction._types import PostToken
from auction.config import config, divar_config
from auction.exception import PostNotFound


logger = logging.getLogger(__name__)

client_conf = ClientConfig(
    app_slug=divar_config.app_slug,
    api_key=divar_config.api_key,
    oauth_secret=divar_config.oauth_secret,
    oauth_redirect_url=divar_config.oauth_redirect_url,
)

divar_client = DivarClient(client_conf)


def _only_divar_domain(url: HttpUrl) -> HttpUrl:
    if url.host != "divar.ir":
        raise ValueError("return url must be from divar.ir domain")
    return url


DivarReturnUrl = Annotated[
    HttpUrl,
    UrlConstraints(allowed_schemes=["https"]),
    AfterValidator(_only_divar_domain),
]


class PostItemResponse(GetPostResponse):
    first_published_at: str | None = None

    @classmethod
    def dummy(cls, post_token: str) -> "PostItemResponse":
        from kenar import PostExtState

        return cls(
            state=PostExtState.PUBLISHED.value,
            first_published_at=None,
            token=post_token,
            category="",
            city="",
            district="",
            data={},
        )


class AuctionFinderService(FinderService):
    """finder service with some fixes"""

    def get_post(
        self,
        data: GetPostRequest,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetPostResponse | None:
        def send_request():
            return self._client.request(
                method="GET",
                url=f"/v1/open-platform/finder/post/{data.token}",
                content=data.json(),
            )

        rsp = send_request()
        if rsp.is_success:
            return PostItemResponse(**rsp.json())
        logger.error(f"get_post error: {rsp.status_code} {rsp.text}")
        return None

    def get_user(
        self,
        access_token: str,
        data: GetUserRequest = None,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetUserResponse:
        def send_request():
            return self._client.post(
                url="/v1/open-platform/users",
                content=data.json() if data is not None else "",
                headers={ACCESS_TOKEN_HEADER_NAME: access_token},
            )

        rsp = send_request()
        if rsp.is_success:
            return GetUserResponse(**rsp.json())
        logger.error(f"get_user error: {rsp.status_code} {rsp.text}")
        return GetUserResponse(phone_numbers=[])

    def get_user_posts(
        self,
        access_token: str,
        data: GetUserPostsRequest | None = None,
    ):
        def send_request():
            return self._client.get(
                url="/v1/open-platform/finder/user-posts",
                params=data.json() if data is not None else "",
                headers={ACCESS_TOKEN_HEADER_NAME: access_token},
            )

        rsp = send_request()
        if rsp.is_success:
            return GetUserPostsResponse(**rsp.json())
        # TODO: log response error
        logger.error(f"get_user_posts error: {rsp.status_code} {rsp.text}")
        return GetUserPostsResponse(posts=[])


auction_finder = AuctionFinderService(client=divar_client._client)
divar_client.finder = auction_finder


async def validate_post(post_token: PostToken) -> PostItemResponse:
    if not post_token:
        raise PostNotFound()
    if config.debug:
        return PostItemResponse.dummy(post_token=post_token)
    post = divar_client.finder.get_post(GetPostRequest(token=post_token))
    if post is None:
        raise PostNotFound()
    return post


async def is_post_owner(post_token: PostToken, user_access_token: str) -> bool:
    """access_token must have GET_USER_POSTS scope access"""

    if not post_token:
        return False
    if config.debug:
        return True
    result = divar_client.finder.get_user_posts(access_token=user_access_token)
    if not result.posts:
        return False
    return any(post.token == post_token for post in result.posts)


if __name__ == "__main__":
    import sys

    post_token = ""
    if len(sys.argv) > 1:
        post_token = sys.argv[1]
    resp = divar_client.finder.get_post(GetPostRequest(token=post_token))
    if resp:
        print(resp.model_dump())
