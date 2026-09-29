# from app.schemas.user import UserCreate

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(user_data.email)

        if existing_user:
            raise ValueError("Email already exists")

        user = User(
            name=user_data.name,
            email=user_data.email
        )

        return self.repository.create(user) 
        

    def get_users(self) -> list[User]:
        return self.repository.get_all()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)




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
