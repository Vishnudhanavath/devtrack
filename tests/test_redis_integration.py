import os
import uuid

import pytest
import redis
from dotenv import load_dotenv

from app.core.rate_limiter import (
    INCREMENT_ATTEMPT_SCRIPT,
    LOGIN_WINDOW_SECONDS,
)


load_dotenv()

TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")


if not TEST_REDIS_URL:
    raise RuntimeError(
        "TEST_REDIS_URL must be configured to run Redis integration tests."
    )

if not TEST_REDIS_URL.endswith("/1"):
    raise RuntimeError(
        "Redis integration tests must use Redis database 1."
    )


@pytest.fixture
def test_redis():
    client = redis.Redis.from_url(
        TEST_REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        client.ping()
        yield client
    finally:
        client.close()


def test_lua_script_increments_counter(test_redis):
    key = f"test:rate-limit:{uuid.uuid4()}"

    try:
        first_result = test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            key,
            LOGIN_WINDOW_SECONDS,
        )

        second_result = test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            key,
            LOGIN_WINDOW_SECONDS,
        )

        assert int(first_result[0]) == 1
        assert int(second_result[0]) == 2

    finally:
        test_redis.delete(key)


def test_lua_script_sets_expiry(test_redis):
    key = f"test:rate-limit:{uuid.uuid4()}"

    try:
        test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            key,
            LOGIN_WINDOW_SECONDS,
        )

        ttl = test_redis.ttl(key)

        assert 0 < ttl <= LOGIN_WINDOW_SECONDS

    finally:
        test_redis.delete(key)


def test_different_keys_have_independent_counters(test_redis):
    first_key = f"test:rate-limit:{uuid.uuid4()}"
    second_key = f"test:rate-limit:{uuid.uuid4()}"

    try:
        test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            first_key,
            LOGIN_WINDOW_SECONDS,
        )

        test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            first_key,
            LOGIN_WINDOW_SECONDS,
        )

        test_redis.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            second_key,
            LOGIN_WINDOW_SECONDS,
        )

        assert test_redis.get(first_key) == "2"
        assert test_redis.get(second_key) == "1"

    finally:
        test_redis.delete(first_key, second_key)