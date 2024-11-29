import logging
from typing import Annotated

from kenar import (
    GetPostRequest,
    GetPostResponse,
    GetUserResponse,
    GetUserRequest,
)
from kenar import ClientConfig, Client as DivarClient
from kenar.app import FinderService, ACCESS_TOKEN_HEADER_NAME
from pydantic import UrlConstraints, HttpUrl, AfterValidator

from config import divar_config
from _types import PostToken
from exception import PostNotFound


logging.basicConfig(level=logging.INFO)

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
        return GetUserResponse(phone_numbers=[])


auction_finder = AuctionFinderService(client=divar_client._client)
divar_client.finder = auction_finder


async def validate_post(post_token: PostToken) -> PostItemResponse:
    post = divar_client.finder.get_post(GetPostRequest(token=post_token))
    if post is None:
        raise PostNotFound()
    return post


if __name__ == "__main__":
    import sys

    post_token = ""
    if len(sys.argv) > 1:
        post_token = sys.argv[1]
    resp = divar_client.finder.get_post(GetPostRequest(token=post_token))
    if resp:
        print(resp.model_dump())
