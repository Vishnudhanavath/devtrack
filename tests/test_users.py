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
    