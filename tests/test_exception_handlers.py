import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.testclient import TestClient
import pytest

from app.core.exceptions.base import AppException, ResourceNotFoundError
from app.main import app

# Register test routes to trigger each type of exception
test_router = APIRouter(prefix="/test-handlers", tags=["Test Handlers"])


@test_router.get("/app-exception")
def route_app_exception():
    raise ResourceNotFoundError("Test resource could not be found")


@test_router.get("/http-exception")
def route_http_exception():
    raise HTTPException(
        status_code=401,
        detail="Unauthorized test request",
        headers={"WWW-Authenticate": "Bearer"},
    )


@test_router.get("/validation-query")
def route_validation_query(page: int = Query(default=1, ge=1)):
    return {"page": page}


@test_router.get("/unexpected-exception")
def route_unexpected_exception():
    raise RuntimeError("Unexpected internal crash for testing")


app.include_router(test_router)


def test_app_exception_handler(client):
    response = client.get("/test-handlers/app-exception")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Test resource could not be found",
    }


def test_http_exception_handler_preserves_status_detail_and_headers(client):
    response = client.get("/test-handlers/http-exception")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Unauthorized test request",
    }
    assert response.headers.get("www-authenticate") == "Bearer"


def test_validation_exception_handler_format(client):
    # Calling endpoint with invalid query parameter page=-1
    response = client.get("/test-handlers/validation-query?page=-1")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0

    first_error = data["detail"][0]
    assert "field" in first_error
    assert "message" in first_error
    assert "type" in first_error
    assert "page" in first_error["field"]


def test_validation_exception_handler_on_registration(client):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "",
            "email": "invalid-email-address",
            "password": "short",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) >= 1

    for error in data["detail"]:
        assert "field" in error
        assert "message" in error
        assert "type" in error


def test_unexpected_exception_handler_returns_generic_500(caplog):
    # TestClient with raise_server_exceptions=False receives the 500 JSONResponse
    with caplog.at_level(logging.ERROR):
        safe_client = TestClient(app, raise_server_exceptions=False)
        response = safe_client.get("/test-handlers/unexpected-exception")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected server error occurred.",
    }
    # Verify the unhandled exception was logged
    assert any("Unhandled exception" in record.message for record in caplog.records)

