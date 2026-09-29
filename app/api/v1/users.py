from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.create_user(user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.get(
    "",
    response_model=list[UserResponse]
)
def get_users(
    db: Session = Depends(get_db)
):
    repository = UserRepository(db)
    service = UserService(repository)

    return service.get_users()


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    repository = UserRepository(db)
    service = UserService(repository)

    user = service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user