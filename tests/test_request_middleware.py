import asyncio
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import RequestIDMiddleware


# Create an independent application for middleware testing.
test_app = FastAPI()

test_app.add_middleware(RequestIDMiddleware)


@test_app.get("/slow")
async def slow_endpoint():
    # Simulate a slow operation.
    await asyncio.sleep(0.65)

    return {"status": "ok"}


def test_slow_request_is_logged_as_warning(caplog):
    with caplog.at_level(
        logging.WARNING,
        logger="app.core.middleware",
    ):
        response = TestClient(test_app).get("/slow")

    # The endpoint should still succeed.
    assert response.status_code == 200

    # The middleware should return a request ID.
    assert response.headers.get("x-request-id")

    # The middleware should log the slow request.
    assert any(
        "Slow request" in record.getMessage()
        for record in caplog.records
    )