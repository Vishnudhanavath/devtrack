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


def test_sort_users_by_name_ascending(client):
    token, _ = register_and_login(client, "Sorting Test User")

    response = client.get(
        "/api/v1/users?sort_by=name&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    data = response.json()
    names = [user["name"] for user in data["item"]]

    assert names == sorted(names)


def test_sort_users_rejects_invalid_field(client):
    token, _ = register_and_login(client, "Invalid Sort Field Test")

    response = client.get(
        "/api/v1/users?sort_by=password",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_sort_users_rejects_invalid_order(client):
    token, _ = register_and_login(client, "Invalid Sort Order Test")

    response = client.get(
        "/api/v1/users?sort_order=random",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_sort_users_by_name_descending(client):
    token, _ = register_and_login(client, "Desc Sort User")

    response = client.get(
        "/api/v1/users?sort_by=name&sort_order=desc",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    data = response.json()
    names = [user["name"] for user in data["item"]]

    assert names == sorted(names, reverse=True)


def test_sort_users_by_email_ascending(client):
    token, _ = register_and_login(client, "Email Sort User")

    response = client.get(
        "/api/v1/users?sort_by=email&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    data = response.json()
    emails = [user["email"] for user in data["item"]]

    assert emails == sorted(emails)