from datetime import datetime, timedelta, timezone
import jwt 

from app.core.config import settings

from pwdlib import PasswordHash


from fastapi.security import OAuth2PasswordBearer



password_hashing = PasswordHash.recommended()


def hash_password(password: str) -> str: 
    return password_hashing.hash(password)




def verify_password(
    password: str,
    hashed_password: str,
)->bool: 
    return password_hashing.verify(password, hashed_password)


def create_access_token(
        user_id: int 
) -> str: 
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    ) 

    payload = {
        "sub":str(user_id),
        "exp": expire 
    }


    return jwt.encode(
        payload,
        settings.jwt_secret_key, # secret key 
        algorithm= settings.jwt_algorithm, # HS256 jwt algo
    ) 


# from cilent we receives the auth header or token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

