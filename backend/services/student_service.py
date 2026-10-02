"""
Student Service: Encapsulates database queries for student lists,
multi-criteria filtering, pagination, and academic record breakdowns.
"""

import math
from typing import Optional, Tuple, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from backend.database.models import StudentSummary, Mark, Attendance

def fetch_students(
    db: Session,
    department: Optional[str] = None,
    risk_level: Optional[str] = None,
    performance_category: Optional[str] = None,
    attendance_category: Optional[str] = None,
    min_marks: Optional[float] = None,
    max_marks: Optional[float] = None,
    min_attendance: Optional[float] = None,
    max_attendance: Optional[float] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[StudentSummary], int, int]:
    """
    Retrieves paginated and filtered list of student summary records.
    """
    query = db.query(StudentSummary)

    if department:
        query = query.filter(StudentSummary.department.ilike(f"%{department.strip()}%"))
    if risk_level:
        query = query.filter(StudentSummary.risk_level == risk_level)
    if performance_category:
        query = query.filter(StudentSummary.performance_category == performance_category)
    if attendance_category:
        query = query.filter(StudentSummary.attendance_category == attendance_category)
    if min_marks is not None:
        query = query.filter(StudentSummary.average_marks >= min_marks)
    if max_marks is not None:
        query = query.filter(StudentSummary.average_marks <= max_marks)
    if min_attendance is not None:
        query = query.filter(StudentSummary.overall_attendance_pct >= min_attendance)
    if max_attendance is not None:
        query = query.filter(StudentSummary.overall_attendance_pct <= max_attendance)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                StudentSummary.name.ilike(search_filter),
                StudentSummary.student_id.cast(str).ilike(search_filter),
                StudentSummary.department.ilike(search_filter)
            )
        )

    total_count = query.count()
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1

    # Order by overall rank or student_id
    items = query.order_by(asc(StudentSummary.overall_rank), asc(StudentSummary.student_id))\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()

    return items, total_count, total_pages

def fetch_student_by_id(db: Session, student_id: int) -> Dict[str, Any]:
    """
    Retrieves full academic profile for a student including subject-by-subject
    marks and attendance figures.
    """
    student = db.query(StudentSummary).filter(StudentSummary.student_id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} was not found."
        )

    # Fetch marks
    marks = db.query(Mark).filter(Mark.student_id == student_id).all()
    # Fetch attendance
    attendance_records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    att_map = {a.subject: a for a in attendance_records}

    courses_detail = []
    for m in marks:
        att = att_map.get(m.subject)
        courses_detail.append({
            "subject": m.subject,
            "internal": m.internal,
            "mid1": m.mid1,
            "mid2": m.mid2,
            "assignment": m.assignment,
            "final": m.final,
            "raw_total": m.raw_total,
            "normalized_score": m.normalized_score,
            "subject_passed": m.subject_passed,
            "subject_performance_cat": m.subject_performance_cat,
            "total_classes": att.total_classes if att else None,
            "attended": att.attended if att else None,
            "attendance_pct": att.attendance_pct if att else None
        })

    return {
        "student_id": student.student_id,
        "name": student.name,
        "department": student.department,
        "year": student.year,
        "section": student.section,
        "gender": student.gender,
        "total_subjects": student.total_subjects,
        "average_marks": student.average_marks,
        "overall_attendance_pct": student.overall_attendance_pct,
        "gpa": student.gpa,
        "performance_category": student.performance_category,
        "attendance_category": student.attendance_category,
        "pass_status": student.pass_status,
        "risk_level": student.risk_level,
        "dept_rank": student.dept_rank,
        "overall_rank": student.overall_rank,
        "courses": courses_detail
    }

def fetch_at_risk_students(
    db: Session,
    department: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[StudentSummary], int, int]:
    """
    Filters specifically for students flagged as 'High Risk' or 'Moderate Risk'.
    """
    query = db.query(StudentSummary)
    if risk_level:
        query = query.filter(StudentSummary.risk_level == risk_level)
    else:
        query = query.filter(StudentSummary.risk_level.in_(["High Risk", "Moderate Risk"]))

    if department:
        query = query.filter(StudentSummary.department.ilike(f"%{department.strip()}%"))

    total_count = query.count()
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1

    items = query.order_by(asc(StudentSummary.risk_level), asc(StudentSummary.average_marks))\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()

    return items, total_count, total_pages
