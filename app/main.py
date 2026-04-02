from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.session import create_db_and_tables, session_scope
from app.routes import auth_router, dashboard_router, transactions_router, users_router
from app.services.auth_service import seed_admin_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    with session_scope() as session:
        seed_admin_user(session)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        description=(
            "A clean, modular backend API for a finance dashboard with JWT authentication, "
            "RBAC, transaction management, and database-level aggregations."
        ),
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(transactions_router)
    app.include_router(dashboard_router)

    @app.get("/", tags=["Health"])
    def root():
        return {
            "success": True,
            "data": {
                "message": "Finance Dashboard API is running.",
                "docs_url": settings.docs_url,
            },
        }

    return app


app = create_app()
