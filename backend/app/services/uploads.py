
import hashlib
import logging
import re
import warnings
from datetime import timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.models.upload import SiteUpload
from app.schemas.upload import UploadResponse

logger = logging.getLogger(__name__)

FORMATS = {
    "JPEG": ({".jpg", ".jpeg"}, "image/jpeg", ".jpg"),
    "PNG": ({".png"}, "image/png", ".png"),
    "WEBP": ({".webp"}, "image/webp", ".webp"),
}


def validate_image(file: UploadFile, settings: Settings):
    raw_name = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    filename = re.sub(r"[\x00-\x1f\x7f]", "", raw_name)
    extension = Path(filename).suffix.lower()

    if not filename or len(filename) > 255:
        raise HTTPException(
            422, "Provide an image filename of at most 255 characters."
        )

    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            415, "Supported image formats: JPEG, PNG and WebP."
        )

    data = file.file.read(settings.max_upload_bytes + 1)

    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            413, "Image exceeds the configured upload size limit."
        )

    if not data:
        raise HTTPException(422, "The image file is empty.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            with Image.open(BytesIO(data)) as img:
                image_format = img.format
                width, height = img.size

                if width * height > settings.max_image_pixels:
                    raise HTTPException(
                        422, "Image has too many pixels. Resize it before uploading."
                    )

                if image_format not in FORMATS:
                    raise HTTPException(
                        415, "Actual image content must be JPEG, PNG or WebP."
                    )

                if getattr(img, "n_frames", 1) != 1:
                    raise HTTPException(
                        422, "Upload a still photograph, not an animated image."
                    )

                img.verify()

            with Image.open(BytesIO(data)) as img:
                img.load()

    except (Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(
            422, "Image has too many pixels. Resize it before uploading."
        ) from None

    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise HTTPException(
            422, "The file is not a complete, readable image."
        ) from None

    extensions, mime, suffix = FORMATS[image_format]

    if extension not in extensions or file.content_type != mime:
        raise HTTPException(
            415,
            "Filename extension and content type must match the actual image format.",
        )

    return data, filename, mime, suffix, width, height


def save_upload(
    file: UploadFile,
    site_context: str | None,
    session,
    settings: Settings,
    user_id: str,
) -> SiteUpload:
    data, filename, mime, suffix, width, height = validate_image(file, settings)

    upload_id = str(uuid4())
    stored_filename = f"{upload_id}{suffix}"
    destination = settings.storage_path / stored_filename

    record = SiteUpload(
        id=upload_id,
        user_id=user_id,
        original_filename=filename,
        stored_filename=stored_filename,
        content_type=mime,
        size_bytes=len(data),
        width=width,
        height=height,
        sha256=hashlib.sha256(data).hexdigest(),
        site_context=site_context,
    )

    created_file = False

    try:
        settings.storage_path.mkdir(parents=True, exist_ok=True)

        with destination.open("xb") as output:
            created_file = True
            output.write(data)

        session.add(record)
        session.commit()

    except (OSError, SQLAlchemyError):
        session.rollback()

        if created_file:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Could not clean up failed upload %s", upload_id
                )

        # Detailed diagnostic information stays in the server log.
        logger.exception("Upload failed, upload ID %s", upload_id)

        raise HTTPException(
            503,
            "Upload could not be saved. Check MySQL configuration, schema and upload folder permissions.",
        ) from None

    return record


def serialize_upload(record: SiteUpload) -> UploadResponse:
    return UploadResponse(
        id=record.id,
        original_filename=record.original_filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        width=record.width,
        height=record.height,
        sha256=record.sha256,
        site_context=record.site_context,
        created_at=record.created_at.replace(tzinfo=timezone.utc),
        image_url=f"/api/uploads/{record.id}/image",
    )
