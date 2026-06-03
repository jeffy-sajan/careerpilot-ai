import pytest
from fastapi import HTTPException
from app.services import auth_service
from app.schemas.user import UserCreate
from app.repositories import refresh_token_repo

@pytest.fixture
async def sample_user(db_session):
    user_in = UserCreate(
        name="Auth Service User",
        email="auth.service@example.com",
        password="secret1Password"
    )
    user = await auth_service.register(db_session, user_in)
    return user

@pytest.mark.asyncio
async def test_register_duplicate_email(db_session, sample_user):
    user_in = UserCreate(
        name="Another User",
        email=sample_user.email,
        password="secret1Password2"
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.register(db_session, user_in)
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_authenticate_success(db_session, sample_user):
    user = await auth_service.authenticate(db_session, sample_user.email, "secret1Password")
    assert user.id == sample_user.id

@pytest.mark.asyncio
async def test_authenticate_wrong_password(db_session, sample_user):
    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate(db_session, sample_user.email, "wrong1Password")
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_authenticate_wrong_email(db_session):
    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate(db_session, "nonexistent@example.com", "password")
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_create_and_refresh_tokens(db_session, sample_user):
    tokens = await auth_service.create_tokens(db_session, sample_user.id)
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    
    # Check that refresh token is saved in DB
    from app.services.auth_service import _hash_token
    rt_hash = _hash_token(tokens.refresh_token)
    db_token = await refresh_token_repo.get_by_hash(db_session, rt_hash)
    assert db_token is not None
    
    # Now refresh the token
    new_tokens = await auth_service.refresh_tokens(db_session, tokens.refresh_token)
    assert new_tokens.access_token is not None
    assert new_tokens.refresh_token is not None
    assert new_tokens.refresh_token != tokens.refresh_token
    
    # Old token should be revoked
    revoked_token = await refresh_token_repo.get_by_hash(db_session, rt_hash)
    assert revoked_token is None

@pytest.mark.asyncio
async def test_refresh_token_invalid(db_session):
    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(db_session, "invalid.refresh.token")
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_expired(db_session, sample_user, monkeypatch):
    import datetime
    
    # We create a token manually that is already expired
    from app.services.auth_service import _hash_token
    import secrets
    rt = secrets.token_urlsafe(32)
    rt_hash = _hash_token(rt)
    # expired 1 day ago
    expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    
    db_token = await refresh_token_repo.create(db_session, sample_user.id, rt_hash, expires_at)
    
    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(db_session, rt)
    assert exc.value.status_code == 401
    
    # It should be revoked
    revoked = await refresh_token_repo.get_by_hash(db_session, rt_hash)
    assert revoked is None

@pytest.mark.asyncio
async def test_request_password_reset_not_found(db_session):
    with pytest.raises(HTTPException) as exc:
        await auth_service.request_password_reset(db_session, "notfound@example.com")
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_request_and_reset_password(db_session, sample_user, capsys):
    # Request reset
    await auth_service.request_password_reset(db_session, sample_user.email)
    
    # Read the token from stdout
    captured = capsys.readouterr()
    stdout = captured.out
    
    # Extract token
    # "http://localhost:5173/reset-password?token=..."
    token_line = [line for line in stdout.split('\n') if "?token=" in line][0]
    token = token_line.split("?token=")[1]
    
    # Verify the token works to reset password
    await auth_service.reset_password(db_session, token, "newsecret1Password")
    
    # Verify old password fails, new password works
    with pytest.raises(HTTPException):
        await auth_service.authenticate(db_session, sample_user.email, "secret1Password")
        
    user = await auth_service.authenticate(db_session, sample_user.email, "newsecret1Password")
    assert user.id == sample_user.id

@pytest.mark.asyncio
async def test_reset_password_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc:
        await auth_service.reset_password(db_session, "invalid_token", "new1Password")
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_reset_password_user_deleted(db_session, sample_user):
    from app.core.security import create_password_reset_token
    token = create_password_reset_token(sample_user.email)
    
    # delete user
    await db_session.delete(sample_user)
    await db_session.commit()
    
    with pytest.raises(HTTPException) as exc:
        await auth_service.reset_password(db_session, token, "new1Password")
    assert exc.value.status_code == 404
