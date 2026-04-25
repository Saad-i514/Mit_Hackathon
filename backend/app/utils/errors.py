"""
Structured error handling utilities
"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Validation error (400)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details
        )


class AuthenticationError(APIError):
    """Authentication error (401)"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401
        )


class AuthorizationError(APIError):
    """Authorization error (403)"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            message=message,
            status_code=403
        )


class NotFoundError(APIError):
    """Not found error (404)"""
    
    def __init__(self, resource: str, resource_id: str = ""):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            error_code="NOT_FOUND",
            message=message,
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class RateLimitError(APIError):
    """Rate limit error (429)"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=429
        )


class ExternalServiceError(APIError):
    """External service error (502)"""
    
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            status_code=502,
            details={"service": service}
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error (503)"""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=503
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    
    return {
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Log error details
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # Log error
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle Pydantic validation exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    if hasattr(exc, 'errors'):
        validation_errors = []
        for error in exc.errors():
            validation_errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        details = {"validation_errors": validation_errors}
        message = f"Validation failed: {len(validation_errors)} error(s)"
    else:
        details = {}
        message = "Validation failed"
    
    logger.warning(
        f"Validation Error: {message}",
        extra={
            "details": details,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response_data = create_error_response(
        error_code="VALIDATION_ERROR",
        message=message,
        status_code=422,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    
    request_id = getattr(request.state, "request_id", None)
    
    # Log full exception details
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal error details in production
    message = "An unexpected error occurred"
    details = {}
    
    # In development, include more details
    import os
    if os.getenv("ENVIRONMENT") == "development":
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    
    response_data = create_error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data
    )