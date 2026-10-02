"""
Pydantic schemas for Analytics API responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class OverviewAnalyticsResponse(BaseModel):
    total_students: int
    average_marks: float
    median_marks: float
    std_marks: float
    average_attendance: float
    pass_count: int
    pass_percentage: float
    at_risk_count: int
    at_risk_percentage: float
    top_performer: Optional[str] = None
    top_performer_marks: Optional[float] = None
    lowest_performer: Optional[str] = None
    lowest_performer_marks: Optional[float] = None

class AttendanceTierItem(BaseModel):
    attendance_category: str
    student_count: int
    avg_marks: float
    min_marks: float
    max_marks: float
    pass_rate: float

class AttendanceCorrelation(BaseModel):
    pearson_r: float
    p_value: float
    spearman_rho: float
    r_squared: float
    slope: float
    intercept: float
    interpretation: str

class AttendanceAnalyticsResponse(BaseModel):
    average_attendance_pct: float
    correlation: AttendanceCorrelation
    attendance_tiers: List[AttendanceTierItem]

class PerformanceCategoryItem(BaseModel):
    category: str
    count: int
    percentage: float

class DepartmentBenchmarkItem(BaseModel):
    department: str
    total_students: int
    dept_avg_marks: float
    dept_avg_attendance: float
    pass_rate: Optional[float] = None

class PerformanceAnalyticsResponse(BaseModel):
    average_marks: float
    median_marks: float
    std_marks: float
    grade_distribution: List[PerformanceCategoryItem]
    department_benchmarks: List[DepartmentBenchmarkItem]

class SubjectStatItem(BaseModel):
    subject: str
    total_enrolled: int
    subject_avg_marks: float
    lowest_marks: float
    highest_marks: float
    total_passed: int
    total_failed: int
    pass_percentage: float

class SubjectsAnalyticsResponse(BaseModel):
    strongest_subject: str
    strongest_avg: float
    weakest_subject: str
    weakest_avg: float
    subjects: List[SubjectStatItem]
