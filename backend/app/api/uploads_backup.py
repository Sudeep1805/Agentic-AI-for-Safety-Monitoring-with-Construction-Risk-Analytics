
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.api.auth import current_user
from app.models.user import User
from app.models.upload import SiteUpload
from app.schemas.upload import (
    DetectionResponse,
    UploadList,
    UploadResponse,
)
from app.services.detector import detect_objects
from app.services.uploads import save_upload, serialize_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post("", response_model=UploadResponse, status_code=201)
def upload_image(
    request: Request,
    session: DatabaseSession,
    user: Annotated[User, Depends(current_user)],
    file: Annotated[UploadFile, File()],
    site_context: Annotated[str | None, Form(max_length=2000)] = None,
):
    context = site_context.strip() or None if site_context else None

    try:
        record = save_upload(
            file,
            context,
            session,
            request.app.state.settings,
            user.id,
        )
    finally:
        file.file.close()

    response = serialize_upload(record)

    try:
        image_path = (
            request.app.state.settings.storage_path / record.stored_filename
        ).resolve()

        detections = detect_objects(image_path.read_bytes())

        response.detections = [
            DetectionResponse(**detection)
            for detection in detections
        ]
        response.analysis_status = "completed"
        response.analysis_message = (
            f"YOLO detection completed. {len(detections)} object(s) detected. "
            "A construction risk score has not been calculated."
        )

    except Exception:
        logger.exception(
            "Image analysis failed for upload ID %s",
            record.id,
        )
        response.analysis_status = "unavailable"
        response.analysis_message = (
            "The image was saved, but YOLO detection could not be completed. "
            "Check the backend logs."
        )
        response.detections = []

    return response


@router.get("", response_model=UploadList)
def list_uploads(
    session: DatabaseSession,
    user: Annotated[User, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    owned = SiteUpload.user_id == user.id

    records = session.scalars(
        select(SiteUpload)
        .where(owned)
        .order_by(SiteUpload.created_at.desc(), SiteUpload.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    total = session.scalar(
        select(func.count()).select_from(SiteUpload).where(owned)
    )

    return UploadList(
        items=[serialize_upload(record) for record in records],
        total=total,
    )


def find_upload(
    upload_id: UUID,
    session: Session,
    user_id: str,
) -> SiteUpload:
    record = session.scalar(
        select(SiteUpload).where(
            SiteUpload.id == str(upload_id),
            SiteUpload.user_id == user_id,
        )
    )

    if record is None:
        raise HTTPException(404, "Upload not found.")

    return record


@router.get("/{upload_id}", response_model=UploadResponse)
def get_upload(
    upload_id: UUID,
    session: DatabaseSession,
    user: Annotated[User, Depends(current_user)],
):
    return serialize_upload(find_upload(upload_id, session, user.id))


@router.get("/{upload_id}/image")
def get_image(
    upload_id: UUID,
    request: Request,
    session: DatabaseSession,
    user: Annotated[User, Depends(current_user)],
):
    record = find_upload(upload_id, session, user.id)
    root = request.app.state.settings.storage_path
    path = (root / record.stored_filename).resolve()

    if path.parent != root or not path.is_file():
        raise HTTPException(404, "Stored image is missing.")

    return FileResponse(
        path,
        media_type=record.content_type,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )
