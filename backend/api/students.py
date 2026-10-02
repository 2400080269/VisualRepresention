"""
Students router: Student records, multi-parameter filtering, and individual report cards.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.schemas.student import StudentListResponse, StudentDetailResponse
from backend.services.student_service import (
    fetch_students,
    fetch_student_by_id,
    fetch_at_risk_students
)

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("", response_model=StudentListResponse, summary="List Students with Filtering & Pagination")
def list_students(
    department: Optional[str] = Query(None, description="Filter by department name (e.g. CSE, AIDS)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (High Risk, Moderate Risk, Low Risk / Safe)"),
    performance_category: Optional[str] = Query(None, description="Filter by academic performance tier"),
    attendance_category: Optional[str] = Query(None, description="Filter by attendance category"),
    min_marks: Optional[float] = Query(None, ge=0, le=100, description="Minimum average marks"),
    max_marks: Optional[float] = Query(None, ge=0, le=100, description="Maximum average marks"),
    min_attendance: Optional[float] = Query(None, ge=0, le=100, description="Minimum overall attendance %"),
    max_attendance: Optional[float] = Query(None, ge=0, le=100, description="Maximum overall attendance %"),
    search: Optional[str] = Query(None, description="Search by name, student ID, or department"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a paginated list of students with comprehensive analytical filtering.
    """
    items, total, total_pages = fetch_students(
        db=db,
        department=department,
        risk_level=risk_level,
        performance_category=performance_category,
        attendance_category=attendance_category,
        min_marks=min_marks,
        max_marks=max_marks,
        min_attendance=min_attendance,
        max_attendance=max_attendance,
        search=search,
        page=page,
        page_size=page_size
    )
    return StudentListResponse(
        items=items,
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/at-risk", response_model=StudentListResponse, summary="List At-Risk Students (Early Warning)")
def list_at_risk_students(
    department: Optional[str] = Query(None, description="Filter by department name"),
    risk_level: Optional[str] = Query(None, description="High Risk or Moderate Risk"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves students flagged under early-warning status (High Risk or Moderate Risk)
    due to low attendance (<75%), low academic marks (<50%), or backlogs.
    """
    items, total, total_pages = fetch_at_risk_students(
        db=db,
        department=department,
        risk_level=risk_level,
        page=page,
        page_size=page_size
    )
    return StudentListResponse(
        items=items,
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{student_id}", response_model=StudentDetailResponse, summary="Get Student Profile & Subject Breakdown")
def get_student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves complete demographics, overall performance rank, GPA, risk assessment,
    and subject-by-subject internal/mid/final exam scores and attendance records.
    """
    return fetch_student_by_id(db, student_id)
