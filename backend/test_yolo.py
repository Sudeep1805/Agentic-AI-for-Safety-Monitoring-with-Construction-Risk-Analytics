
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent

model_path = (
    BASE_DIR
    / "runs"
    / "construction_safety"
    / "yolo11n_baseline"
    / "weights"
    / "best.pt"
)

image_path = (
    BASE_DIR
    / "datasets"
    / "construction_safety"
    / "valid"
    / "images"
    / "-1079-_png_jpg.rf.19092a3937930012f9fd9c1ce57f5a7b.jpg"
)

if not model_path.exists():
    raise FileNotFoundError(f"Model not found: {model_path}")

if not image_path.exists():
    raise FileNotFoundError(f"Image not found: {image_path}")

model = YOLO(str(model_path))

results = model.predict(
    source=str(image_path),
    conf=0.25,
    save=True
)

print("Trained model test completed!")
print(f"Model: {model_path}")
print(f"Output folder: {results[0].save_dir}")
print("Detected objects:")

for box in results[0].boxes:
    class_id = int(box.cls[0])
    confidence = float(box.conf[0])
    class_name = model.names[class_id]
    print(f"{class_name}: {confidence:.2%}")
