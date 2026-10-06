from fastapi import Depends

from app.repositories.project_repository import ProjectRepository
from app.services.project_service import ProjectService
from app.db.database import get_db
from sqlalchemy.orm import Session


def get_project_repository(
    db: Session = Depends(get_db),
) -> ProjectRepository:

    return ProjectRepository(db)


def get_project_service(
    repository: ProjectRepository = Depends(
        get_project_repository
    ),
) -> ProjectService:

    return ProjectService(repository)