from uuid import uuid4


def register_and_login(client, name):
    email = f"{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration = client.post(
        "/api/v1/users",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201, registration.text

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200, login.text

    return login.json()["access_token"]


def test_user_pagination(client):
    token = register_and_login(client, "Pagination Test User")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/api/v1/users?page=1&page_size=2",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "item" in data
    assert len(data["item"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= len(data["item"])
    assert data["total_pages"] >= 1

    # Verify that sensitive fields aren't exposed.
    for user in data["item"]:
        assert "password" not in user
        assert "password_hash" not in user


def test_user_pagination_rejects_invalid_page(client):
    token = register_and_login(client, "Pagination Validation User")

    response = client.get(
        "/api/v1/users?page=0",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


def test_user_pagination_rejects_excessive_page_size(client):
    token = register_and_login(client, "Page Size Validation User")

    response = client.get(
        "/api/v1/users?page_size=101",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422



def test_user_pagination_page_out_of_range(client):
    token = register_and_login(client, "Page Out Of Range User")

    response = client.get(
        "/api/v1/users?page=9999&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["item"] == []
    assert data["page"] == 9999


def test_user_pagination_rejects_zero_page_size(client):
    token = register_and_login(client, "Zero Page Size User")

    response = client.get(
        "/api/v1/users?page_size=0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422







