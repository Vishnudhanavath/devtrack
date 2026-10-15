import logging
import time
import uuid

from app.core.request_context import request_id_var
from app.core.config import settings

logger = logging.getLogger(__name__)

# SLOW_REQUEST_THRESHOLD_MS = 500.0


class RequestIDMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        # Pass non-HTTP traffic through unchanged.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)

        scope.setdefault("state", {})["request_id"] = request_id

        method = scope["method"]
        path = scope["path"]

        start_time = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message):

            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]

                headers.append(
                    (
                        b"x-request-id",
                        request_id.encode("ascii"),
                    )
                )

                message["headers"] = headers

            await send(message)

        try:
            logger.info(
                "Request started method=%s path=%s",
                method,
                path,
            )

            await self.app(
                scope,
                receive,
                send_with_request_id,
            )

        except Exception:
            logger.exception(
                "Request failed method=%s path=%s",
                method,
                path,
            )
            raise

        finally:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            if duration_ms >= settings.slow_request_threshold_ms:
                logger.warning(
                    "Slow request method=%s path=%s "
                    "status_code=%s duration_ms=%.2f "
                    "threshold_ms=%.2f",
                    method,
                    path,
                    status_code,
                    duration_ms,
                   settings.slow_request_threshold_ms,
                )
            else:
                logger.info(
                    "Request completed method=%s path=%s "
                    "status_code=%s duration_ms=%.2f",
                    method,
                    path,
                    status_code,
                    duration_ms,
                )

            request_id_var.reset(token)