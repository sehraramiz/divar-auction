from auction._types import PostToken
from auction.divar import DivarReturnUrl
from auction.repo import AuctionRepo, auction_repo


async def get_repo() -> AuctionRepo:
    return auction_repo


async def get_return_url(
    post_token: PostToken, return_url: DivarReturnUrl | None = None
) -> DivarReturnUrl:
    if return_url:
        return return_url
    return_url = DivarReturnUrl(f"https://divar.ir/v/{post_token}")
    return return_url
