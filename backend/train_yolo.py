
from pathlib import Path
from ultralytics import YOLO

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_YAML = BASE_DIR / "datasets" / "construction_safety" / "data.yaml"

# Verify dataset configuration
if not DATA_YAML.exists():
    raise FileNotFoundError(f"Dataset config not found: {DATA_YAML}")

print("Dataset config:", DATA_YAML)
print("Loading YOLO11 nano model...")

model = YOLO("yolo11n.pt")

print("Starting construction safety training...")

model.train(
    data=str(DATA_YAML),
    epochs=20,
    imgsz=640,
    batch=4,
    device="cpu",
    workers=0,
    project=str(BASE_DIR / "runs" / "construction_safety"),
    name="yolo11n_baseline",
    patience=5,
    plots=True,
)

print("Training finished.")
