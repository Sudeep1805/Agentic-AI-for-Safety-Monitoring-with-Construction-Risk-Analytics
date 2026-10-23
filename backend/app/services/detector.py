
from io import BytesIO
from pathlib import Path

from PIL import Image
from ultralytics import YOLO


BACKEND_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BACKEND_DIR
    / "runs"
    / "construction_safety"
    / "yolo11n_baseline"
    / "weights"
    / "best.pt"
)

_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Trained YOLO model not found: {MODEL_PATH}"
            )

        _model = YOLO(str(MODEL_PATH))

    return _model


def detect_objects(image_bytes: bytes) -> list[dict]:
    with Image.open(BytesIO(image_bytes)) as image:
        image = image.convert("RGB")

    model = get_model()

    results = model.predict(
        source=image,
        device="cpu",
        conf=0.25,
        verbose=False,
    )

    detections = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            coordinates = box.xyxy[0].tolist()

            detections.append({
                "class_id": class_id,
                "class_name": result.names[class_id],
                "confidence": round(confidence, 4),
                "bbox": [round(float(value), 2) for value in coordinates],
            })

    return detections
