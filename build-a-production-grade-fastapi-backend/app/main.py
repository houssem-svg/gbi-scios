import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.compliance import router as compliance_router
from app.routers.dashboard import router as dashboard_router
from app.routers.evaluations import router as evaluations_router
from app.routers.parsing import router as parsing_router
from app.routers.payroll import router as payroll_router
from app.routers.projects import router as projects_router
from app.routers.reporting import router as reporting_router
from app.routers.risk import router as risk_router
from app.routers.uploads import router as uploads_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # CORS allow-list driven by settings (comma-separated cors_origins env var).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Auth"])
    app.include_router(
        compliance_router,
        prefix=f"{settings.api_v1_prefix}/compliance",
        tags=["Compliance"],
    )
    app.include_router(parsing_router, prefix=f"{settings.api_v1_prefix}/parsing", tags=["Parsing"])
    app.include_router(projects_router, prefix=f"{settings.api_v1_prefix}/projects", tags=["Projects"])
    app.include_router(uploads_router, prefix=f"{settings.api_v1_prefix}/uploads", tags=["Uploads"])
    app.include_router(risk_router)
    app.include_router(ai_router)
    app.include_router(reporting_router)
    app.include_router(dashboard_router)
    app.include_router(evaluations_router)
    app.include_router(payroll_router)

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Global exception handler: prevent leaking tracebacks / internal details to clients.
    # Returns a structured error with a correlation id; the full traceback is logged server-side.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.exception("Unhandled exception [correlation_id=%s]: %s", correlation_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred.",
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    return app


app = create_app()
