from typing import Annotated

import httpx

from kenar import Client as DivarClient
from kenar import (
    ClientConfig,
    CreatePostAddonRequest,
    CreatePostAddonResponse,
    DeletePostAddonRequest,
    DeletePostAddonResponse,
    GetPostRequest,
    GetPostResponse,
    GetUserPostsRequest,
    GetUserPostsResponse,
    GetUserRequest,
    GetUserResponse,
)
from kenar.app import ACCESS_TOKEN_HEADER_NAME, AddonService, FinderService
from pydantic import AfterValidator, BaseModel, HttpUrl, UrlConstraints

from auction._types import PostToken
from auction.config import config, divar_config
from auction.exception import PostNotFound
from auction.i18n import gettext as _
from auction.log import logger


client_conf = ClientConfig(
    app_slug=divar_config.app_slug,
    api_key=divar_config.api_key,
    oauth_secret=divar_config.oauth_secret,
    oauth_redirect_url=divar_config.oauth_redirect_url,
)

divar_client = DivarClient(client_conf)


def _only_divar_domain(url: HttpUrl) -> HttpUrl:
    if url.host != "divar.ir":
        raise ValueError(_("return url must be from divar.ir domain"))
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


class Post(BaseModel):
    token: str
    title: str


class AuctionAddonService(AddonService):
    def __init__(self, client: httpx.Client):
        self._client = client
        self._aclient = httpx.AsyncClient(
            timeout=1,
            headers=client.headers,
            base_url=client.base_url,
        )
        super().__init__(client=client)

    async def create_post_addon(
        self,
        access_token: str,
        data: CreatePostAddonRequest,
    ) -> CreatePostAddonResponse:
        async def send_request():
            return await self._aclient.post(
                url=f"/v2/open-platform/addons/post/{data.token}",
                content=data.model_dump_json(exclude={"token"}),
                headers={ACCESS_TOKEN_HEADER_NAME: access_token},
            )

        rsp = await send_request()
        if not rsp.is_success:
            logger.error(f"create_post_addon error: {rsp.status_code} {rsp.text}")
        return CreatePostAddonResponse()

    async def delete_post_addon(
        self,
        data: DeletePostAddonRequest,
    ) -> DeletePostAddonResponse | None:
        async def send_request():
            return await self._aclient.delete(
                url=f"/v1/open-platform/addons/post/{data.token}",
                params=data.json(),
            )

        rsp = await send_request()
        if not rsp.is_success:
            logger.error(f"delete_post_addon error: {rsp.status_code} {rsp.text}")
            return None
        return DeletePostAddonResponse()


class AuctionFinderService(FinderService):
    """finder service with some fixes"""

    def __init__(self, client: httpx.Client):
        self._client = client
        self._aclient = httpx.AsyncClient(
            timeout=1,
            headers=client.headers,
            base_url=client.base_url,
        )
        super().__init__(client=client)

    async def get_post(
        self,
        data: GetPostRequest,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetPostResponse | None:
        async def send_request():
            return await self._aclient.request(
                method="GET",
                url=f"/v1/open-platform/finder/post/{data.token}",
                content=data.json(),
            )

        rsp = await send_request()
        if rsp.is_success:
            return PostItemResponse(**rsp.json())
        logger.error(f"get_post error: {rsp.status_code} {rsp.text}")
        return None

    async def get_user(
        self,
        access_token: str,
        data: GetUserRequest = None,
        max_retry: int = 3,
        retry_delay: int = 1,
    ) -> GetUserResponse:
        async def send_request():
            return await self._aclient.post(
                url="/v1/open-platform/users",
                content=data.json() if data is not None else "",
                headers={ACCESS_TOKEN_HEADER_NAME: access_token},
            )

        rsp = await send_request()
        if rsp.is_success:
            return GetUserResponse(**rsp.json())
        logger.error(f"get_user error: {rsp.status_code} {rsp.text}")
        return GetUserResponse(phone_numbers=[])

    async def get_user_posts(
        self,
        access_token: str,
        data: GetUserPostsRequest | None = None,
    ):
        async def send_request():
            return await self._aclient.get(
                url="/v1/open-platform/finder/user-posts",
                params=data.json() if data is not None else "",
                headers={ACCESS_TOKEN_HEADER_NAME: access_token},
            )

        rsp = await send_request()
        if rsp.is_success:
            return GetUserPostsResponse(**rsp.json())
        # TODO: log response error
        logger.error(f"get_user_posts error: {rsp.status_code} {rsp.text}")
        return GetUserPostsResponse(posts=[])

    async def validate_post(self, post_token: PostToken) -> PostItemResponse:
        if not post_token:
            raise PostNotFound()
        if config.debug:
            return PostItemResponse.dummy(post_token=post_token)
        post = await self.get_post(GetPostRequest(token=post_token))
        if post is None:
            raise PostNotFound()
        return post

    async def find_post_from_user_posts(
        self, post_token: PostToken, user_access_token: str
    ) -> Post | None:
        """access_token must have GET_USER_POSTS scope access"""

        if not post_token:
            return None
        if config.debug:
            return Post(token=post_token, title="Dummy Post")
        result = await self.get_user_posts(access_token=user_access_token)
        if not result.posts:
            return None
        return next((post for post in result.posts if post.token == post_token), None)


auction_finder = AuctionFinderService(client=divar_client._client)
auction_addon = AuctionAddonService(client=divar_client._client)
divar_client.finder = auction_finder
divar_client.addon = auction_addon


async def get_divar_client() -> DivarClient:
    return divar_client


if __name__ == "__main__":
    import asyncio
    import sys

    post_token = ""
    if len(sys.argv) > 1:
        post_token = sys.argv[1]
    resp = asyncio.run(divar_client.finder.get_post(GetPostRequest(token=post_token)))
    if resp:
        print(resp.model_dump())
