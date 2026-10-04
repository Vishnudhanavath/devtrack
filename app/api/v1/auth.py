from fastapi import APIRouter, HTTPException,status, Depends



from app.core.security import (
    create_access_token,
    verify_password,
) 

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.user_service import UserService 
from app.dependencies.user import get_user_service 


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/login",response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    service: UserService = Depends(get_user_service)
    ):

    user = service.repository.get_by_email(login_data.email)

    if user is None: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
         raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid email or password",
         )
    
    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }









