import pytest
from datetime import datetime, timedelta, timezone
from app.repositories import refresh_token_repo, user_repo
from app.schemas.user import UserCreate

@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(
        name="Token User",
        email="token@example.com",
        password="secret1Password"
    )
    user = await user_repo.create(db_session, user_in)
    return user

@pytest.mark.asyncio
async def test_refresh_token_lifecycle(db_session, sample_user):
    # 1. Create Token
    token_hash = "some_random_hash"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    token = await refresh_token_repo.create(
        db_session,
        user_id=sample_user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    assert token.id is not None
    assert token.user_id == sample_user.id
    assert token.token_hash == token_hash
    assert token.is_revoked is False
    
    # 2. Get by hash
    fetched = await refresh_token_repo.get_by_hash(db_session, token_hash)
    assert fetched is not None
    assert fetched.id == token.id
    assert fetched.is_revoked is False
    
    # 3. Revoke
    await refresh_token_repo.revoke(db_session, token.id)
    fetched_revoked = await refresh_token_repo.get_by_hash(db_session, token_hash)
    # the repo get_by_hash returns None if revoked
    assert fetched_revoked is None

@pytest.mark.asyncio
async def test_revoke_all_for_user(db_session, sample_user):
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Create two tokens
    token1 = await refresh_token_repo.create(db_session, sample_user.id, "hash1", expires_at)
    token2 = await refresh_token_repo.create(db_session, sample_user.id, "hash2", expires_at)
    
    # Verify both are active
    assert await refresh_token_repo.get_by_hash(db_session, "hash1") is not None
    assert await refresh_token_repo.get_by_hash(db_session, "hash2") is not None
    
    # Revoke all
    await refresh_token_repo.revoke_all_for_user(db_session, sample_user.id)
    
    # Verify both are revoked (get_by_hash should return None)
    assert await refresh_token_repo.get_by_hash(db_session, "hash1") is None
    assert await refresh_token_repo.get_by_hash(db_session, "hash2") is None
