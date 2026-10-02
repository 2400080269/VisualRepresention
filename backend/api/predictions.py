"""
Predictions router: Real-time academic grade forecasting, risk categorization,
what-if intervention simulations, and prediction history.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.schemas.prediction import PredictionRequest, PredictionResponse
from backend.services.prediction_service import run_prediction, get_prediction_history

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.post("", response_model=PredictionResponse, summary="Execute Grade & Risk Prediction")
def predict_student_performance(
    payload: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validates academic inputs, applies the pre-trained Random Forest Classifier
    and Gradient Boosting Regressor, calculates class probabilities, and generates
    personalized early-intervention recommendations.
    """
    result = run_prediction(
        attendance_pct=payload.attendance_pct,
        internal=payload.internal,
        mid1=payload.mid1,
        mid2=payload.mid2,
        assignment=payload.assignment,
        student_name=payload.student_name
    )
    return result

@router.get("", response_model=List[PredictionResponse], summary="Get Recent Predictions History")
def list_prediction_history(
    limit: int = Query(20, ge=1, le=100, description="Number of recent records to retrieve"),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves history of recent predictions and simulations.
    """
    return get_prediction_history(limit=limit)
