import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions.base import AppException

# from sqlalchemy.exc import IntegrityError

# from app.core.exceptions.base import ResourceConflictError



logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:

    if exc.status_code >= 500:
        logger.error(
            "Application error while processing %s %s: %s",
            request.method,
            request.url.path,
            exc.message,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:

    if exc.status_code >= 500:
        logger.error(
            "HTTP server error while processing %s %s: status=%s",
            request.method,
            request.url.path,
            exc.status_code,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
        },
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled exception while processing %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred.",
        },
    )