
import logging
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.api.dependencies import get_session
from app.models.detection import Detection
from app.models.upload import SiteUpload
from app.models.user import User
from app.schemas.upload import (
    DetectionResponse,
    UploadList,
    UploadResponse,
)
from app.services.detector import detect_objects
from app.services.risk_scorer import calculate_risk
from app.services.uploads import save_upload, serialize_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def get_upload_response(
    record: SiteUpload,
    session: Session,
) -> UploadResponse:
    response = serialize_upload(record)

    saved_detections = session.scalars(
        select(Detection)
        .where(Detection.upload_id == record.id)
        .order_by(Detection.id)
    ).all()

    response.detections = [
        DetectionResponse(
            class_id=item.class_id,
            class_name=item.class_name,
            confidence=item.confidence,
            bbox=item.bbox,
        )
        for item in saved_detections
    ]

    risk_result = calculate_risk(
        [
            {
                "class_name": item.class_name,
                "confidence": item.confidence,
            }
            for item in saved_detections
        ]
    )

    response.risk_score = risk_result["risk_score"]
    response.risk_level = risk_result["risk_level"]
    response.hazard_count = risk_result["hazard_count"]
    response.hazards = risk_result["hazards"]

    response.analysis_status = "completed"
    response.analysis_message = (
        f"YOLO detection completed. "
        f"{len(saved_detections)} object(s) detected. "
        f"Preliminary risk: {response.risk_level} "
        f"({response.risk_score}/100), with "
        f"{response.hazard_count} possible PPE violation(s). "
        "Manual review is required."
    )

    return response


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

    try:
        image_path = (
            request.app.state.settings.storage_path
            / record.stored_filename
        ).resolve()

        detections = detect_objects(image_path.read_bytes())

        saved_rows = [
            Detection(
                upload_id=record.id,
                class_id=item["class_id"],
                class_name=item["class_name"],
                confidence=item["confidence"],
                bbox=item["bbox"],
            )
            for item in detections
        ]

        session.add_all(saved_rows)
        session.commit()

        return get_upload_response(record, session)

    except Exception:
        session.rollback()
        logger.exception(
            "Image analysis failed for upload ID %s",
            record.id,
        )

        response = serialize_upload(record)
        response.analysis_status = "unavailable"
        response.analysis_message = (
            "The image was saved, but YOLO detection or saving its "
            "results could not be completed. Check the backend logs."
        )
        response.detections = []
        response.risk_score = None
        response.risk_level = None
        response.hazard_count = 0
        response.hazards = []

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
        .order_by(
            SiteUpload.created_at.desc(),
            SiteUpload.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    total = session.scalar(
        select(func.count())
        .select_from(SiteUpload)
        .where(owned)
    ) or 0

    return UploadList(
        items=[
            get_upload_response(record, session)
            for record in records
        ],
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
    record = find_upload(upload_id, session, user.id)
    return get_upload_response(record, session)


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
