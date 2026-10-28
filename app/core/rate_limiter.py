import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis_client import redis_client


logger = logging.getLogger(__name__)

LOGIN_ATTEMPT_LIMIT = settings.login_rate_limit_attempts
LOGIN_WINDOW_SECONDS = settings.login_rate_limit_window_seconds


INCREMENT_ATTEMPT_SCRIPT = """
local count = redis.call("INCR", KEYS[1])

if count == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {count, ttl}
"""


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _get_account_attempt_key(email: str, client_ip: str) -> str:
    normalized_email = email.strip().lower()

    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        normalized_email.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"rate-limit:login-failure:{digest}:{client_ip}"


def enforce_login_rate_limit(request: Request) -> None:
    """Apply a general login-request limit per client IP."""
    client_ip = _get_client_ip(request)
    redis_key = f"rate-limit:login:{client_ip}"

    try:
        result = redis_client.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            redis_key,
            LOGIN_WINDOW_SECONDS,
        )
    except RedisError as exc:
        logger.error("Redis unavailable while checking login IP limit")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service is temporarily unavailable.",
            headers={"Retry-After": "5"},
        ) from exc

    attempt_count = int(result[0])
    ttl = max(int(result[1]), 1)

    if attempt_count > LOGIN_ATTEMPT_LIMIT:
        logger.warning(
            "Login rate limit exceeded client_ip=%s "
            "attempt_count=%s retry_after_seconds=%s",
            client_ip,
            attempt_count,
            ttl,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(ttl)},
        )


def enforce_account_login_rate_limit(
    email: str,
    request: Request,
) -> None:
    """Block further attempts after too many failures for an account/IP pair."""
    client_ip = _get_client_ip(request)
    redis_key = _get_account_attempt_key(email, client_ip)

    try:
        attempt_count = int(redis_client.get(redis_key) or 0)

        if attempt_count >= LOGIN_ATTEMPT_LIMIT:
            ttl = max(int(redis_client.ttl(redis_key)), 1)

            logger.warning(
                "Account login failure limit reached client_ip=%s "
                "retry_after_seconds=%s",
                client_ip,
                ttl,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(ttl)},
            )

    except RedisError as exc:
        logger.error("Redis unavailable while checking account login limit")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service is temporarily unavailable.",
            headers={"Retry-After": "5"},
        ) from exc


def record_failed_login_attempt(
    email: str,
    request: Request,
) -> None:
    """Record an unsuccessful login for an account/IP pair."""
    client_ip = _get_client_ip(request)
    redis_key = _get_account_attempt_key(email, client_ip)

    try:
        result = redis_client.eval(
            INCREMENT_ATTEMPT_SCRIPT,
            1,
            redis_key,
            LOGIN_WINDOW_SECONDS,
        )
    except RedisError as exc:
        logger.error("Redis unavailable while recording failed login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service is temporarily unavailable.",
            headers={"Retry-After": "5"},
        ) from exc

    attempt_count = int(result[0])

    logger.info(
        "Failed login recorded client_ip=%s attempt_count=%s",
        client_ip,
        attempt_count,
    )


def reset_failed_login_attempts(
    email: str,
    request: Request,
) -> None:
    """Clear the account/IP failure counter after successful authentication."""
    client_ip = _get_client_ip(request)
    redis_key = _get_account_attempt_key(email, client_ip)

    try:
        redis_client.delete(redis_key)
    except RedisError as exc:
        logger.error("Redis unavailable while resetting failed login counter")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service is temporarily unavailable.",
            headers={"Retry-After": "5"},
        ) from exc