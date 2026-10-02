"""
Dataset Service: Orchestrates secure file ingestion, format detection,
data cleaning, feature engineering, SQLite persistence, and model updating.
"""

import os
import io
import json
import uuid
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
import pandas as pd

from backend.config import settings
from src.file_uploader import parse_uploaded_academic_data
from src.data_cleaning import DataCleaner
from src.data_processing import DataProcessor
from src.database import DatabaseManager
from src.ml_predictor import StudentPerformancePredictor

REGISTRY_PATH = settings.DATA_DIR / "datasets_registry.json"

def _load_registry() -> dict:
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_registry(registry: dict):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, default=str)

async def validate_and_read_file(file: UploadFile) -> tuple[bytes, str]:
    """
    Validates file extension and size before reading contents into memory.
    """
    filename = file.filename or "unknown_file"
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = [".csv", ".xlsx", ".xls"]
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions are: {', '.join(allowed_exts)}"
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    return content, filename

def process_dataset(content: bytes, filename: str) -> dict:
    """
    Ingests and processes raw academic file through the data cleaning, feature engineering,
    database update, and model retraining pipeline.
    """
    dataset_id = f"ds_{uuid.uuid4().hex[:10]}"
    upload_time = datetime.utcnow()

    # Step 1: Flexible Parse
    try:
        file_obj = io.BytesIO(content)
        setattr(file_obj, "name", filename)
        df_students_raw, df_marks_raw, df_att_raw, format_detected = parse_uploaded_academic_data(file_obj)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse dataset layout: {str(e)}"
        )

    # Step 2: Comprehensive Cleaning and Audit
    cleaner = DataCleaner()
    df_students_clean = cleaner.clean_students(df_students_raw)
    df_marks_clean = cleaner.clean_marks(df_marks_raw)
    df_att_clean = cleaner.clean_attendance(df_att_raw)
    audit_log = cleaner.cleaning_audit_log

    # Calculate audit metrics
    duplicates_removed = sum(a.get("rows_affected", 0) for a in audit_log if "Deduplication" in a.get("step", ""))
    imputed_count = sum(a.get("rows_affected", 0) for a in audit_log if "Missing" in a.get("step", ""))
    clipped_count = sum(a.get("rows_affected", 0) for a in audit_log if "Out-of-bounds" in a.get("step", ""))

    # Step 3: Feature Engineering and Summary Aggregations
    processor = DataProcessor(processed_data_dir=str(settings.PROCESSED_DATA_DIR))
    df_details, df_summary = processor.process_and_merge(
        df_students_clean, df_marks_clean, df_att_clean, save_master=True
    )

    # Step 4: Persist in SQLite Relational Database
    db = DatabaseManager(db_path=str(settings.SQLITE_DB_PATH))
    db.populate_database(df_students_clean, df_details, df_summary)

    # Step 5: Retrain ML models on fresh dataset
    try:
        predictor = StudentPerformancePredictor(model_dir=str(settings.MODELS_DIR))
        predictor.train_models(df_details)
    except Exception as e:
        print(f"Warning: ML retraining encountered note: {e}")

    summary_result = {
        "dataset_id": dataset_id,
        "filename": filename,
        "upload_timestamp": upload_time.isoformat(),
        "format_detected": format_detected,
        "total_students": len(df_summary),
        "total_enrollments": len(df_details),
        "duplicate_records_removed": duplicates_removed,
        "imputed_values_count": imputed_count,
        "out_of_bounds_clipped": clipped_count,
        "overall_pass_rate": round(float((df_summary["pass_status"] == "Passed").mean() * 100), 1),
        "average_marks": round(float(df_summary["average_marks"].mean()), 1),
        "overall_attendance_pct": round(float(df_summary["overall_attendance_pct"].mean()), 1),
        "at_risk_count": int(df_summary["risk_level"].isin(["High Risk", "Moderate Risk"]).sum()),
        "audit_log": audit_log
    }

    # Record in persistent registry
    registry = _load_registry()
    registry[dataset_id] = {
        "dataset_id": dataset_id,
        "filename": filename,
        "uploaded_at": upload_time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "processed",
        "records_count": len(df_summary),
        "file_size_bytes": len(content),
        "summary": summary_result
    }
    _save_registry(registry)

    return summary_result

def get_all_datasets() -> list:
    registry = _load_registry()
    items = []
    for ds_id, data in registry.items():
        items.append({
            "dataset_id": ds_id,
            "filename": data.get("filename", "unknown"),
            "uploaded_at": data.get("uploaded_at", ""),
            "status": data.get("status", "processed"),
            "records_count": data.get("records_count", 0),
            "file_size_bytes": data.get("file_size_bytes", 0)
        })
    return items

def get_dataset_by_id(dataset_id: str) -> dict:
    registry = _load_registry()
    if dataset_id not in registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found."
        )
    return registry[dataset_id]
