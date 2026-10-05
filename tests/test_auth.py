import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import verify_password, get_password_hash, create_access_token
from jose import jwt
from app.core.config import settings


def test_health():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["demo_mode"] is True


def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = "12345678-1234-5678-1234-567812345678"
    token = create_access_token(subject=user_id)
    assert token is not None

    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert "exp" in payload
