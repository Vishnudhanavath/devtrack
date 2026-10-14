from uuid import uuid4


def register_and_login(client, name):
    email = f"{name.lower().replace(' ', '-')}-{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration = client.post(
        "/api/v1/users",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200

    return registration.json()["id"], login.json()["access_token"]


def test_create_project_success(client):
    owner_id, owner_token = register_and_login(client, "Project Creator")

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "DevTrack Platform",
            "description": "Developer tracking software",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "DevTrack Platform"
    assert data["description"] == "Developer tracking software"
    assert data["owner_id"] == owner_id
    assert "id" in data


def test_create_project_unauthenticated(client):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Unauthorized Project",
            "description": "Should fail",
        },
    )

    assert response.status_code == 401


def test_create_project_missing_name(client):
    _, owner_token = register_and_login(client, "Validation User")

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "description": "Missing project name",
        },
    )

    assert response.status_code == 422


def test_get_my_projects_returns_only_owned_projects(client):
    owner1_id, owner1_token = register_and_login(client, "Owner One")
    owner2_id, owner2_token = register_and_login(client, "Owner Two")

    # Owner 1 creates two projects
    p1 = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner1_token}"},
        json={"name": "Project 1", "description": "First project"},
    ).json()

    p2 = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner1_token}"},
        json={"name": "Project 2", "description": "Second project"},
    ).json()

    # Owner 2 creates one project
    p3 = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner2_token}"},
        json={"name": "Project 3", "description": "Third project"},
    ).json()

    # Owner 1 lists their projects
    resp1 = client.get(
        "/api/v1/projects/mine",
        headers={"Authorization": f"Bearer {owner1_token}"},
    )
    assert resp1.status_code == 200
    ids1 = [p["id"] for p in resp1.json()]
    assert p1["id"] in ids1
    assert p2["id"] in ids1
    assert p3["id"] not in ids1

    # Owner 2 lists their projects
    resp2 = client.get(
        "/api/v1/projects/mine",
        headers={"Authorization": f"Bearer {owner2_token}"},
    )
    assert resp2.status_code == 200
    ids2 = [p["id"] for p in resp2.json()]
    assert p3["id"] in ids2
    assert p1["id"] not in ids2
    assert p2["id"] not in ids2


def test_get_my_projects_unauthenticated(client):
    response = client.get("/api/v1/projects/mine")
    assert response.status_code == 401


def test_get_project_by_owner(client):
    owner_id, owner_token = register_and_login(client, "Project Owner")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Owner Project", "description": "Details here"},
    )
    project_id = create_resp.json()["id"]

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Owner Project"
    assert data["owner_id"] == owner_id


def test_get_project_by_member(client):
    _, owner_token = register_and_login(client, "Project Owner")
    member_id, member_token = register_and_login(client, "Project Member")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Shared Project", "description": "Shared"},
    )
    project_id = create_resp.json()["id"]

    # Owner adds member
    add_resp = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"user_id": member_id, "role": "member"},
    )
    assert add_resp.status_code == 201

    # Member accesses project
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_non_member_cannot_access_project(client):
    _, owner_token = register_and_login(client, "Project Owner")

    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Private Test Project",
            "description": "A project for authorization testing",
        },
    )

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    _, outsider_token = register_and_login(client, "Project Outsider")

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )

    assert response.status_code == 403


def test_get_project_not_found(client):
    _, user_token = register_and_login(client, "Regular User")

    response = client.get(
        "/api/v1/projects/999999",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_get_project_unauthenticated(client):
    response = client.get("/api/v1/projects/1")
    assert response.status_code == 401


def test_update_project_by_owner(client):
    _, owner_token = register_and_login(client, "Update Owner")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Old Project Name", "description": "Old Description"},
    )
    project_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "New Project Name", "description": "New Description"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "New Project Name"
    assert data["description"] == "New Description"


def test_update_project_by_non_owner(client):
    _, owner_token = register_and_login(client, "Real Owner")
    _, outsider_token = register_and_login(client, "Unauthorized Updater")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Protected Project"},
    )
    project_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
        json={"name": "Malicious Update"},
    )

    assert response.status_code == 403


def test_update_project_not_found(client):
    _, user_token = register_and_login(client, "Updater")

    response = client.put(
        "/api/v1/projects/999999",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "Nonexistent Project"},
    )

    assert response.status_code == 404


def test_update_project_unauthenticated(client):
    response = client.put(
        "/api/v1/projects/1",
        json={"name": "No Auth"},
    )
    assert response.status_code == 401


def test_delete_project_by_owner(client):
    _, owner_token = register_and_login(client, "Delete Owner")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "To Be Deleted"},
    )
    project_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 204

    # Verify project no longer exists
    get_resp = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert get_resp.status_code == 404


def test_delete_project_by_non_owner(client):
    _, owner_token = register_and_login(client, "Delete Owner")
    _, outsider_token = register_and_login(client, "Delete Attacker")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Cannot Delete Me"},
    )
    project_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )

    assert response.status_code == 403


def test_delete_project_not_found(client):
    _, user_token = register_and_login(client, "Deleter")

    response = client.delete(
        "/api/v1/projects/999999",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404


def test_delete_project_unauthenticated(client):
    response = client.delete("/api/v1/projects/1")
    assert response.status_code == 401


def test_delete_project_cascades_memberships(client):
    _, owner_token = register_and_login(client, "Cascade Owner")
    member_id, _ = register_and_login(client, "Cascade Member")

    create_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"name": "Cascade Project"},
    )
    project_id = create_resp.json()["id"]

    # Add member
    add_resp = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"user_id": member_id, "role": "member"},
    )
    assert add_resp.status_code == 201

    # Delete project
    del_resp = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert del_resp.status_code == 204