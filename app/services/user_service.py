from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserPatch, UserUpdate
from app.core.security import hash_password


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(user_data.email)

        if existing_user:
            raise ValueError("Email already exists")
        
        hashed_password = hash_password(user_data.password)

        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash = hashed_password
        )
        return self.repository.create(user)

    def get_users(              
    self,
    page: int = 1,
    page_size: int = 20,
    name: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
                  
    ) -> tuple[list[User], int]:
        return self.repository.get_all(
            page=page,
            page_size=page_size,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ) -> User | None:

        user = self.repository.get_by_id(user_id)

        if user is None:
            return None

        existing_user = self.repository.get_by_email(
            user_data.email
        )

        if existing_user and existing_user.id != user_id:
            raise ValueError("Email already exists")

        user.name = user_data.name
        user.email = user_data.email

        return self.repository.update(user)

    def patch_user(
        self,
        user_id: int,
        user_data: UserPatch
    ) -> User | None:

        user = self.repository.get_by_id(user_id)

        if user is None:
            return None

        if user_data.email is not None:
            existing_user = self.repository.get_by_email(
                user_data.email
            )

            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already exists")

        if user_data.name is not None:
            user.name = user_data.name

        if user_data.email is not None:
            user.email = user_data.email

        return self.repository.update(user)

    def delete_user(self, user_id: int) -> bool:
        user = self.repository.get_by_id(user_id)

        if user is None:
            return False

        self.repository.delete(user)

        return True






# ----------alembic: ------------------

# We'll use Alembic for database schema changes.

# That gives us version-controlled database changes.




# -------------- sqlalchemy: -----------------
#it help pythong application to communicate with the database
    #  sqlalchemy has: 
        # |Engine
        # Session
        # Model
        # ORM
        # Query
        # Transaction
        # Connection Pool

# 1. engine:
        #  think it as  python application and database connectivity setup.
            # FastAPI application
            #         │
            #         ▼
            #     SQLAlchemy
            #         │
            #         Engine
            #         │
            #         ▼
            #     PostgreSQL



            # SQLAlchemy
            #     ↓
            # Python database toolkit / ORM

            # psycopg
            #     ↓
            # PostgreSQL driver

            # Alembic
            #     ↓
            # Database migrations


# SQLAlchemy = higher-level database toolkit

# psycopg = PostgreSQL communication driver









