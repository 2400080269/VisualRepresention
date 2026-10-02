"""
Analytics router: High-level academic KPIs, attendance statistics,
performance distributions, and course benchmarking.
"""

from fastapi import APIRouter, Depends
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.schemas.analytics import (
    OverviewAnalyticsResponse,
    AttendanceAnalyticsResponse,
    PerformanceAnalyticsResponse,
    SubjectsAnalyticsResponse
)
from backend.services.analytics_service import (
    get_overview_kpis,
    get_attendance_analytics,
    get_performance_analytics,
    get_subjects_analytics
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview", response_model=OverviewAnalyticsResponse, summary="Academic Overview KPIs")
def overview(current_user: User = Depends(get_current_user)):
    """
    Returns headline institutional metrics: total students, overall average marks,
    attendance rate, university pass percentage, and early-warning counts.
    """
    return get_overview_kpis()

@router.get("/attendance", response_model=AttendanceAnalyticsResponse, summary="Attendance Analytics & Correlations")
def attendance(current_user: User = Depends(get_current_user)):
    """
    Returns attendance rate distributions, standing tier breakdowns, and
    rigorous statistical correlation (Pearson r, Spearman rho, p-value, interpretation)
    against academic outcomes.
    """
    return get_attendance_analytics()

@router.get("/performance", response_model=PerformanceAnalyticsResponse, summary="Performance Distributions & Benchmarks")
def performance(current_user: User = Depends(get_current_user)):
    """
    Returns grade band distributions and department-level academic comparative benchmarks.
    """
    return get_performance_analytics()

@router.get("/subjects", response_model=SubjectsAnalyticsResponse, summary="Course & Subject Benchmarking")
def subjects(current_user: User = Depends(get_current_user)):
    """
    Returns subject-level performance metrics, failure counts, pass rates,
    and identifies strongest versus weakest subjects across curriculum.
    """
    return get_subjects_analytics()
