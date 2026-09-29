"""
Module: data_cleaning.py
Purpose: Comprehensive data validation, anomaly detection, deduplication, 
and missing value imputation for the Student Performance Analytics Platform.
"""

import os
import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self, raw_data_dir="data/raw"):
        self.raw_data_dir = raw_data_dir
        self.cleaning_audit_log = []
        
    def _log_audit(self, step, message, rows_affected=0):
        log_entry = {
            "step": step,
            "message": message,
            "rows_affected": rows_affected
        }
        self.cleaning_audit_log.append(log_entry)
        print(f"[{step}] {message} (Affected: {rows_affected})")

    def clean_students(self, df_students=None):
        if df_students is None:
            path = os.path.join(self.raw_data_dir, "students.csv")
            df_students = pd.read_csv(path)
            
        initial_count = len(df_students)
        
        # 1. Deduplication
        duplicates = df_students.duplicated(subset=["student_id"]).sum()
        if duplicates > 0:
            df_students = df_students.drop_duplicates(subset=["student_id"], keep="first")
            self._log_audit("Students: Deduplication", "Removed duplicate student records", duplicates)
            
        # 2. Missing Values Check
        # Check Name
        missing_names = df_students["name"].isnull().sum()
        if missing_names > 0:
            # Impute unknown names with 'Student_<id>'
            df_students["name"] = df_students.apply(
                lambda row: f"Student {row['student_id']}" if pd.isna(row["name"]) else str(row["name"]).strip(),
                axis=1
            )
            self._log_audit("Students: Missing Names", "Imputed missing student names with default identifier", missing_names)
            
        # Check Department
        missing_dept = df_students["department"].isnull().sum()
        if missing_dept > 0:
            # Impute with most frequent department or 'General'
            mode_dept = df_students["department"].mode()[0] if not df_students["department"].dropna().empty else "AIDS"
            df_students["department"] = df_students["department"].fillna(mode_dept)
            self._log_audit("Students: Missing Department", f"Imputed missing departments with mode ({mode_dept})", missing_dept)
            
        # Check Year and Section
        df_students["year"] = pd.to_numeric(df_students["year"], errors="coerce").fillna(3).astype(int)
        df_students["section"] = df_students["section"].fillna("A").astype(str).str.upper()
        df_students["gender"] = df_students["gender"].fillna("Unspecified").astype(str).str.capitalize()
        
        self._log_audit("Students: Completed", f"Cleaned students dataset. Count: {len(df_students)} (was {initial_count})")
        return df_students.reset_index(drop=True)

    def clean_marks(self, df_marks=None):
        if df_marks is None:
            path = os.path.join(self.raw_data_dir, "marks.csv")
            df_marks = pd.read_csv(path)
            
        initial_count = len(df_marks)
        
        # 1. Deduplication (same student_id and subject)
        duplicates = df_marks.duplicated(subset=["student_id", "subject"]).sum()
        if duplicates > 0:
            df_marks = df_marks.drop_duplicates(subset=["student_id", "subject"], keep="first")
            self._log_audit("Marks: Deduplication", "Removed duplicate marks records for same student & subject", duplicates)
            
        # 2. Component constraints and boundaries
        # internal: [0, 20], mid1: [0, 25], mid2: [0, 25], assignment: [0, 10], final: [0, 100]
        component_limits = {
            "internal": (0, 20),
            "mid1": (0, 25),
            "mid2": (0, 25),
            "assignment": (0, 10),
            "final": (0, 100)
        }
        
        for col, (min_val, max_val) in component_limits.items():
            if col in df_marks.columns:
                # Handle missing with median for that subject
                missing_count = df_marks[col].isnull().sum()
                if missing_count > 0:
                    df_marks[col] = df_marks.groupby("subject")[col].transform(
                        lambda x: x.fillna(round(x.median()))
                    )
                    # If still any null (in case entire group null), fill with half of max_val
                    df_marks[col] = df_marks[col].fillna(round(max_val * 0.6))
                    self._log_audit(f"Marks: Missing {col}", f"Imputed missing {col} marks with subject median", missing_count)
                
                # Check out of range values
                invalid_mask = (df_marks[col] < min_val) | (df_marks[col] > max_val)
                invalid_count = invalid_mask.sum()
                if invalid_count > 0:
                    df_marks[col] = df_marks[col].clip(lower=min_val, upper=max_val)
                    self._log_audit(f"Marks: Out-of-bounds {col}", f"Clipped invalid {col} marks to [{min_val}, {max_val}]", invalid_count)
                    
                df_marks[col] = df_marks[col].round(1)

        self._log_audit("Marks: Completed", f"Cleaned marks dataset. Count: {len(df_marks)} (was {initial_count})")
        return df_marks.reset_index(drop=True)

    def clean_attendance(self, df_attendance=None):
        if df_attendance is None:
            path = os.path.join(self.raw_data_dir, "attendance.csv")
            df_attendance = pd.read_csv(path)
            
        initial_count = len(df_attendance)
        
        # 1. Deduplication
        duplicates = df_attendance.duplicated(subset=["student_id", "subject"]).sum()
        if duplicates > 0:
            df_attendance = df_attendance.drop_duplicates(subset=["student_id", "subject"], keep="first")
            self._log_audit("Attendance: Deduplication", "Removed duplicate attendance entries", duplicates)
            
        # 2. Total classes sanity check (> 0)
        df_attendance["total_classes"] = pd.to_numeric(df_attendance["total_classes"], errors="coerce").fillna(50)
        df_attendance["total_classes"] = df_attendance["total_classes"].apply(lambda x: 50 if x <= 0 else int(x))
        
        # 3. Attended classes sanity check (0 <= attended <= total_classes)
        missing_att = df_attendance["attended"].isnull().sum()
        if missing_att > 0:
            # Impute with average attendance (approx 75% of total_classes)
            df_attendance["attended"] = df_attendance["attended"].fillna(round(df_attendance["total_classes"] * 0.75))
            self._log_audit("Attendance: Missing attended", "Imputed missing attended count with 75% class baseline", missing_att)
            
        # Check invalid attended > total_classes or negative
        invalid_att = ((df_attendance["attended"] > df_attendance["total_classes"]) | (df_attendance["attended"] < 0)).sum()
        if invalid_att > 0:
            df_attendance["attended"] = df_attendance.apply(
                lambda row: min(max(0, row["attended"]), row["total_classes"]),
                axis=1
            )
            self._log_audit("Attendance: Out-of-bounds", "Corrected attendance exceeding total classes or negative", invalid_att)
            
        df_attendance["attended"] = df_attendance["attended"].astype(int)
        df_attendance["total_classes"] = df_attendance["total_classes"].astype(int)
        
        self._log_audit("Attendance: Completed", f"Cleaned attendance dataset. Count: {len(df_attendance)} (was {initial_count})")
        return df_attendance.reset_index(drop=True)

    def clean_all(self, save_processed=True, processed_dir="data/processed"):
        os.makedirs(processed_dir, exist_ok=True)
        
        students_clean = self.clean_students()
        marks_clean = self.clean_marks()
        attendance_clean = self.clean_attendance()
        
        if save_processed:
            students_clean.to_csv(os.path.join(processed_dir, "students_cleaned.csv"), index=False)
            marks_clean.to_csv(os.path.join(processed_dir, "marks_cleaned.csv"), index=False)
            attendance_clean.to_csv(os.path.join(processed_dir, "attendance_cleaned.csv"), index=False)
            
            # Save audit log
            df_audit = pd.DataFrame(self.cleaning_audit_log)
            df_audit.to_csv(os.path.join(processed_dir, "cleaning_audit_log.csv"), index=False)
            print(f"Cleaned datasets and audit log successfully saved to '{processed_dir}'")
            
        return students_clean, marks_clean, attendance_clean, self.cleaning_audit_log

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.clean_all()

