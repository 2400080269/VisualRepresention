"""
Datasets router: File upload, pipeline trigger, dataset history, and data-quality inspection.
"""

from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.schemas.dataset import DatasetQualitySummary, DatasetItem
from backend.services.dataset_service import (
    validate_and_read_file,
    process_dataset,
    get_all_datasets,
    get_dataset_by_id
)

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetQualitySummary, status_code=status.HTTP_201_CREATED, summary="Upload & Process Academic Dataset")
async def upload_dataset(
    file: UploadFile = File(..., description="CSV or Excel (.xlsx, .xls) dataset"),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads an academic dataset (CSV or Excel). Validates file size and format,
    triggers automated cleaning, metric feature engineering, updates the SQLite database,
    refreshes ML models, and returns a detailed data quality summary.
    """
    content, filename = await validate_and_read_file(file)
    summary = process_dataset(content, filename)
    return summary

@router.get("", response_model=List[DatasetItem], summary="List Ingested Datasets")
def list_datasets(current_user: User = Depends(get_current_user)):
    """
    Retrieves a list of all processed datasets with metadata and timestamps.
    """
    return get_all_datasets()

@router.get("/{dataset_id}", summary="Get Dataset Details and Quality Audit")
def get_dataset(dataset_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieves detailed metadata, record counts, and quality audit logs for a specific dataset ID.
    """
    return get_dataset_by_id(dataset_id)
