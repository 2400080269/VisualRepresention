"""
SQLAlchemy ORM models representing both authentication entities
and existing educational analytics database tables.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class User(Base):
    """User account model supporting role-based authorization (ADMIN / USER)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="USER", nullable=False)  # 'ADMIN' or 'USER'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Student(Base):
    """Demographics table for students."""
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    section = Column(String(10), nullable=False)
    gender = Column(String(20), nullable=False)

class Mark(Base):
    """Course marks component table (composite PK: student_id + subject)."""
    __tablename__ = "marks"

    student_id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), primary_key=True, index=True)
    internal = Column(Float, nullable=False)
    mid1 = Column(Float, nullable=False)
    mid2 = Column(Float, nullable=False)
    assignment = Column(Float, nullable=False)
    final = Column(Float, nullable=False)
    raw_total = Column(Float, nullable=False)
    normalized_score = Column(Float, nullable=False)
    subject_passed = Column(Integer, nullable=False)
    subject_performance_cat = Column(String(30))

class Attendance(Base):
    """Course attendance component table (composite PK: student_id + subject)."""
    __tablename__ = "attendance"

    student_id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), primary_key=True, index=True)
    total_classes = Column(Integer, nullable=False)
    attended = Column(Integer, nullable=False)
    attendance_pct = Column(Float, nullable=False)

class StudentSummary(Base):
    """Aggregated academic summary profile for each student."""
    __tablename__ = "student_summary"

    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    section = Column(String(10), nullable=False)
    gender = Column(String(20))
    total_subjects = Column(Integer)
    average_marks = Column(Float, nullable=False)
    overall_attendance_pct = Column(Float, nullable=False)
    gpa = Column(Float, nullable=False)
    performance_category = Column(String(30), nullable=False, index=True)
    attendance_category = Column(String(30), nullable=False)
    pass_status = Column(String(20), nullable=False)
    risk_level = Column(String(30), nullable=False, index=True)
    dept_rank = Column(Integer)
    overall_rank = Column(Integer)
