from auction._types import DivarReturnUrl, PostToken
from auction.db import get_session
from auction.repo import AuctionRepo, SQLARepo, auction_repo


async def get_file_repo() -> AuctionRepo:
    return auction_repo


async def get_repo() -> AuctionRepo:
    sessionmaker = get_session()
    repo = SQLARepo(session=sessionmaker)
    return repo


async def get_return_url(
    post_token: PostToken, return_url: DivarReturnUrl | None = None
) -> DivarReturnUrl:
    if return_url:
        return return_url
    return_url = DivarReturnUrl(f"https://divar.ir/v/{post_token}")
    return return_url
