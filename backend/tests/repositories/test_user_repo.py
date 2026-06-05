import pytest

from app.repositories import user_repo
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_and_get_user(db_session):
    user_in = UserCreate(name="Test User", email="test@example.com", password="secret1Password")
    user = await user_repo.create(db_session, user_in)

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password_hash is not None

    # Get by ID
    fetched_user = await user_repo.get_by_id(db_session, user.id)
    assert fetched_user is not None
    assert fetched_user.id == user.id

    # Get by Email
    fetched_by_email = await user_repo.get_by_email(db_session, "test@example.com")
    assert fetched_by_email is not None
    assert fetched_by_email.id == user.id


@pytest.mark.asyncio
async def test_get_nonexistent_user(db_session):
    import uuid

    fetched = await user_repo.get_by_id(db_session, uuid.uuid4())
    assert fetched is None


@pytest.mark.asyncio
async def test_get_nonexistent_email(db_session):
    fetched = await user_repo.get_by_email(db_session, "nonexistent@example.com")
    assert fetched is None
