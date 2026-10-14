from uuid import uuid4


def register_and_login(client, name):
    """Register a user and return their access token and user ID."""

    email = f"user-{uuid4().hex}@example.com"
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

    user_id = registration.json()["id"]

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200, login.text

    return user_id, login.json()["access_token"]


def create_project(client, owner_token):
    """Create a project owned by the authenticated user."""

    response = client.post(
        "/api/v1/projects",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        json={
            "name": f"Test Project {uuid4().hex[:8]}",
            "description": "Project for authorization testing",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def add_project_member(
    client,
    project_id,
    owner_token,
    user_id,
    role="member",
):
    """Add a user to a project with the requested role."""

    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        json={
            "user_id": user_id,
            "role": role,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_member_cannot_change_project_role(client):
    # Arrange: create the project owner.
    owner_id, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Create a regular project member.
    member_id, member_token = register_and_login(
        client, "Regular Member"
    )

    add_project_member(
        client,
        project_id,
        owner_token,
        member_id,
    )

    # Create another member whose role might be changed.
    target_id, _ = register_and_login(
        client, "Target Member"
    )

    add_project_member(
        client,
        project_id,
        owner_token,
        target_id,
    )

    # Act: the regular member attempts to promote the target.
    response = client.patch(
        f"/api/v1/projects/{project_id}/members/{target_id}",
        headers={
            "Authorization": f"Bearer {member_token}",
        },
        json={
            "role": "manager",
        },
    )

    # Assert: only the owner can change project roles.
    assert response.status_code == 403


def test_manager_cannot_change_project_role(client):
    # Arrange: create a project and its owner.
    _, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Add a manager.
    manager_id, manager_token = register_and_login(
        client, "Project Manager"
    )

    add_project_member(
        client,
        project_id,
        owner_token,
        manager_id,
        role="manager",
    )

    # Add a regular member as the target.
    target_id, _ = register_and_login(
        client, "Target Member"
    )

    add_project_member(
        client,
        project_id,
        owner_token,
        target_id,
    )

    # Act: the manager attempts to promote the target.
    response = client.patch(
        f"/api/v1/projects/{project_id}/members/{target_id}",
        headers={
            "Authorization": f"Bearer {manager_token}",
        },
        json={
            "role": "manager",
        },
    )

    # Assert: managers cannot change member roles.
    assert response.status_code == 403


def test_owner_can_promote_member_to_manager(client):
    # Arrange: create a project and its owner.
    _, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Add a regular member.
    member_id, _ = register_and_login(
        client, "Regular Member"
    )

    add_project_member(
        client,
        project_id,
        owner_token,
        member_id,
    )

    # Act: the owner promotes the member.
    response = client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        json={
            "role": "manager",
        },
    )

    # Assert: the operation succeeds.
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] == member_id
    assert response.json()["role"] == "manager"


def test_cannot_add_same_member_twice(client):
    # Create the project owner.
    _, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Create a user to add to the project.
    member_id, _ = register_and_login(
        client, "Project Member"
    )

    # First addition should succeed.
    add_project_member(
        client,
        project_id,
        owner_token,
        member_id,
    )

    # Attempt to add the same user again.
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
        json={
            "user_id": member_id,
            "role": "member",
        },
    )

    assert response.status_code == 409



#Prevent project owners from removing themselves
def test_owner_cannot_remove_themselves(client):
    # Create a project owner.
    owner_id, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Attempt to remove the owner's own membership.
    response = client.delete(
        f"/api/v1/projects/{project_id}/members/{owner_id}",
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )

    assert response.status_code == 409, response.text 



#Verify that non-members cannot list project members
def test_non_member_cannot_list_project_members(client):
    # Create the project owner and project.
    _, owner_token = register_and_login(
        client, "Project Owner"
    )

    project_id = create_project(client, owner_token)

    # Create a separate user who is not a project member.
    _, outsider_token = register_and_login(
        client, "Project Outsider"
    )

    # The outsider attempts to list project members.
    response = client.get(
        f"/api/v1/projects/{project_id}/members",
        headers={
            "Authorization": f"Bearer {outsider_token}",
        },
    )

    assert response.status_code == 403


def test_owner_can_add_member(client):
    owner_id, owner_token = register_and_login(client, "Owner Adder")
    project_id = create_project(client, owner_token)
    member_id, _ = register_and_login(client, "New Member")

    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "user_id": member_id,
            "role": "member",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["project_id"] == project_id
    assert data["user_id"] == member_id
    assert data["role"] == "member"


