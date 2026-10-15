from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService


def test_create_project_rolls_back_if_owner_membership_fails(db_session):
    # Arrange: create a user who will own the project.
    owner = User(
        name="Transaction Test User",
        email=f"transaction-{uuid4().hex}@example.com",
        password_hash="test-password-hash",
    )
    db_session.add(owner)
    db_session.flush()

    owner_id = owner.id

    repository = ProjectRepository(db_session)
    service = ProjectService(repository=repository, db=db_session)

    # Simulate a failure after the project has been inserted,
    # but before its owner membership is created.
    def fail_after_project_insert(project):
        db_session.add(project)
        db_session.flush()

        raise RuntimeError("Simulated owner membership failure")

    repository.create_with_owner = fail_after_project_insert

    project_data = ProjectCreate(
        name="Transaction Rollback Project",
        description="This project must not be persisted",
    )

    # Act: project creation should fail and roll back.
    with pytest.raises(
        RuntimeError,
        match="Simulated owner membership failure",
    ):
        service.create_project(
            project_data=project_data,
            owner_id=owner_id,
        )

    # Assert: the project must not exist after rollback.
    projects = db_session.scalars(
        select(Project).where(
            Project.name == "Transaction Rollback Project"
        )
    ).all()

    assert projects == []

    # Assert: no owner membership should exist either.
    memberships = db_session.scalars(
        select(ProjectMember).where(
            ProjectMember.user_id == owner_id
        )
    ).all()

    assert memberships == []