"""
Module: data_processing.py
Purpose: Feature engineering, academic metric calculation (attendance %, weighted totals,
performance tiers, pass/fail status, risk levels), and dataset merging.
"""

import os
import pandas as pd
import numpy as np

def assign_performance_category(score):
    """Categorizes student academic score into standard college performance bands."""
    if pd.isna(score):
        return "Unknown"
    elif score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Very Good"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    else:
        return "Needs Improvement"

def assign_attendance_category(attendance_pct):
    """Categorizes attendance percentage into academic standing / risk levels."""
    if pd.isna(attendance_pct):
        return "Unknown"
    elif attendance_pct >= 85:
        return "Good (>85%)"
    elif attendance_pct >= 75:
        return "Normal (75-85%)"
    else:
        return "At Risk (<75%)"

class DataProcessor:
    def __init__(self, processed_data_dir="data/processed"):
        self.processed_data_dir = processed_data_dir

    def process_and_merge(self, df_students, df_marks, df_attendance, save_master=True):
        """
        Calculates all key metrics and builds both subject-level and student-level
        unified analytical master dataframes.
        """
        # 1. Merge Marks and Attendance on [student_id, subject]
        marks_att = pd.merge(
            df_marks,
            df_attendance,
            on=["student_id", "subject"],
            how="inner"
        )
        
        # 2. Subject-level Feature Engineering
        # Calculate Attendance % per subject
        marks_att["attendance_pct"] = (
            (marks_att["attended"] / marks_att["total_classes"]) * 100
        ).round(1)
        
        # Calculate Normalized 100-point Academic Score for each subject:
        # Internal (20) + Mid1 (25) + Mid2 (25) + Assignment (10) + Final (100) = 180 total possible
        marks_att["raw_total"] = (
            marks_att["internal"] + 
            marks_att["mid1"] + 
            marks_att["mid2"] + 
            marks_att["assignment"] + 
            marks_att["final"]
        ).round(1)
        
        marks_att["normalized_score"] = (
            (marks_att["raw_total"] / 180.0) * 100.0
        ).round(1)
        
        # Midterm average progression
        marks_att["mid_avg"] = ((marks_att["mid1"] + marks_att["mid2"]) / 2.0).round(1)
        # Midterm change: indicates whether student improved between mid 1 and mid 2
        marks_att["mid_growth"] = (marks_att["mid2"] - marks_att["mid1"]).round(1)
        
        # Subject Pass criteria: normalized_score >= 40 AND final >= 35 (standard university bar)
        marks_att["subject_passed"] = (
            (marks_att["normalized_score"] >= 40.0) & (marks_att["final"] >= 35.0)
        )
        marks_att["subject_status"] = marks_att["subject_passed"].apply(lambda x: "Pass" if x else "Fail")
        marks_att["subject_performance_cat"] = marks_att["normalized_score"].apply(assign_performance_category)

        # 3. Merge with Student Demographics
        df_full_details = pd.merge(
            marks_att,
            df_students,
            on="student_id",
            how="inner"
        )

        # 4. Student-Level Aggregations (Comprehensive Profile)
        student_summary = df_full_details.groupby("student_id").agg(
            name=("name", "first"),
            department=("department", "first"),
            year=("year", "first"),
            section=("section", "first"),
            gender=("gender", "first"),
            total_subjects=("subject", "count"),
            total_attended=("attended", "sum"),
            total_classes=("total_classes", "sum"),
            overall_raw_marks=("raw_total", "sum"),
            average_marks=("normalized_score", "mean"),
            final_exam_avg=("final", "mean"),
            mid1_avg=("mid1", "mean"),
            mid2_avg=("mid2", "mean"),
            internal_avg=("internal", "mean"),
            assignment_avg=("assignment", "mean"),
            passed_subjects_count=("subject_passed", "sum")
        ).reset_index()

        # Calculate student-level attendance percentage
        student_summary["overall_attendance_pct"] = (
            (student_summary["total_attended"] / student_summary["total_classes"]) * 100
        ).round(1)
        
        # Round averages
        student_summary["average_marks"] = student_summary["average_marks"].round(1)
        student_summary["final_exam_avg"] = student_summary["final_exam_avg"].round(1)
        student_summary["mid1_avg"] = student_summary["mid1_avg"].round(1)
        student_summary["mid2_avg"] = student_summary["mid2_avg"].round(1)
        student_summary["internal_avg"] = student_summary["internal_avg"].round(1)
        student_summary["assignment_avg"] = student_summary["assignment_avg"].round(1)
        
        # GPA (on 10.0 scale)
        student_summary["gpa"] = (student_summary["average_marks"] / 10.0).round(2)
        
        # Academic and Attendance standing
        student_summary["performance_category"] = student_summary["average_marks"].apply(assign_performance_category)
        student_summary["attendance_category"] = student_summary["overall_attendance_pct"].apply(assign_attendance_category)
        
        # Pass Status: Student passes only if they pass ALL enrolled subjects
        student_summary["failed_subjects_count"] = student_summary["total_subjects"] - student_summary["passed_subjects_count"]
        student_summary["all_passed"] = student_summary["failed_subjects_count"] == 0
        student_summary["pass_status"] = student_summary["all_passed"].apply(lambda x: "Passed" if x else "Failed")
        
        # Risk assessment:
        # At Risk if attendance < 75% OR average marks < 50% OR failed >= 1 subject
        def determine_risk(row):
            reasons = []
            if row["overall_attendance_pct"] < 75.0:
                reasons.append("Low Attendance")
            if row["average_marks"] < 50.0:
                reasons.append("Low Marks")
            if row["failed_subjects_count"] > 0:
                reasons.append("Subject Backlog")
                
            if len(reasons) >= 2:
                return "High Risk"
            elif len(reasons) == 1:
                return "Moderate Risk"
            else:
                return "Low Risk / Safe"
                
        student_summary["risk_level"] = student_summary.apply(determine_risk, axis=1)
        
        # Rank students by average marks within their department
        student_summary["dept_rank"] = student_summary.groupby("department")["average_marks"].rank(
            ascending=False, method="dense"
        ).astype(int)
        
        # Overall Rank
        student_summary["overall_rank"] = student_summary["average_marks"].rank(
            ascending=False, method="dense"
        ).astype(int)

        if save_master:
            os.makedirs(self.processed_data_dir, exist_ok=True)
            df_full_details.to_csv(
                os.path.join(self.processed_data_dir, "subject_performance_detailed.csv"),
                index=False
            )
            student_summary.to_csv(
                os.path.join(self.processed_data_dir, "master_student_summary.csv"),
                index=False
            )
            print(f"Master datasets successfully saved in '{self.processed_data_dir}'")
            
        return df_full_details, student_summary

if __name__ == "__main__":
    from data_cleaning import DataCleaner
    cleaner = DataCleaner()
    stus, mrks, att, _ = cleaner.clean_all()
    processor = DataProcessor()
    df_details, df_summary = processor.process_and_merge(stus, mrks, att)
    print("Processing sample:")
    print(df_summary[["student_id", "name", "department", "average_marks", "overall_attendance_pct", "performance_category", "risk_level"]].head())