def test_regular_member_cannot_add_member(client):
    owner_id, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    member_id, member_token = register_and_login(client, "Member User")
    add_project_member(client, project_id, owner_token, member_id)

    target_id, _ = register_and_login(client, "Target User")

    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {member_token}"},
        json={
            "user_id": target_id,
            "role": "member",
        },
    )

    assert response.status_code == 403


def test_manager_cannot_add_member(client):
    owner_id, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    manager_id, manager_token = register_and_login(client, "Manager User")
    add_project_member(client, project_id, owner_token, manager_id)

    # Promote to manager
    client.patch(
        f"/api/v1/projects/{project_id}/members/{manager_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "manager"},
    )

    target_id, _ = register_and_login(client, "Target User")

    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "user_id": target_id,
            "role": "member",
        },
    )

    assert response.status_code == 403


def test_add_member_user_not_found(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "user_id": 999999,
            "role": "member",
        },
    )

    assert response.status_code == 404


def test_add_member_project_not_found(client):
    _, owner_token = register_and_login(client, "Owner User")
    member_id, _ = register_and_login(client, "Member User")

    response = client.post(
        "/api/v1/projects/999999/members",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "user_id": member_id,
            "role": "member",
        },
    )

    assert response.status_code == 404


def test_owner_can_remove_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    member_id, _ = register_and_login(client, "Member User")
    add_project_member(client, project_id, owner_token, member_id)

    response = client.delete(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 204

    # Verify member is no longer in member list
    list_resp = client.get(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_resp.status_code == 200
    member_ids = [m["user_id"] for m in list_resp.json()]
    assert member_id not in member_ids


def test_regular_member_cannot_remove_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    member1_id, member1_token = register_and_login(client, "Member 1")
    member2_id, _ = register_and_login(client, "Member 2")
    add_project_member(client, project_id, owner_token, member1_id)
    add_project_member(client, project_id, owner_token, member2_id)

    response = client.delete(
        f"/api/v1/projects/{project_id}/members/{member2_id}",
        headers={"Authorization": f"Bearer {member1_token}"},
    )

    assert response.status_code == 403


def test_manager_cannot_remove_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    manager_id, manager_token = register_and_login(client, "Manager User")
    add_project_member(client, project_id, owner_token, manager_id)
    client.patch(
        f"/api/v1/projects/{project_id}/members/{manager_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "manager"},
    )

    member_id, _ = register_and_login(client, "Member User")
    add_project_member(client, project_id, owner_token, member_id)

    response = client.delete(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 403


def test_remove_nonexistent_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    outsider_id, _ = register_and_login(client, "Outsider User")

    response = client.delete(
        f"/api/v1/projects/{project_id}/members/{outsider_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 404


def test_owner_can_demote_manager_to_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    member_id, _ = register_and_login(client, "Member To Promote Demote")
    add_project_member(client, project_id, owner_token, member_id)

    # Promote to manager
    promo_resp = client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "manager"},
    )
    assert promo_resp.status_code == 200
    assert promo_resp.json()["role"] == "manager"

    # Demote back to member
    demote_resp = client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "member"},
    )
    assert demote_resp.status_code == 200
    assert demote_resp.json()["role"] == "member"


def test_update_role_nonexistent_member(client):
    _, owner_token = register_and_login(client, "Owner User")
    project_id = create_project(client, owner_token)

    outsider_id, _ = register_and_login(client, "Outsider User")

    response = client.patch(
        f"/api/v1/projects/{project_id}/members/{outsider_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "manager"},
    )

    assert response.status_code == 404


def test_owner_and_members_can_list_project_members(client):
    owner_id, owner_token = register_and_login(client, "List Owner")
    project_id = create_project(client, owner_token)

    member_id, member_token = register_and_login(client, "List Member")
    add_project_member(client, project_id, owner_token, member_id)

    # Owner lists members
    owner_resp = client.get(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_resp.status_code == 200
    members = owner_resp.json()
    assert len(members) >= 2
    u_ids = [m["user_id"] for m in members]
    assert owner_id in u_ids
    assert member_id in u_ids

    # Member lists members
    member_resp = client.get(
        f"/api/v1/projects/{project_id}/members",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert member_resp.status_code == 200
    m_ids = [m["user_id"] for m in member_resp.json()]
    assert owner_id in m_ids
    assert member_id in m_ids






