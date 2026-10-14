from uuid import uuid4


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

    assert response.status_code == 201, response.text

    return {
        "id": response.json()["id"],
        "email": email,
        "password": password,
    }


def login_user(client, email, password):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def test_update_user_requires_authentication(client):
    user = register_user(client, "Update Auth Test")

    response = client.put(
        f"/api/v1/users/{user['id']}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 401


def test_patch_user_requires_authentication(client):
    user = register_user(client, "Patch Auth Test")

    response = client.patch(
        f"/api/v1/users/{user['id']}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 401


def test_delete_user_requires_authentication(client):
    user = register_user(client, "Delete Auth Test")

    response = client.delete(
        f"/api/v1/users/{user['id']}",
    )

    assert response.status_code == 401


def test_user_cannot_update_another_users_account(client):
    owner = register_user(client, "Account Owner")
    attacker = register_user(client, "Another User")

    token = login_user(
        client,
        attacker["email"],
        attacker["password"],
    )

    response = client.put(
        f"/api/v1/users/{owner['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Unauthorized Change"},
    )

    assert response.status_code == 403


def test_user_cannot_patch_another_users_account(client):
    owner = register_user(client, "Patch Owner")
    attacker = register_user(client, "Patch Attacker")

    token = login_user(
        client,
        attacker["email"],
        attacker["password"],
    )

    response = client.patch(
        f"/api/v1/users/{owner['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Unauthorized Change"},
    )

    assert response.status_code == 403


def test_user_cannot_delete_another_users_account(client):
    owner = register_user(client, "Delete Owner")
    attacker = register_user(client, "Delete Attacker")

    token = login_user(
        client,
        attacker["email"],
        attacker["password"],
    )

    response = client.delete(
        f"/api/v1/users/{owner['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_get_user_requires_authentication(client):
    user = register_user(client, "Get Auth Test")

    response = client.get(
        f"/api/v1/users/{user['id']}",
    )

    assert response.status_code == 401


def test_user_cannot_get_another_users_account(client):
    owner = register_user(client, "Get Owner")
    attacker = register_user(client, "Get Attacker")

    token = login_user(
        client,
        attacker["email"],
        attacker["password"],
    )

    response = client.get(
        f"/api/v1/users/{owner['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not allowed to access this user"


def test_admin_check_allows_admin(client, db_session):
    admin = register_user(client, "Admin User")

    # Update role to admin in the database
    from app.models.enums import UserRole
    from app.models.user import User

    db_user = db_session.query(User).filter(User.id == admin["id"]).one()
    db_user.role = UserRole.ADMIN
    db_session.commit()

    token = login_user(
        client,
        admin["email"],
        admin["password"],
    )

    response = client.get(
        "/api/v1/users/admin-check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Welcome, administrator!"
    assert data["user_id"] == admin["id"]
    assert data["role"] == UserRole.ADMIN


def test_admin_check_rejects_regular_user(client):
    user = register_user(client, "Regular User")

    token = login_user(
        client,
        user["email"],
        user["password"],
    )

    response = client.get(
        "/api/v1/users/admin-check",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action"


def test_admin_check_requires_authentication(client):
    response = client.get("/api/v1/users/admin-check")
    assert response.status_code == 401