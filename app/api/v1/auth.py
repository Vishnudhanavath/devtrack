# from fastapi import APIRouter, Depends, HTTPException, status,Request

# from app.dependencies.auth import get_auth_service
# from app.schemas.auth import LoginRequest, TokenResponse
# from app.services.auth_service import AuthService
# from fastapi.security import OAuth2PasswordRequestForm
# from app.core.rate_limiter import enforce_login_rate_limit

# router = APIRouter(
#     prefix="/auth",
#     tags=["Authentication"],
# )


# @router.post(
#     "/login",
#     response_model=TokenResponse,
#     dependencies=[Depends(enforce_login_rate_limit)],
# )
# def login(
#     login_data: LoginRequest,
#     # login_data: OAuth2PasswordRequestForm = Depends(),
#     service: AuthService = Depends(get_auth_service),
# ):
#     user = service.authenticate_user(
#         email=login_data.email,
#         password=login_data.password,
#     )

#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     access_token = service.create_access_token(user)

#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#     }


from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limiter import (
    enforce_account_login_rate_limit,
    enforce_login_rate_limit,
    record_failed_login_attempt,
    reset_failed_login_attempts,
)
from app.dependencies.auth import get_auth_service
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_login_rate_limit)],
)
def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    # Check whether this account/IP combination has too many failures.
    enforce_account_login_rate_limit(
        email=login_data.email,
        request=request,
    )

    user = service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
    )

    if user is None:
        # Record the failure, then return the usual generic 401 response.
        record_failed_login_attempt(
            email=login_data.email,
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # A successful login clears this account/IP failure counter.
    reset_failed_login_attempts(
        email=login_data.email,
        request=request,
    )

    access_token = service.create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }



