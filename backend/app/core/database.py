from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables on startup, and migrate new columns if needed."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column migrations for SQLite
        for col_sql in [
            "ALTER TABLE interview_sessions ADD COLUMN github_url TEXT",
            "ALTER TABLE interview_sessions ADD COLUMN github_context TEXT",
            "ALTER TABLE interview_sessions ADD COLUMN optimize_result TEXT",
            "ALTER TABLE jobs ADD COLUMN archetype VARCHAR(64) DEFAULT ''",
            "ALTER TABLE jobs ADD COLUMN fit_analysis TEXT",
        ]:
            try:
                await conn.execute(__import__("sqlalchemy").text(col_sql))
            except Exception:
                pass  # column already exists
