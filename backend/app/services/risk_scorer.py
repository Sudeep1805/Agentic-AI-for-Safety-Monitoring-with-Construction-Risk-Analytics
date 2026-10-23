
from typing import Any


# Preliminary rule-based penalties for detected PPE violations.
HAZARD_PENALTIES = {
    "NO-Hardhat": 25,
    "NO-Mask": 10,
    "NO-Safety Vest": 25,
}


def calculate_risk(detections: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate a preliminary construction risk score from 0 to 100.
    Higher scores indicate more detected PPE hazards.
    This is not a certified safety assessment.
    """
    hazards = []
    total_penalty = 0

    for detection in detections:
        class_name = detection.get("class_name", "")
        confidence = float(detection.get("confidence", 0))

        if class_name in HAZARD_PENALTIES and confidence >= 0.25:
            penalty = HAZARD_PENALTIES[class_name]
            total_penalty += penalty

            hazards.append({
                "hazard": class_name,
                "confidence": round(confidence, 4),
                "penalty": penalty,
                "description": (
                    f"Possible PPE violation detected: {class_name}"
                ),
            })

    risk_score = min(total_penalty, 100)

    if risk_score >= 60:
        risk_level = "High"
    elif risk_score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "hazard_count": len(hazards),
        "hazards": hazards,
        "message": (
            "Preliminary risk indicator based on detected PPE violations. "
            "Review the image manually before taking safety decisions."
        ),
    }
