"""
Module: file_uploader.py
Purpose: Parses user-uploaded Excel (.xlsx/.xls) or CSV files into standard DataFrames
supporting multi-sheet Excel workbooks, combined single-table files, and multiple individual files.
"""

import io
import pandas as pd
import numpy as np

def parse_uploaded_academic_data(main_file, marks_file=None, att_file=None):
    """
    Parses uploaded file(s) into:
    (df_students, df_marks, df_attendance, format_description)
    """
    def read_any(file_obj):
        name = getattr(file_obj, "name", "").lower()
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(file_obj)
        else:
            return pd.read_csv(file_obj)

    # Case 1: Three individual files provided
    if marks_file is not None and att_file is not None:
        df_st = read_any(main_file)
        df_mk = read_any(marks_file)
        df_at = read_any(att_file)
        return df_st, df_mk, df_at, "Three Separate Files (Students, Marks, Attendance)"

    # Case 2: Single file provided (could be multi-sheet Excel or unified table)
    fname = getattr(main_file, "name", "").lower()
    
    if fname.endswith(".xlsx") or fname.endswith(".xls"):
        excel_file = pd.ExcelFile(main_file)
        sheet_names = [s.lower().strip() for s in excel_file.sheet_names]
        
        # Check for multi-sheet layout
        has_students = any("student" in s for s in sheet_names)
        has_marks = any("mark" in s or "grade" in s or "score" in s for s in sheet_names)
        has_att = any("attend" in s for s in sheet_names)
        
        if has_students and has_marks and has_att:
            st_sheet = [s for s in excel_file.sheet_names if "student" in s.lower()][0]
            mk_sheet = [s for s in excel_file.sheet_names if any(w in s.lower() for w in ["mark", "grade", "score"])][0]
            at_sheet = [s for s in excel_file.sheet_names if "attend" in s.lower()][0]
            
            df_st = pd.read_excel(main_file, sheet_name=st_sheet)
            df_mk = pd.read_excel(main_file, sheet_name=mk_sheet)
            df_at = pd.read_excel(main_file, sheet_name=at_sheet)
            return df_st, df_mk, df_at, f"Multi-Sheet Excel Workbook (Sheets: {st_sheet}, {mk_sheet}, {at_sheet})"

    # Case 3: Single combined table (CSV or single-sheet Excel)
    df_combined = read_any(main_file)
    cols = [c.lower().strip() for c in df_combined.columns]
    
    # Check if this is a single unified table with demographics + marks + attendance
    required_st = ["student_id"]
    if not any("student_id" in c or "roll" in c or "id" in c for c in cols):
        raise ValueError("Uploaded file is missing a 'student_id' or 'Roll No' column.")

    # Normalize column names to standard lowercase
    col_map = {}
    for col in df_combined.columns:
        c_low = col.lower().strip()
        if c_low in ["student_id", "roll_no", "rollno", "roll", "id"]:
            col_map[col] = "student_id"
        elif c_low in ["student_name", "name", "full_name"]:
            col_map[col] = "name"
        elif c_low in ["department", "dept", "branch"]:
            col_map[col] = "department"
        elif c_low in ["year", "academic_year"]:
            col_map[col] = "year"
        elif c_low in ["section", "sec"]:
            col_map[col] = "section"
        elif c_low in ["gender", "sex"]:
            col_map[col] = "gender"
        elif c_low in ["subject", "course", "subject_name"]:
            col_map[col] = "subject"
        elif c_low in ["internal", "internals", "cie"]:
            col_map[col] = "internal"
        elif c_low in ["mid1", "mid_1", "midterm1"]:
            col_map[col] = "mid1"
        elif c_low in ["mid2", "mid_2", "midterm2"]:
            col_map[col] = "mid2"
        elif c_low in ["assignment", "assignments", "project"]:
            col_map[col] = "assignment"
        elif c_low in ["final", "final_exam", "see", "external"]:
            col_map[col] = "final"
        elif c_low in ["total_classes", "total_sessions", "total_lectures"]:
            col_map[col] = "total_classes"
        elif c_low in ["attended", "classes_attended", "sessions_attended"]:
            col_map[col] = "attended"
            
    df_combined = df_combined.rename(columns=col_map)
    
    # Fill any missing critical columns with standard defaults
    if "name" not in df_combined.columns:
        df_combined["name"] = df_combined["student_id"].apply(lambda x: f"Student {x}")
    if "department" not in df_combined.columns:
        df_combined["department"] = "General"
    if "year" not in df_combined.columns:
        df_combined["year"] = 3
    if "section" not in df_combined.columns:
        df_combined["section"] = "A"
    if "gender" not in df_combined.columns:
        df_combined["gender"] = "Unspecified"
    if "subject" not in df_combined.columns:
        df_combined["subject"] = "General Course"
    if "internal" not in df_combined.columns:
        df_combined["internal"] = 15.0
    if "mid1" not in df_combined.columns:
        df_combined["mid1"] = 18.0
    if "mid2" not in df_combined.columns:
        df_combined["mid2"] = 19.0
    if "assignment" not in df_combined.columns:
        df_combined["assignment"] = 8.0
    if "final" not in df_combined.columns:
        df_combined["final"] = 70.0
    if "total_classes" not in df_combined.columns:
        df_combined["total_classes"] = 50
    if "attended" not in df_combined.columns:
        df_combined["attended"] = 40

    # Extract distinct student demographics
    st_cols = ["student_id", "name", "department", "year", "section", "gender"]
    df_st = df_combined[st_cols].drop_duplicates(subset=["student_id"]).reset_index(drop=True)
    
    # Extract marks
    mk_cols = ["student_id", "subject", "internal", "mid1", "mid2", "assignment", "final"]
    df_mk = df_combined[mk_cols].reset_index(drop=True)
    
    # Extract attendance
    at_cols = ["student_id", "subject", "total_classes", "attended"]
    df_at = df_combined[at_cols].reset_index(drop=True)
    
    return df_st, df_mk, df_at, "Unified Single-Table Dataset"

