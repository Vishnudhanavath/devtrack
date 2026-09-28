from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserResponse 

#A router groups related API endpoints.
from app.services.user_service import (
    create_user,
    get_user_by_id,
    get_users,
)
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user_endpoint(user: UserCreate):
    return create_user(user)


@router.get(
    "",
    response_model=list[UserResponse]
)
def get_users_endpoint():
    return get_users()


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user_endpoint(user_id: int):
    user = get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user