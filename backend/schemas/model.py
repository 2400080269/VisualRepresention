"""
Pydantic schemas for Machine Learning Model Metadata and Evaluation Metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_family: str
    classifier_algorithm: str
    regressor_algorithm: str
    version: str
    last_trained: str
    feature_names: List[str]
    target_classes: List[str]
    target_regression_label: str
    training_sample_size: int

class ModelMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    classifier_accuracy: float
    regressor_r2_score: float
    regressor_rmse: float
    feature_importances: Dict[str, float]
    classification_report_summary: Dict[str, Any]
    evaluation_benchmark: str
