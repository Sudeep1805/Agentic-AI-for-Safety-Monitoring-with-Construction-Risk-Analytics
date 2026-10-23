
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATA_YAML = BASE_DIR / "datasets" / "construction_safety" / "data.yaml"

if not DATA_YAML.exists():
    raise FileNotFoundError(f"Dataset config not found: {DATA_YAML}")

model = YOLO("yolo11n.pt")

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

print("Training finished. Check the runs/construction_safety folder.")
