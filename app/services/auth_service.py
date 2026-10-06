from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User | None:

        user = self.repository.get_by_email(email)

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user

    def create_access_token(
        self,
        user: User,
    ) -> str:

        return create_access_token(user.id)


    