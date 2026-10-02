"""
Analytics Service: Computes headline KPIs, statistical correlations,
grade distributions, and subject benchmarking from live database records.
"""

from typing import Dict, Any, List
import pandas as pd
from fastapi import HTTPException, status

from backend.config import settings
from src.database import DatabaseManager
from src.analysis import PerformanceAnalyzer

def _get_data_frames():
    """Helper to query current summary and detail tables from SQLite."""
    db = DatabaseManager(db_path=str(settings.SQLITE_DB_PATH))
    df_summary = db.run_query("SELECT * FROM student_summary")
    df_marks = db.run_query("SELECT * FROM marks")
    if df_summary.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student data available in database. Please ingest a dataset first."
        )
    return db, df_summary, df_marks

def get_overview_kpis() -> Dict[str, Any]:
    """Computes headline KPIs from actual student_summary records."""
    db, df_summary, df_marks = _get_data_frames()
    analyzer = PerformanceAnalyzer(df_summary=df_summary)
    kpis = analyzer.get_kpis()

    return {
        "total_students": int(kpis["total_students"]),
        "average_marks": float(kpis["avg_marks"]),
        "median_marks": float(kpis["median_marks"]),
        "std_marks": float(kpis["std_marks"]),
        "average_attendance": float(kpis["avg_attendance"]),
        "pass_count": int(kpis["pass_count"]),
        "pass_percentage": float(kpis["pass_rate"]),
        "at_risk_count": int(kpis["at_risk_count"]),
        "at_risk_percentage": float(kpis["at_risk_pct"]),
        "top_performer": str(kpis.get("top_performer", "")),
        "top_performer_marks": float(kpis.get("top_performer_marks", 0.0)),
        "lowest_performer": str(kpis.get("lowest_performer", "")),
        "lowest_performer_marks": float(kpis.get("lowest_performer_marks", 0.0))
    }

def get_attendance_analytics() -> Dict[str, Any]:
    """Computes attendance distributions and statistical correlations with academic scores."""
    db, df_summary, _ = _get_data_frames()
    analyzer = PerformanceAnalyzer(df_summary=df_summary)
    corr_stats = analyzer.compute_attendance_correlation()

    # Query attendance tier correlation
    df_tiers = db.get_attendance_tier_correlation()
    tier_items = []
    for _, r in df_tiers.iterrows():
        tier_items.append({
            "attendance_category": str(r["attendance_category"]),
            "student_count": int(r["student_count"]),
            "avg_marks": float(r["avg_marks"]),
            "min_marks": float(r["min_marks"]),
            "max_marks": float(r["max_marks"]),
            "pass_rate": float(r["pass_rate"])
        })

    return {
        "average_attendance_pct": round(float(df_summary["overall_attendance_pct"].mean()), 1),
        "correlation": {
            "pearson_r": float(corr_stats.get("pearson_r", 0.0)),
            "p_value": float(corr_stats.get("p_value", 1.0)),
            "spearman_rho": float(corr_stats.get("spearman_rho", 0.0)),
            "r_squared": float(corr_stats.get("r_squared", 0.0)),
            "slope": float(corr_stats.get("slope", 0.0)),
            "intercept": float(corr_stats.get("intercept", 0.0)),
            "interpretation": str(corr_stats.get("interpretation", ""))
        },
        "attendance_tiers": tier_items
    }

def get_performance_analytics() -> Dict[str, Any]:
    """Computes academic grade distributions and department benchmarks."""
    db, df_summary, _ = _get_data_frames()
    analyzer = PerformanceAnalyzer(df_summary=df_summary)
    df_dist = analyzer.get_performance_distribution()

    dist_items = []
    for _, r in df_dist.iterrows():
        dist_items.append({
            "category": str(r["Category"]),
            "count": int(r["Count"]),
            "percentage": float(r["Percentage"])
        })

    df_dept = db.get_department_benchmarks()
    # Compute pass rate per department
    dept_items = []
    for _, r in df_dept.iterrows():
        dept_name = str(r["department"])
        dept_subset = df_summary[df_summary["department"] == dept_name]
        pass_rate = round(float((dept_subset["pass_status"] == "Passed").mean() * 100), 1) if not dept_subset.empty else 0.0
        dept_items.append({
            "department": dept_name,
            "total_students": int(r["total_students"]),
            "dept_avg_marks": float(r["dept_avg_marks"]),
            "dept_avg_attendance": float(r["dept_avg_attendance"]),
            "pass_rate": pass_rate
        })

    return {
        "average_marks": round(float(df_summary["average_marks"].mean()), 1),
        "median_marks": round(float(df_summary["average_marks"].median()), 1),
        "std_marks": round(float(df_summary["average_marks"].std()), 1),
        "grade_distribution": dist_items,
        "department_benchmarks": dept_items
    }

def get_subjects_analytics() -> Dict[str, Any]:
    """Computes course-level averages, pass rates, and identifies strongest/weakest subjects."""
    db, _, df_marks = _get_data_frames()
    df_subj = db.get_subject_statistics()

    subjects_list = []
    for _, r in df_subj.iterrows():
        subjects_list.append({
            "subject": str(r["subject"]),
            "total_enrolled": int(r["total_enrolled"]),
            "subject_avg_marks": float(r["subject_avg_marks"]),
            "lowest_marks": float(r["lowest_marks"]),
            "highest_marks": float(r["highest_marks"]),
            "total_passed": int(r["total_passed"]),
            "total_failed": int(r["total_failed"]),
            "pass_percentage": float(r["pass_percentage"])
        })

    sorted_by_score = sorted(subjects_list, key=lambda x: x["subject_avg_marks"], reverse=True)
    strongest = sorted_by_score[0] if sorted_by_score else {"subject": "None", "subject_avg_marks": 0.0}
    weakest = sorted_by_score[-1] if sorted_by_score else {"subject": "None", "subject_avg_marks": 0.0}

    return {
        "strongest_subject": strongest["subject"],
        "strongest_avg": strongest["subject_avg_marks"],
        "weakest_subject": weakest["subject"],
        "weakest_avg": weakest["subject_avg_marks"],
        "subjects": subjects_list
    }
