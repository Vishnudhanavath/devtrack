import logging
import pytest

from fastapi import HTTPException
from fastapi import Request

from redis.exceptions import RedisError

from app.core.config import settings

from app.core.rate_limiter import (
    enforce_login_rate_limit,
    enforce_account_login_rate_limit,
    record_failed_login_attempt,
    reset_failed_login_attempts,
    LOGIN_ATTEMPT_LIMIT,
)


def create_request(client_ip: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [],
        "client": (client_ip, 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
    }

    return Request(scope)


def test_login_attempt_within_limit_is_allowed(monkeypatch):
    request = create_request()

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        lambda *args: [LOGIN_ATTEMPT_LIMIT, 60],
    )

    # Should finish without raising HTTPException.
    enforce_login_rate_limit(request)


def test_exceeding_login_limit_returns_429(monkeypatch):
    request = create_request()

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        lambda *args: [LOGIN_ATTEMPT_LIMIT + 1, 45],
    )

    with pytest.raises(HTTPException) as exc_info:
        enforce_login_rate_limit(request)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == "45"


def test_redis_failure_returns_503(monkeypatch):
    request = create_request()

    def raise_redis_error(*args):
        raise RedisError("Redis unavailable")

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        raise_redis_error,
    )

    with pytest.raises(HTTPException) as exc_info:
        enforce_login_rate_limit(request)

    assert exc_info.value.status_code == 503
    assert exc_info.value.headers["Retry-After"] == "5"


def test_each_client_ip_gets_a_separate_key(monkeypatch):
    request = create_request("192.0.2.10")
    captured = {}

    def fake_eval(script, number_of_keys, key, window_seconds):
        captured["key"] = key
        captured["window_seconds"] = window_seconds
        return [1, 60]

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        fake_eval,
    )

    enforce_login_rate_limit(request)

    assert captured["key"] == "rate-limit:login:192.0.2.10"
    assert captured["window_seconds"] == 60


def test_exceeding_limit_logs_warning(monkeypatch, caplog):
    request = create_request("192.0.2.25")

    def fake_eval(*args):
        return [
            settings.login_rate_limit_attempts + 1,
            45,
        ]

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        fake_eval,
    )

    with caplog.at_level(
        logging.WARNING,
        logger="app.core.rate_limiter",
    ):
        with pytest.raises(HTTPException) as exc_info:
            enforce_login_rate_limit(request)

    assert exc_info.value.status_code == 429
    assert any(
        "Login rate limit exceeded" in record.getMessage()
        for record in caplog.records
    )
    assert any(
        "192.0.2.25" in record.getMessage()
        for record in caplog.records
    )



def test_account_limit_allows_attempts_below_limit(monkeypatch):
    request = create_request()
    captured = {}

    def fake_get(key):
        captured["key"] = key
        return "2"

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.get",
        fake_get,
    )

    enforce_account_login_rate_limit(
        email="User@example.com",
        request=request,
    )

    # The actual email must not appear in the Redis key.
    assert "User@example.com" not in captured["key"]
    assert captured["key"].startswith(
        "rate-limit:login-failure:"
    )


def test_account_limit_returns_429_at_limit(monkeypatch):
    request = create_request()

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.get",
        lambda key: str(LOGIN_ATTEMPT_LIMIT),
    )

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.ttl",
        lambda key: 30,
    )

    with pytest.raises(HTTPException) as exc_info:
        enforce_account_login_rate_limit(
            email="user@example.com",
            request=request,
        )

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == "30"


def test_record_failed_login_attempt_increments_counter(monkeypatch):
    request = create_request()
    captured = {}

    def fake_eval(script, number_of_keys, key, window_seconds):
        captured["key"] = key
        captured["window_seconds"] = window_seconds
        return [1, window_seconds]

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.eval",
        fake_eval,
    )

    record_failed_login_attempt(
        email="user@example.com",
        request=request,
    )

    assert captured["key"].startswith(
        "rate-limit:login-failure:"
    )
    assert captured["window_seconds"] == (
        settings.login_rate_limit_window_seconds
    )


def test_successful_login_resets_failure_counter(monkeypatch):
    request = create_request()
    captured = {}

    def fake_delete(key):
        captured["key"] = key
        return 1

    monkeypatch.setattr(
        "app.core.rate_limiter.redis_client.delete",
        fake_delete,
    )

    reset_failed_login_attempts(
        email="user@example.com",
        request=request,
    )

    assert captured["key"].startswith(
        "rate-limit:login-failure:"
    )