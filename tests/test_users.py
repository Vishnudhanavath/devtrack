from uuid import uuid4

from app.core.security import verify_password
from app.models.user import User


def test_register_user(client, db_session):
    # Arrange: create unique test data.
    password = "StrongPassword123!"
    email = f"test-{uuid4().hex}@example.com"

    payload = {
        "name": "Test User",
        "email": email,
        "password": password,
    }

    # Act: send a registration request to the API.
    response = client.post(
        "/api/v1/users",
        json=payload,
    )

    # Assert: verify the HTTP response.
    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == payload["name"]
    assert response_data["email"] == email

    # Password information must never be returned.
    assert "password" not in response_data
    assert "password_hash" not in response_data

    # Assert: verify the user was saved in the database.
    saved_user = (
        db_session.query(User)
        .filter(User.email == email)
        .one()
    )

    assert saved_user.name == payload["name"]

    # The stored password must not equal the original password.
    assert saved_user.password_hash != password

    # Verify that the stored hash matches the original password.
    assert verify_password(password, saved_user.password_hash)





def test_register_user_with_duplicate_email(client):
    email = f"duplicate-{uuid4().hex}@example.com"

    payload = {
        "name": "First User",
        "email": email,
        "password": "StrongPassword123!",
    }

    # First registration should succeed.
    first_response = client.post(
        "/api/v1/users",
        json=payload,
    )

    assert first_response.status_code == 201

    # Attempt to register the same email again.
    second_response = client.post(
        "/api/v1/users",
        json={
            "name": "Second User",
            "email": email,
            "password": "AnotherPassword123!",
        },
    )

    assert second_response.status_code == 409
    assert "already" in second_response.json()["detail"].lower()





def test_login_with_valid_credentials(client):
    email = f"login-{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    # Register a user first.
    registration = client.post(
        "/api/v1/users",
        json={
            "name": "Login Test User",
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201

    # Attempt login with the same credentials.
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0

    

def test_login_with_wrong_password(client):
    email = f"wrong-password-{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration = client.post(
        "/api/v1/users",
        json={
            "name": "Login Test User",
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_login_with_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"unknown-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_register_user_invalid_email(client):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Invalid Email User",
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_user_short_password(client):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Short Pwd User",
            "email": f"short-pwd-{uuid4().hex}@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_user_empty_name(client):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "",
            "email": f"empty-name-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_user_extra_fields_forbidden(client):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Hacker User",
            "email": f"hacker-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_register_user_missing_required_fields(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": f"missing-name-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422