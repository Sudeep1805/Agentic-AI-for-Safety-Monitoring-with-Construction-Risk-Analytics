
from ultralytics import YOLO

# Load a small pretrained YOLO model
model = YOLO("yolo11n.pt")

# Run inference on one image from our construction dataset
image_path = (
    r"datasets\construction_safety\valid\images"
)

import os

images = [
    os.path.join(image_path, name)
    for name in os.listdir(image_path)
    if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
]

if not images:
    raise FileNotFoundError(
        f"No images found in {image_path}"
    )

results = model.predict(
    source=images[0],
    save=True,
    conf=0.25,
)

print("Test image:", images[0])
print("Detection test completed.")
print("Annotated output saved under the runs/detect folder.")
print("Note: this pretrained model uses COCO classes, not our 10 construction classes.")
