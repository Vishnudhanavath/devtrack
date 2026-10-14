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

    return registration.json(), login.json()["access_token"]


def test_user_can_update_own_account(client):
    user, token = register_and_login(client, "Original Name")

    response = client.put(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Name",
            "email": user["email"],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Name"


def test_user_can_patch_own_account(client):
    user, token = register_and_login(client, "Original Patch Name")

    response = client.patch(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Patched Name"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Patched Name"


def test_user_can_delete_own_account(client):
    user, token = register_and_login(client, "Account To Delete")

    response = client.delete(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204, response.text

    # Verify that the account no longer exists.
    get_response = client.get(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404


def test_user_can_get_own_account(client):
    user, token = register_and_login(client, "Get User Test")

    response = client.get(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == user["id"]
    assert data["name"] == "Get User Test"
    assert data["email"] == user["email"]
    assert "password" not in data
    assert "password_hash" not in data


def test_get_nonexistent_user_returns_404(client):
    user, token = register_and_login(client, "Ghost User")

    # Delete the user first
    del_resp = client.delete(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    # Now attempt to get the user using the token
    response = client.get(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_duplicate_email(client):
    user1, token1 = register_and_login(client, "User One")
    user2, _ = register_and_login(client, "User Two")

    response = client.put(
        f"/api/v1/users/{user1['id']}",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "User One Updated",
            "email": user2["email"],
        },
    )

    assert response.status_code == 409


def test_patch_user_duplicate_email(client):
    user1, token1 = register_and_login(client, "User One Patch")
    user2, _ = register_and_login(client, "User Two Patch")

    response = client.patch(
        f"/api/v1/users/{user1['id']}",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "email": user2["email"],
        },
    )

    assert response.status_code == 409


def test_user_cannot_be_deleted_while_owning_projects(client):
    user, token = register_and_login(client, "Owner Deleter")

    # User creates a project
    proj_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Owner Project"},
    )
    assert proj_resp.status_code == 201

    # Attempt to delete user while owning a project
    response = client.delete(
        f"/api/v1/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert "User cannot be deleted while they own projects" in response.json()["detail"]


def test_user_member_of_project_can_delete_account(client):
    owner, owner_token = register_and_login(client, "Project Owner")
    member, member_token = register_and_login(client, "Project Member")

    # Owner creates project
    proj_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Team Project"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Add member to project
    add_resp = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"user_id": member["id"], "role": "member"},
    )
    assert add_resp.status_code == 201

    # Member deletes their own account - should succeed
    del_resp = client.delete(
        f"/api/v1/users/{member['id']}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert del_resp.status_code == 204

    # Check project members list - member should no longer be in the list
    list_resp = client.get(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_resp.status_code == 200
    m_ids = [m["user_id"] for m in list_resp.json()]
    assert member["id"] not in m_ids