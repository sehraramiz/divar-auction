import logging

from kenar import (
    GetPostRequest,
    GetPostResponse,
)
from kenar import ClientConfig, Client
from kenar.app import FinderService

from config import divar_config


logging.basicConfig(level=logging.INFO)

client_conf = ClientConfig(
    app_slug=divar_config.app_slug,
    api_key=divar_config.api_key,
    oauth_secret=divar_config.oauth_secret,
    oauth_redirect_url=divar_config.oauth_redirect_url,
)

divar_client = Client(client_conf)


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


auction_finder = AuctionFinderService(client=divar_client._client)
divar_client.finder = auction_finder


if __name__ == "__main__":
    resp = divar_client.finder.get_post(GetPostRequest(token="wYIw8OJp"))
    if resp:
        print(resp.model_dump())
