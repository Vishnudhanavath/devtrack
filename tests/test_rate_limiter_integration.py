from uuid import uuid4

import app.core.rate_limiter as rate_limiter
from app.core.rate_limiter import (
    LOGIN_ATTEMPT_LIMIT,
    LOGIN_WINDOW_SECONDS,
    _get_account_attempt_key,
    enforce_login_rate_limit,
)
from app.main import app


def test_login_api_blocks_repeated_failed_attempts(
    client,
    test_redis_client,
):
    # Arrange: create a unique account for this test.
    email = f"{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration_response = client.post(
        "/api/v1/users",
        json={
            "name": "Rate Limit Integration User",
            "email": email,
            "password": password,
        },
    )

    assert registration_response.status_code == 201

    # TestClient uses "testclient" as its default client host.
    redis_key = _get_account_attempt_key(email, "testclient")

    # Remove only this test's key before starting.
    test_redis_client.delete(redis_key)

    try:
        # Act: submit the maximum allowed number of failed logins.
        for attempt in range(LOGIN_ATTEMPT_LIMIT):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": "DefinitelyWrongPassword123!",
                },
            )

            assert response.status_code == 401
            assert response.json()["detail"] == (
                "Invalid email or password"
            )

        # Assert: Redis recorded each failed login.
        assert int(test_redis_client.get(redis_key)) == (
            LOGIN_ATTEMPT_LIMIT
        )

        # The next attempt should be blocked before authentication.
        blocked_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert blocked_response.status_code == 429
        assert blocked_response.json()["detail"] == (
            "Too many login attempts. Please try again later."
        )
        assert "Retry-After" in blocked_response.headers

    finally:
        # Clean up only the key created for this test.
        test_redis_client.delete(redis_key)


def test_successful_login_resets_account_failure_counter(
    client,
    test_redis_client,
):
    # Arrange: create a unique account.
    email = f"{uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration_response = client.post(
        "/api/v1/users",
        json={
            "name": "Successful Login Integration User",
            "email": email,
            "password": password,
        },
    )

    assert registration_response.status_code == 201

    redis_key = _get_account_attempt_key(email, "testclient")

    try:
        # Simulate previous failed login attempts.
        test_redis_client.set(
            redis_key,
            LOGIN_ATTEMPT_LIMIT - 1,
            ex=60,
        )

        # Act: authenticate with the correct password.
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        # Assert: login succeeds.
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]

        # Successful authentication must clear the counter.
        assert test_redis_client.exists(redis_key) == 0

    finally:
        test_redis_client.delete(redis_key)


def test_login_api_enforces_ip_rate_limit(
    client,
    test_redis_client,
    monkeypatch,
):
    from uuid import uuid4

    # Use a unique IP-like identifier to isolate this test's Redis key.
    test_ip = f"integration-test-{uuid4().hex}"
    redis_key = f"rate-limit:login:{test_ip}"

    # Make the real limiter use our unique test identifier.
    monkeypatch.setattr(
        rate_limiter,
        "_get_client_ip",
        lambda request: test_ip,
    )

    # Temporarily remove the fixture's bypass of the IP limiter.
    existing_override = app.dependency_overrides.pop(
        enforce_login_rate_limit,
        None,
    )

    try:
        # Seed the counter at the limit.
        test_redis_client.set(
            redis_key,
            LOGIN_ATTEMPT_LIMIT,
            ex=LOGIN_WINDOW_SECONDS,
        )

        # Send a request through the real login endpoint.
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"{uuid4().hex}@example.com",
                "password": "StrongPassword123!",
            },
        )

        # The real IP limiter increments the counter and blocks the request.
        assert response.status_code == 429
        assert response.json()["detail"] == (
            "Too many login attempts. Please try again later."
        )
        assert "Retry-After" in response.headers

        # The counter should have increased from the configured limit.
        assert int(test_redis_client.get(redis_key)) == (
            LOGIN_ATTEMPT_LIMIT + 1
        )

    finally:
        # Restore the ordinary test-client behavior.
        if existing_override is not None:
            app.dependency_overrides[
                enforce_login_rate_limit
            ] = existing_override

        # Delete only this test's Redis key.
        test_redis_client.delete(redis_key)



