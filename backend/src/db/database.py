"""SQLAlchemy database setup with async support."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from typing import AsyncGenerator

from src.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={
        "check_same_thread": False,  # aiosqlite 后台线程执行，需要允许跨线程
        "timeout": 60,                # sqlite3 连接级别锁等待超时（秒）
    },
    poolclass=NullPool,              # 异步引擎仅支持 NullPool（每个 task 独立连接）
)


# 启用 WAL 模式 + 长 busy_timeout，允许读写并发，大幅降低锁冲突
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    dbapi_connection.execute("PRAGMA journal_mode=WAL")
    dbapi_connection.execute("PRAGMA busy_timeout=60000")    # 60秒等待写锁释放
    dbapi_connection.execute("PRAGMA synchronous=NORMAL")    # 降低同步开销
    dbapi_connection.execute("PRAGMA cache_size=-60000")     # 加大缓存（字节），60MB
    dbapi_connection.execute("PRAGMA temp_store=MEMORY")     # 临时表存内存

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
