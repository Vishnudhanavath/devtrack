from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer #This provides FastAPI's OAuth2 Bearer-token authentication helper.
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    repository = UserRepository(db)

    user = repository.get_by_id(
        int(user_id)
    )

    if user is None:
        raise credentials_exception

    return user




