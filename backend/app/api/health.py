from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.upload import SiteUpload

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "site-risk-api", "phase": "upload-foundation"}


@router.get("/health/ready")
def readiness(request: Request):
    try:
        with request.app.state.session_factory() as session:
            session.execute(select(SiteUpload.id).limit(1))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={
            "status": "not_ready", "database": "unavailable",
            "detail": "Configure backend/.env and run python -m app.init_db. MySQL and its upload table are required.",
        })
    return {"status": "ready", "database": "connected", "analysis": "unavailable"}
