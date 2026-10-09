from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.project_member import ProjectMember
from app.models.user import User
from app.repositories.project_member_repository import ProjectMemberRepository


from app.models.project_member import ProjectMember, ProjectRole

def get_project_member(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectMember:
    repository = ProjectMemberRepository(db)

    membership = repository.get_membership(
        project_id=project_id,
        user_id=current_user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    return membership





def require_project_role(*allowed_roles: ProjectRole):
    def role_checker(
        membership: ProjectMember = Depends(get_project_member),
    ) -> ProjectMember:

        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return membership

    return role_checker