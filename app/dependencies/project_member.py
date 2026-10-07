from fastapi import Depends
from sqlalchemy.orm import Session 



from app.db.database import get_db
from app.repositories.project_member_repository import (
    ProjectMemberRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.services.project_member_service import ProjectMemberService 


def get_project_member_service(
    db: Session = Depends(get_db),
) -> ProjectMemberService:

    return ProjectMemberService(
        member_repository=ProjectMemberRepository(db),
        project_repository=ProjectRepository(db),
        user_repository=UserRepository(db),
    )


