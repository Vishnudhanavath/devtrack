from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.enums import UserRole

from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreate,
    UserPatch,
    UserResponse,
    UserUpdate,
    UserListResponse
)
from app.services.user_service import UserService
from app.dependencies.user import get_user_service

from app.dependencies.auth import get_current_user
import jwt
from pydantic import ValidationError
from app.core.config import settings
from app.models.user import User


from app.dependencies.auth import require_role
# app/api/v1/users.py
from typing import Literal

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)



# UserService
#     │
#     │ has
#     ▼
# UserRepository
#     │
#     │ has
#     ▼
# Database Session
#     │
#     ▼
# PostgreSQL




@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user: UserCreate,
    # db: Session = Depends(get_db) #session is created with get_db and passes endpoint function call 
    service: UserService = Depends(get_user_service),
):
    # repository = UserRepository(db)
    # service = UserService(repository)

    try:
        return service.create_user(user)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

# @router.get(
#     "",
#     response_model=UserListResponse
# )
# def get_users(
#     page: int = Query(default=1, ge=1),
#     page_size: int = Query(
#         default=20,
#         ge=1,
#         le=100
#     ),
#     name: str | None = Query(default=None),
#     sort_by: str = Query(
#         default="created_at"
#     ),
#     sort_order: str = Query(
#         default="desc"
#     ),
#     # db: Session = Depends(get_db),
#     service: UserService = Depends(get_user_service),
#     current_user: User = Depends(get_current_user)
# ):
    # repository = UserRepository(db)
    # service = UserService(repository)
@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    sort_by: Literal[
        "id",
        "name",
        "email",
        "created_at",
        "updated_at",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    try:
        users, total = service.get_users(
            page=page,
            page_size=page_size,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total_pages = (total + page_size - 1) // page_size

        return UserListResponse(
            item=users,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

@router.get(
    "/admin-check",
    tags=["Administration"],
)
def admin_check(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return {
        "message": "Welcome, administrator!",
        "user_id": current_user.id,
        "role": current_user.role,
    }

# get user by id 
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: int,
    request: Request,
    service: UserService = Depends(get_user_service),
):
    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        current_user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this user",
        )

    user = service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user 



# @router.put("/{user_id}", response_model=UserResponse)
# def update_user(
#     user_id:int,
#     user_data:UserUpdate,
#     # db:Session = Depends(get_db)
#     service: UserService = Depends(get_user_service),
# ):
#     # repository = UserRepository(db)
#     # service = UserService(repository) 


#     try:
#         user = service.update_user(user_id, user_data) 

#     except ValueError as error:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=str(error)
#         )

#     if user is None: 
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         ) 

#     return user 



@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: Request,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    # Authorization is checked before request body validation.
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this user",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON payload",
        )

    try:
        user_data = UserUpdate.model_validate(payload)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error.errors(),
        )

    try:
        user = service.update_user(user_id, user_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user




# @router.patch("/{user_id}", response_model= UserResponse) 

# def patch_user(
#     user_id:int,
#     user_data: UserPatch, 
#     # db:Session= Depends(get_db)
#     service: UserService = Depends(get_user_service),
# ):
#     # repository = UserRepository(db)
#     # service = UserService(repository)

#     try: 
#         user = service.patch_user(
#             user_id,
#             user_data
#         )
#     except ValueError as error: 
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=str(error)
#         )
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='user not found'
#         )

#     return user

@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: int,
    user_data: UserPatch,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    # Authorization: users can modify only their own account.
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this user",
        )

    try:
        user = service.patch_user(user_id, user_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


# @router.delete(
#     "/{user_id}",
#     status_code=status.HTTP_204_NO_CONTENT
# )
# def delete_user(
#     user_id: int,
#     # db: Session = Depends(get_db)
#     service: UserService = Depends(get_user_service),
# ):
#     # repository = UserRepository(db)
#     # service = UserService(repository)

#     deleted = service.delete_user(user_id)

#     if not deleted:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    # Authorization: users can delete only their own account.
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this user",
        )

    try:
        deleted = service.delete_user(user_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User cannot be deleted while they own projects",
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )










