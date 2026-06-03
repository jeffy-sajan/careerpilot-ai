from datetime import datetime, timezone

import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
)


def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    subject = "user123"
    token = create_access_token(subject)
    
    # Verify token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == subject
    assert "exp" in payload

def test_create_password_reset_token():
    email = "test@example.com"
    token = create_password_reset_token(email)
    
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == email
    assert payload["type"] == "password_reset"

def test_verify_password_reset_token():
    email = "test@example.com"
    token = create_password_reset_token(email)
    
    verified_email = verify_password_reset_token(token)
    assert verified_email == email

def test_verify_password_reset_token_invalid():
    invalid_token = "not.a.real.token"
    assert verify_password_reset_token(invalid_token) is None

def test_verify_password_reset_token_expired():
    # Create an artificially expired token
    to_encode = {
        "sub": "test@example.com",
        "type": "password_reset",
        "exp": datetime.now(timezone.utc).timestamp() - 1000  # expired
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    assert verify_password_reset_token(encoded_jwt) is None
