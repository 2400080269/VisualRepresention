"""
Pydantic schemas for Machine Learning Grade Prediction and Risk Simulation.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PredictionRequest(BaseModel):
    attendance_pct: float = Field(..., ge=0.0, le=100.0, description="Overall attendance percentage (0 to 100)")
    internal: float = Field(..., ge=0.0, le=20.0, description="Internal Continuous Evaluation marks (0 to 20)")
    mid1: float = Field(..., ge=0.0, le=25.0, description="Midterm 1 marks (0 to 25)")
    mid2: float = Field(..., ge=0.0, le=25.0, description="Midterm 2 marks (0 to 25)")
    assignment: float = Field(..., ge=0.0, le=10.0, description="Assignment / Project marks (0 to 10)")
    student_name: Optional[str] = Field(None, description="Optional name of the student for reporting")

class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: str
    timestamp: datetime
    student_name: Optional[str] = None
    input_features: Dict[str, float]
    predicted_category: str
    predicted_final_score: float
    estimated_overall_percentage: float
    category_probabilities: Dict[str, float]
    is_at_risk: bool
    risk_label: str
    recommendations: List[str]
