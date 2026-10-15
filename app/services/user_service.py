from logging import error

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserPatch, UserUpdate
from app.core.security import hash_password

from sqlalchemy.exc import IntegrityError

from app.core.exceptions.base import ResourceConflictError



class UserService:

    def __init__(self, repository: UserRepository, db: Session):
        self.repository = repository
        self.db = db


    def _handle_integrity_error(self, error: IntegrityError) -> None:
        self.db.rollback()

        original_error = error.orig

        sqlstate = (
            getattr(original_error, "sqlstate", None)
            or getattr(original_error, "pgcode", None)
        )

        diagnostic = getattr(original_error, "diag", None)

        constraint_name = getattr(
            diagnostic,
            "constraint_name",
            None,
        )

        if (
            sqlstate == "23505"
            and constraint_name == "ix_users_email"
        ):
            raise ResourceConflictError(
                "Email already exists"
            ) from error

        raise error

    # def create_user(self, user_data: UserCreate) -> User:
    #     existing_user = self.repository.get_by_email(user_data.email)

    #     if existing_user:
    #         raise ValueError("Email already exists")
        
    #     hashed_password = hash_password(user_data.password)

    #     user = User(
    #         name=user_data.name,
    #         email=user_data.email,
    #         password_hash=hashed_password,
    #     )

    #     try:
    #         user = self.repository.create(user)
    #         self.db.commit()
    #         self.db.refresh(user)
    #         return user
    #     except Exception:
    #         self.db.rollback()
    #         raise
    def create_user(self, user_data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(user_data.email)

        if existing_user:
            raise ValueError("Email already exists")

        hashed_password = hash_password(user_data.password)

        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
        )

        try:
            user = self.repository.create(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except IntegrityError as error:
            self.db.rollback()

            original_error = error.orig

            sqlstate = (
                getattr(original_error, "sqlstate", None)
                or getattr(original_error, "pgcode", None)
            )

            diagnostic = getattr(original_error, "diag", None)
            constraint_name = getattr(
                diagnostic,
                "constraint_name",
                None,
            )

            if (
                sqlstate == "23505"
                and constraint_name == "ix_users_email"
            ):
                raise ResourceConflictError(
                    "Email already exists"
                ) from error

            raise

        except Exception:
            self.db.rollback()
            raise
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
        user_data: UserUpdate,
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

        try:
            user = self.repository.update(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as error:
            self._handle_integrity_error(error)


        except Exception:
            self.db.rollback()
            raise





    def patch_user(
        self,
        user_id: int,
        user_data: UserPatch,
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

        try:
            user = self.repository.update(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except IntegrityError as error:
            self._handle_integrity_error(error)

        except Exception:
            self.db.rollback()
            raise




    def delete_user(self, user_id: int) -> bool:
        user = self.repository.get_by_id(user_id)

        if user is None:
            return False

        try:
            self.repository.delete(user)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise







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









