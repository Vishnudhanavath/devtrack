from fastapi import APIRouter, Depends, HTTPException, status,Query
from sqlalchemy.orm import Session

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
from app.models.user import User

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

@router.get(
    "",
    response_model=UserListResponse
)
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    name: str | None = Query(default=None),
    sort_by: str = Query(
        default="created_at"
    ),
    sort_order: str = Query(
        default="desc"
    ),
    # db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    # repository = UserRepository(db)
    # service = UserService(repository)

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

# get user by id 
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    # db: Session = Depends(get_db)
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    # repository = UserRepository(db)
    # service = UserService(repository)

    user = service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user 



@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id:int,
    user_data:UserUpdate,
    # db:Session = Depends(get_db)
    service: UserService = Depends(get_user_service),
):
    # repository = UserRepository(db)
    # service = UserService(repository) 


    try:
        user = service.update_user(user_id, user_data) 

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    if user is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        ) 

    return user 


@router.patch("/{user_id}", response_model= UserResponse) 

def patch_user(
    user_id:int,
    user_data: UserPatch, 
    # db:Session= Depends(get_db)
    service: UserService = Depends(get_user_service),
):
    # repository = UserRepository(db)
    # service = UserService(repository)

    try: 
        user = service.patch_user(
            user_id,
            user_data
        )
    except ValueError as error: 
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found'
        )

    return user




@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(
    user_id: int,
    # db: Session = Depends(get_db)
    service: UserService = Depends(get_user_service),
):
    # repository = UserRepository(db)
    # service = UserService(repository)

    deleted = service.delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )



