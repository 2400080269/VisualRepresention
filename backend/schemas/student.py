"""
Pydantic schemas for Student records, filtering, and deep-dive profiles.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class StudentSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    department: str
    year: int
    section: str
    gender: Optional[str] = None
    total_subjects: Optional[int] = None
    average_marks: float
    overall_attendance_pct: float
    gpa: float
    performance_category: str
    attendance_category: str
    pass_status: str
    risk_level: str
    dept_rank: Optional[int] = None
    overall_rank: Optional[int] = None

class StudentListResponse(BaseModel):
    items: List[StudentSummaryItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class StudentCourseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subject: str
    internal: float
    mid1: float
    mid2: float
    assignment: float
    final: float
    raw_total: float
    normalized_score: float
    subject_passed: int
    subject_performance_cat: Optional[str] = None
    total_classes: Optional[int] = None
    attended: Optional[int] = None
    attendance_pct: Optional[float] = None

class StudentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    department: str
    year: int
    section: str
    gender: Optional[str] = None
    total_subjects: Optional[int] = None
    average_marks: float
    overall_attendance_pct: float
    gpa: float
    performance_category: str
    attendance_category: str
    pass_status: str
    risk_level: str
    dept_rank: Optional[int] = None
    overall_rank: Optional[int] = None
    courses: List[StudentCourseDetail]
