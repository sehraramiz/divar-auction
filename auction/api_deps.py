from typing import Annotated, cast
from fastapi import Depends, Query

from repo import AuctionRepo, auction_repo
from _types import PostToken
from divar import DivarReturnUrl


async def get_repo() -> AuctionRepo:
    return auction_repo


async def get_session_data(
    auction_repo: Annotated[AuctionRepo, Depends(get_repo)],
    state: str = "nostate",
) -> dict:
    session_data = await auction_repo.get_session_data(state)
    return session_data


async def get_post_token_from_session(
    session_data: Annotated[dict, Depends(get_session_data)],
    post_token: Annotated[PostToken, Query()] = PostToken(""),
) -> PostToken:
    post_token = post_token or cast(PostToken, session_data.get("post_token", ""))
    if post_token:
        return PostToken(post_token)
    return PostToken("")


async def get_return_url_from_session(
    session_data: Annotated[dict, Depends(get_session_data)],
    return_url: Annotated[DivarReturnUrl | None, Query()] = None,
    post_token: Annotated[PostToken, Query()] = PostToken(""),
) -> DivarReturnUrl:
    return_url = return_url or session_data.get("return_url")
    if return_url:
        return DivarReturnUrl(return_url)
    return DivarReturnUrl(f"https://divar.ir/v/{post_token}")
