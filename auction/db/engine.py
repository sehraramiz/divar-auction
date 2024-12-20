from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from auction.db.base import Base


@lru_cache
def get_engine(database_url: str | None = None) -> AsyncEngine:
    if database_url is None:
        database_url = "sqlite+aiosqlite:///./storage.db"
    engine = create_async_engine(database_url, echo=False)
    return engine


@lru_cache
def get_session(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    if engine is None:
        engine = get_engine()
    sessionmaker = async_sessionmaker(engine)
    return sessionmaker


async def setup_db() -> None:
    engine = get_engine()
    sessionmaker = async_sessionmaker(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmaker.begin() as session:
        res = await session.execute(select(1))
        print(res.all())


if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_db())
