from auction.repo import AuctionRepo, auction_repo


async def get_repo() -> AuctionRepo:
    return auction_repo
