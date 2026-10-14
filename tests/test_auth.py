import time
from uuid import uuid4
import jwt

from app.core.config import settings


def register_user(client, name):
    email = f"{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    response = client.post(
        "/api/v1/users",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201

    return {
        "id": response.json()["id"],
        "email": email,
        "password": password,
    }


def test_protected_users_endpoint_rejects_missing_token(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 401


def test_protected_users_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )
    assert response.status_code == 401


def test_protected_users_endpoint_rejects_malformed_token(client):
    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": "Bearer not.a.valid.jwt.token",
        },
    )
    assert response.status_code == 401


def test_protected_users_endpoint_rejects_non_bearer_scheme(client):
    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": "Basic dXNlcjpwYXNz",
        },
    )
    assert response.status_code == 401


def test_protected_users_endpoint_rejects_expired_token(client):
    user = register_user(client, "Expired Token User")

    expired_payload = {
        "sub": str(user["id"]),
        "exp": int(time.time()) - 3600,
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )
    assert response.status_code == 401


def test_login_success(client):
    user = register_user(client, "Auth Login User")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client):
    user = register_user(client, "Wrong Pwd User")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user["email"],
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"unknown-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_missing_required_fields(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "incomplete@example.com",
        },
    )

    assert response.status_code == 422