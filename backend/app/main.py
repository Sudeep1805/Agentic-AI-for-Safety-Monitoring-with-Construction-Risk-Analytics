from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import auth, health, projects, uploads
from app.core.config import Settings, get_settings
from app.core.database import make_engine, make_session_factory
from app.core.upload_limit import UploadBodyLimitMiddleware


def create_app(settings: Settings | None = None, session_factory=None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings) if session_factory is None else None

    @asynccontextmanager
    async def lifespan(app):
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Site Risk Monitoring API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory or make_session_factory(engine)
    app.add_middleware(UploadBodyLimitMiddleware, max_bytes=settings.max_upload_bytes + 64 * 1024)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type", "Authorization"])

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        return JSONResponse(status_code=503, content={
            "detail": "Database unavailable. Check backend/.env, start MySQL and initialize the schema."
        })

    @app.get("/")
    def root():
        return {
            "service": "site-risk-api",
            "message": "Backend API is running. Open the frontend at http://127.0.0.1:5173.",
            "frontend_url": "http://127.0.0.1:5173",
            "docs_url": "/docs",
            "health_url": "/health",
        }

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(uploads.router)
    return app


app = create_app()
