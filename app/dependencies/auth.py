from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.core.config import settings
from app.dependencies.user import get_user_repository
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

from app.models.enums import UserRole


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


#login 
def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)



#dependency verifies the token and returns the authenticated user.
def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = int(payload["sub"])

    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise credentials_exception

    user = repository.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: UserRole):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker 




#---------------------------------- EXPLAINATION -------------------

# 2. Understand the difference between these functions
# get_auth_service() — during login
# POST /api/v1/auth/login
#           ↓
#       Auth Router
#           ↓
#     get_auth_service()
#           ↓
#       AuthService
#           ↓
#     UserRepository
#           ↓
#       PostgreSQL

# The service checks the email and password and creates an access token.

# get_current_user() — for protected endpoints
# Client sends JWT
#         ↓
# OAuth2PasswordBearer extracts token
#         ↓
# jwt.decode() validates token signature and expiration
#         ↓
# Extract user ID from "sub"
#         ↓
# Look up user in PostgreSQL
#         ↓
# Return authenticated User object

# For example, a protected endpoint can request the current user like this:

# current_user: User = Depends(get_current_user)

# FastAPI automatically executes the dependency before calling the endpoint.