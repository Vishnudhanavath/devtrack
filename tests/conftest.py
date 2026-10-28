import os
from dotenv import load_dotenv

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.rate_limiter import enforce_login_rate_limit
from app.db.database import get_db
from app.main import app

from urllib.parse import urlparse

import redis
import app.core.rate_limiter as rate_limiter

load_dotenv()

TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")
if not TEST_REDIS_URL:
    raise RuntimeError(
        "TEST_REDIS_URL is required for Redis integration tests."
    )
parsed_redis_url = urlparse(TEST_REDIS_URL)
if parsed_redis_url.scheme not in {"redis", "rediss"}:
    raise RuntimeError(
        "TEST_REDIS_URL must use the redis:// or rediss:// scheme."
    )
if not parsed_redis_url.hostname:
    raise RuntimeError(
        "TEST_REDIS_URL must specify a Redis hostname."
    )
if parsed_redis_url.path != "/1":
    raise RuntimeError(
        "Redis integration tests must use Redis database /1."
    )



# Require an explicit test database URL.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is required to run database tests."
    )

if not TEST_DATABASE_URL.endswith("/devtrack_test"):
    raise RuntimeError(
        "Tests must use the dedicated devtrack_test database."
    )

# Create a separate engine for automated tests.
test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db_session():
    """Provide an isolated database transaction for a test."""

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_redis_client(monkeypatch):
    """Provide an isolated Redis client for integration tests."""
    client = redis.Redis.from_url(
        TEST_REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    try:
        client.ping()
        # Make the real rate-limiter functions use the test Redis database.
        monkeypatch.setattr(
            rate_limiter,
            "redis_client",
            client,
        )
        yield client
    finally:
        client.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI client using the test database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[enforce_login_rate_limit] = lambda: None

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(enforce_login_rate_limit, None)











