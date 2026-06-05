import ssl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Detect database type
_is_sqlite = settings.database_url.startswith("sqlite")
_is_neon = "neon.tech" in settings.database_url

engine_kwargs: dict = {
    "echo": settings.app_env == "development",
}

if _is_sqlite:
    # SQLite: no pool settings
    pass
elif _is_neon:
    # NeonDB: requires SSL, uses connection pooler
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"ssl": ssl_ctx},
    )
else:
    # Standard PostgreSQL
    engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
