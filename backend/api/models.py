"""
Model router: Inspect trained machine learning model architectures,
feature importances, and validation benchmark metrics.
"""

from fastapi import APIRouter, Depends
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.schemas.model import ModelInfoResponse, ModelMetricsResponse
from backend.services.model_service import get_model_specifications, get_model_evaluation_metrics

router = APIRouter(prefix="/api/model", tags=["Model"])

@router.get("/info", response_model=ModelInfoResponse, summary="Get Model Architecture & Information")
def model_info(current_user: User = Depends(get_current_user)):
    """
    Returns metadata about active ML models: algorithm architectures,
    feature lists, classification targets, and training timestamps.
    """
    return get_model_specifications()

@router.get("/metrics", response_model=ModelMetricsResponse, summary="Get Model Performance Metrics")
def model_metrics(current_user: User = Depends(get_current_user)):
    """
    Returns offline test performance metrics: Classification Accuracy,
    Macro Precision/Recall/F1, Regressor R2 score, RMSE, and feature importance weights.
    """
    return get_model_evaluation_metrics()
