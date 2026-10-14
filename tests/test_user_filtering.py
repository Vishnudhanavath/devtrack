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

    return login.json()["access_token"], email


def test_filter_users_by_name(client):
    token, email = register_and_login(client, "Vishnu Filter Test")

    response = client.get(
        "/api/v1/users?name=Vishnu Filter Test",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total"] >= 1
    assert any(user["email"] == email for user in data["item"])


def test_filter_users_by_partial_name(client):
    token, email = register_and_login(client, "PartialFilterTestVishnu")

    response = client.get(
        "/api/v1/users?name=PartialFilter",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert any(user["email"] == email for user in data["item"])




def test_filter_users_no_match(client):
    token, _ = register_and_login(client, "Any Filter User")

    response = client.get(
        "/api/v1/users?name=NonExistentNameXYZ987654321",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 0
    assert len(data["item"]) == 0