import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.database.base import Base
from app.database.session import get_async_session
from app.main import app

# Ensure we're using the test DB
assert "careerpilot_test" in settings.DATABASE_URL

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    # Create all tables once per session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Drop all tables after the session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture()
async def db_session(engine):
    """Provides an isolated database session by using a nested transaction that rolls back."""
    connection = await engine.connect()
    # Begin a non-nested transaction
    transaction = await connection.begin()
    
    # Bind the session to the connection
    session_maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=AsyncSession,
        join_transaction_mode="create_savepoint",
    )
    session = session_maker()
    
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()

@pytest_asyncio.fixture()
async def client(db_session):
    """Provides an HTTP client connected to the FastAPI app, overriding the DB dependency."""
    async def override_get_async_session():
        yield db_session
        
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    
    app.dependency_overrides.clear()
