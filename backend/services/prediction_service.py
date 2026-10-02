"""
Prediction Service: Executes low-latency ML inference using pre-trained
Random Forest Classifier and Gradient Boosting Regressor models.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import HTTPException, status

from backend.config import settings
from src.ml_predictor import StudentPerformancePredictor

# Persistent prediction history path
HISTORY_PATH = settings.DATA_DIR / "prediction_history.json"

# In-memory singleton predictor
_predictor_instance = None

def get_predictor() -> StudentPerformancePredictor:
    """Returns singleton predictor instance with loaded model weights."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = StudentPerformancePredictor(model_dir=str(settings.MODELS_DIR))
        success = _predictor_instance.load_models()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML models not yet trained or found on disk. Please trigger the data pipeline first."
            )
    return _predictor_instance

def _load_history() -> List[Dict[str, Any]]:
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_history(history: List[Dict[str, Any]]):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, default=str)

def run_prediction(
    attendance_pct: float,
    internal: float,
    mid1: float,
    mid2: float,
    assignment: float,
    student_name: str = None
) -> Dict[str, Any]:
    """
    Executes inference against pre-trained models and records result in history.
    """
    predictor = get_predictor()
    raw_result = predictor.predict(
        attendance_pct=attendance_pct,
        internal=internal,
        mid1=mid1,
        mid2=mid2,
        assignment=assignment
    )

    pred_id = f"pred_{uuid.uuid4().hex[:10]}"
    timestamp = datetime.utcnow()

    prediction_record = {
        "prediction_id": pred_id,
        "timestamp": timestamp.isoformat(),
        "student_name": student_name,
        "input_features": {
            "attendance_pct": float(attendance_pct),
            "internal": float(internal),
            "mid1": float(mid1),
            "mid2": float(mid2),
            "assignment": float(assignment)
        },
        "predicted_category": raw_result["predicted_category"],
        "predicted_final_score": raw_result["predicted_final_score"],
        "estimated_overall_percentage": raw_result["estimated_overall_percentage"],
        "category_probabilities": raw_result["category_probabilities"],
        "is_at_risk": raw_result["is_at_risk"],
        "risk_label": raw_result["risk_label"],
        "recommendations": raw_result["recommendations"]
    }

    # Store in history (keep latest 100)
    history = _load_history()
    history.insert(0, prediction_record)
    _save_history(history[:100])

    return prediction_record

def get_prediction_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves list of recent prediction simulations."""
    history = _load_history()
    return history[:limit]
