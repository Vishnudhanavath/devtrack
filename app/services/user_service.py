from app.schemas.user import UserCreate


users = [{
        "id": 1,
        "name": "Vishnu",
        "email": "vishnu@example.com"
    },
    {
        "id": 2,
        "name": "Rahul",
        "email": "rahul@example.com"
    }]


next_user_id = len(users)+1


def create_user(user: UserCreate):
    global next_user_id

    new_user = {
        "id": next_user_id,
        "name": user.name,
        "email": user.email
    }

    users.append(new_user)
    next_user_id += 1

    return new_user


def get_users():
    return users


def get_user_by_id(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user

    return None


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