def generate_sample_excel_template():
    """Generates an in-memory multi-sheet sample Excel file for users to download and test."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sample Students
        pd.DataFrame([
            {"student_id": 2001, "name": "Aarav Patel", "department": "CSE", "year": 3, "section": "A", "gender": "Male"},
            {"student_id": 2002, "name": "Diya Nair", "department": "AIDS", "year": 3, "section": "A", "gender": "Female"},
            {"student_id": 2003, "name": "Rohan Gupta", "department": "IT", "year": 3, "section": "B", "gender": "Male"}
        ]).to_excel(writer, sheet_name="Students", index=False)
        
        # Sample Marks
        pd.DataFrame([
            {"student_id": 2001, "subject": "Python", "internal": 18, "mid1": 22, "mid2": 24, "assignment": 9, "final": 82},
            {"student_id": 2001, "subject": "DBMS", "internal": 17, "mid1": 20, "mid2": 21, "assignment": 8, "final": 74},
            {"student_id": 2002, "subject": "Python", "internal": 20, "mid1": 25, "mid2": 25, "assignment": 10, "final": 90},
            {"student_id": 2002, "subject": "DBMS", "internal": 19, "mid1": 23, "mid2": 24, "assignment": 9, "final": 88},
            {"student_id": 2003, "subject": "Python", "internal": 14, "mid1": 15, "mid2": 16, "assignment": 7, "final": 58},
            {"student_id": 2003, "subject": "DBMS", "internal": 12, "mid1": 14, "mid2": 15, "assignment": 6, "final": 52}
        ]).to_excel(writer, sheet_name="Marks", index=False)
        
        # Sample Attendance
        pd.DataFrame([
            {"student_id": 2001, "subject": "Python", "total_classes": 50, "attended": 44},
            {"student_id": 2001, "subject": "DBMS", "total_classes": 48, "attended": 40},
            {"student_id": 2002, "subject": "Python", "total_classes": 50, "attended": 48},
            {"student_id": 2002, "subject": "DBMS", "total_classes": 48, "attended": 46},
            {"student_id": 2003, "subject": "Python", "total_classes": 50, "attended": 32},
            {"student_id": 2003, "subject": "DBMS", "total_classes": 48, "attended": 29}
        ]).to_excel(writer, sheet_name="Attendance", index=False)
        
    return output.getvalue()
