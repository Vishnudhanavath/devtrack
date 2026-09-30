from sqlalchemy import select, asc, desc, func
from sqlalchemy.orm import Session
from app.models.user import User 



class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception:
            self.db.rollback()
            raise

    def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:

        # -------------------------
        # Base query
        # -------------------------

        statement = select(User)

        # -------------------------
        # Filtering
        # -------------------------

        if name:
            statement = statement.where(
                User.name.ilike(f"%{name}%")
            )

        # -------------------------
        # Count query
        # -------------------------

        count_statement = select(
            func.count()
        ).select_from(User)

        if name:
            count_statement = count_statement.where(
                User.name.ilike(f"%{name}%")
            )

        total = self.db.scalar(count_statement) or 0

        # -------------------------
        # Sorting
        # -------------------------

        allowed_sort_fields = {
            "id": User.id,
            "name": User.name,
            "email": User.email,
            "created_at": User.created_at,
            "updated_at": User.updated_at,
        }

        sort_column = allowed_sort_fields.get(sort_by)

        if sort_column is None:
            raise ValueError("Invalid sort field")

        if sort_order == "asc":
            statement = statement.order_by(
                asc(sort_column)
            )
        else:
            statement = statement.order_by(
                desc(sort_column)
            )

        # -------------------------
        # Pagination
        # -------------------------

        offset = (page - 1) * page_size

        statement = (
            statement
            .offset(offset)
            .limit(page_size)
        )

        result = self.db.scalars(statement)

        users = result.all()

        return users, total

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(
            User.id == user_id
        )

        return self.db.scalars(statement).first()

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(
            User.email == email
        )

        return self.db.scalars(statement).first()

    def update(self, user: User) -> User:
        try:
            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception:
            self.db.rollback()
            raise

    def delete(self, user: User) -> None:
        try:
            self.db.delete(user)
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise 







