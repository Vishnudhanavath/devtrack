from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.dependencies.project_member import get_project_member_service
from app.models.user import User
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from app.services.project_member_service import ProjectMemberService


router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["Project Members"],
)


def raise_service_error(error: Exception) -> None:
    if isinstance(error, PermissionError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    if isinstance(error, LookupError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    if isinstance(error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    raise error


@router.post(
    "",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectMemberService = Depends(
        get_project_member_service
    ),
):
    try:
        return service.add_member(
            project_id=project_id,
            member_data=member_data,
            current_user_id=current_user.id,
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise_service_error(error)


@router.get(
    "",
    response_model=list[ProjectMemberResponse],
)
def get_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectMemberService = Depends(
        get_project_member_service
    ),
):
    try:
        return service.get_members(
            project_id=project_id,
            current_user_id=current_user.id,
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise_service_error(error)


@router.patch(
    "/{user_id}",
    response_model=ProjectMemberResponse,
)
def update_project_member(
    project_id: int,
    user_id: int,
    member_data: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectMemberService = Depends(
        get_project_member_service
    ),
):
    try:
        return service.update_member_role(
            project_id=project_id,
            user_id=user_id,
            new_role=member_data.role,
            current_user_id=current_user.id,
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise_service_error(error)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectMemberService = Depends(
        get_project_member_service
    ),
):
    try:
        service.remove_member(
            project_id=project_id,
            user_id=user_id,
            current_user_id=current_user.id,
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise_service_error(error)








