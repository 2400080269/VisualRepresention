"""
Pydantic schemas for Dataset uploads and Data Quality Summaries.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DataQualityAuditEntry(BaseModel):
    step: str
    message: str
    rows_affected: int

class DatasetQualitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    filename: str
    upload_timestamp: datetime
    format_detected: str
    total_students: int
    total_enrollments: int
    duplicate_records_removed: int
    imputed_values_count: int
    out_of_bounds_clipped: int
    overall_pass_rate: float
    average_marks: float
    overall_attendance_pct: float
    at_risk_count: int
    audit_log: List[DataQualityAuditEntry]

class DatasetItem(BaseModel):
    dataset_id: str
    filename: str
    uploaded_at: str
    status: str
    records_count: int
    file_size_bytes: int
