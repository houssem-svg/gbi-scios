from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.risk import router as risk_router
from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.compliance import router as compliance_router
from app.routers.parsing import router as parsing_router
from app.routers.projects import router as projects_router
from app.routers.uploads import router as uploads_router
from app.routers.ai import router as ai_router
from app.routers.reporting import router as reporting_router
from app.routers.dashboard import router as dashboard_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 🛡️ تفعيل جدار حماية CORS للربط مع Next.js
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app

app = create_app()