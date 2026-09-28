"""
Module: file_uploader.py
Purpose: Ultra-flexible parser that accepts virtually ANY messy academic dataset:
- Auto-detects multi-sheet Excel, wide-format tables (subjects as columns), or standard long tables
- Auto-generates student IDs if missing
- Automatically cleans strings in numeric columns ("85%", "Absent", "AB", "N/A")
- Fuzzy maps arbitrary column headers (Roll No, Candidate Name, Branch, Presences, etc.)
"""

import io
import re
import pandas as pd
import numpy as np

def clean_numeric_series(series, default=0.0):
    """Cleans dirty string values ('85%', 'Absent', 'AB', 'N/A') into pure floats."""
    def clean_val(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip().lower()
        if s in ["absent", "ab", "fail", "na", "n/a", "null", "none", "-", ""]:
            return 0.0
        # Remove %, $, and commas
        cleaned = re.sub(r"[^\d.-]", "", s)
        try:
            return float(cleaned) if cleaned else default
        except ValueError:
            return default
    return series.apply(clean_val)

def parse_uploaded_academic_data(main_file, marks_file=None, att_file=None):
    """
    Intelligently parses any messy Excel or CSV file into standard DataFrames:
    (df_students, df_marks, df_attendance, format_description)
    """
    def read_any(file_obj):
        name = getattr(file_obj, "name", "").lower()
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(file_obj)
        else:
            try:
                return pd.read_csv(file_obj)
            except Exception:
                file_obj.seek(0)
                return pd.read_csv(file_obj, encoding="latin1")

    # Case 1: Three separate files uploaded
    if marks_file is not None and att_file is not None:
        df_st = read_any(main_file)
        df_mk = read_any(marks_file)
        df_at = read_any(att_file)
        return df_st, df_mk, df_at, "Three Separate Files (Students, Marks, Attendance)"

    # Case 2: Single file uploaded (check if multi-sheet Excel)
    fname = getattr(main_file, "name", "").lower()
    if fname.endswith(".xlsx") or fname.endswith(".xls"):
        try:
            excel_file = pd.ExcelFile(main_file)
            sheet_names = [s.lower().strip() for s in excel_file.sheet_names]
            
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
                return df_st, df_mk, df_at, f"Multi-Sheet Excel Workbook ({st_sheet}, {mk_sheet}, {at_sheet})"
        except Exception:
            pass

    # Case 3: Single Table (CSV or single Excel sheet)
    df_raw = read_any(main_file)
    
    # Drop completely empty rows and columns
    df_raw = df_raw.dropna(how="all").dropna(axis=1, how="all")
    
    # Fuzzy normalize column headers
    col_map = {}
    known_id_cols = ["student_id", "roll_no", "rollno", "roll", "reg_no", "regno", "id", "usn", "htno", "hallticket"]
    known_name_cols = ["name", "student_name", "candidate_name", "full_name", "student"]
    known_dept_cols = ["department", "dept", "branch", "stream", "course_branch"]
    known_year_cols = ["year", "academic_year", "sem", "semester"]
    known_sec_cols = ["section", "sec"]
    known_gender_cols = ["gender", "sex"]
    known_subj_cols = ["subject", "course", "subject_name", "paper"]
    known_internal_cols = ["internal", "internals", "cie", "ia"]
    known_mid1_cols = ["mid1", "mid_1", "midterm1", "midterm_1", "t1", "test1"]
    known_mid2_cols = ["mid2", "mid_2", "midterm2", "midterm_2", "t2", "test2"]
    known_assign_cols = ["assignment", "assignments", "project", "quiz", "task"]
    known_final_cols = ["final", "final_exam", "see", "external", "marks", "score", "total_marks", "grade_score"]
    known_tot_cls_cols = ["total_classes", "total_sessions", "total_lectures", "held", "classes_held"]
    known_att_cols = ["attended", "classes_attended", "sessions_attended", "attendance", "present", "attendance_pct", "attendance%"]

    for col in df_raw.columns:
        c_clean = re.sub(r"[^a-zA-Z0-9%]", "", str(col).lower())
        if any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_id_cols):
            col_map[col] = "student_id"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_name_cols):
            col_map[col] = "name"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_dept_cols):
            col_map[col] = "department"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_year_cols):
            col_map[col] = "year"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_sec_cols):
            col_map[col] = "section"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_gender_cols):
            col_map[col] = "gender"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_subj_cols):
            col_map[col] = "subject"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_internal_cols):
            col_map[col] = "internal"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_mid1_cols):
            col_map[col] = "mid1"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_mid2_cols):
            col_map[col] = "mid2"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_assign_cols):
            col_map[col] = "assignment"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_final_cols):
            col_map[col] = "final"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_tot_cls_cols):
            col_map[col] = "total_classes"
        elif any(c_clean == re.sub(r"[^a-zA-Z0-9%]", "", k) for k in known_att_cols):
            col_map[col] = "attended"

    df_renamed = df_raw.rename(columns=col_map).copy()

    # If missing student_id, auto-generate sequential IDs: 1001, 1002...
    if "student_id" not in df_renamed.columns:
        df_renamed["student_id"] = [1001 + i for i in range(len(df_renamed))]
    else:
        # Clean ID
        df_renamed["student_id"] = clean_numeric_series(df_renamed["student_id"]).fillna(1001).astype(int)

    # Check for Wide-Format Table (e.g. Columns are: Roll, Name, Python, Java, DBMS...)
    demographic_keys = ["student_id", "name", "department", "year", "section", "gender", "total_classes", "attended"]
    potential_subject_cols = [c for c in df_renamed.columns if c not in demographic_keys and c not in ["subject", "internal", "mid1", "mid2", "assignment", "final"]]
    
    # If there is no 'subject' column, but multiple unknown columns exist, melt them as subjects!
    if "subject" not in df_renamed.columns and len(potential_subject_cols) >= 2:
        id_vars = [c for c in df_renamed.columns if c in demographic_keys]
        df_melted = pd.melt(
            df_renamed,
            id_vars=id_vars,
            value_vars=potential_subject_cols,
            var_name="subject",
            value_name="final"
        )
        df_renamed = df_melted
        format_detected = f"Wide-Format Table Auto-Reshaped (Subjects: {', '.join(potential_subject_cols[:4])})"
    else:
        format_detected = "Standard Table Format"

    # Fill defaults for missing demographic fields
    if "name" not in df_renamed.columns:
        df_renamed["name"] = df_renamed["student_id"].apply(lambda x: f"Student {x}")
    if "department" not in df_renamed.columns:
        df_renamed["department"] = "General Engineering"
    if "year" not in df_renamed.columns:
        df_renamed["year"] = 3
    if "section" not in df_renamed.columns:
        df_renamed["section"] = "A"
    if "gender" not in df_renamed.columns:
        df_renamed["gender"] = "Unspecified"
    if "subject" not in df_renamed.columns:
        df_renamed["subject"] = "General Course"

    # Clean numerical columns
    if "final" not in df_renamed.columns:
        df_renamed["final"] = 70.0
    else:
        df_renamed["final"] = clean_numeric_series(df_renamed["final"], default=65.0)

    if "internal" not in df_renamed.columns:
        df_renamed["internal"] = (df_renamed["final"] / 100.0 * 20.0).round(1)
    else:
        df_renamed["internal"] = clean_numeric_series(df_renamed["internal"], default=15.0)

    if "mid1" not in df_renamed.columns:
        df_renamed["mid1"] = (df_renamed["final"] / 100.0 * 25.0).round(1)
    else:
        df_renamed["mid1"] = clean_numeric_series(df_renamed["mid1"], default=18.0)

    if "mid2" not in df_renamed.columns:
        df_renamed["mid2"] = df_renamed["mid1"]
    else:
        df_renamed["mid2"] = clean_numeric_series(df_renamed["mid2"], default=19.0)

    if "assignment" not in df_renamed.columns:
        df_renamed["assignment"] = (df_renamed["final"] / 100.0 * 10.0).round(1)
    else:
        df_renamed["assignment"] = clean_numeric_series(df_renamed["assignment"], default=8.0)

    # Attendance handling
    if "total_classes" not in df_renamed.columns:
        df_renamed["total_classes"] = 50
    else:
        df_renamed["total_classes"] = clean_numeric_series(df_renamed["total_classes"], default=50.0).astype(int)

    if "attended" not in df_renamed.columns:
        df_renamed["attended"] = (df_renamed["total_classes"] * 0.8).astype(int)
    else:
        # If attended was given as percentage (e.g. 85%), scale it
        att_cleaned = clean_numeric_series(df_renamed["attended"], default=40.0)
        df_renamed["attended"] = att_cleaned.apply(
            lambda v: int(v if v <= 50 else round((v / 100.0) * 50))
        )

    # Extract clean entities
    st_cols = ["student_id", "name", "department", "year", "section", "gender"]
    df_st = df_renamed[st_cols].drop_duplicates(subset=["student_id"]).reset_index(drop=True)
    
    mk_cols = ["student_id", "subject", "internal", "mid1", "mid2", "assignment", "final"]
    df_mk = df_renamed[mk_cols].reset_index(drop=True)
    
    at_cols = ["student_id", "subject", "total_classes", "attended"]
    df_at = df_renamed[at_cols].reset_index(drop=True)

    return df_st, df_mk, df_at, format_detected

def generate_sample_excel_template():
    """Generates an in-memory multi-sheet sample Excel file for users to download and test."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([
            {"student_id": 2001, "name": "Aarav Patel", "department": "CSE", "year": 3, "section": "A", "gender": "Male"},
            {"student_id": 2002, "name": "Diya Nair", "department": "AIDS", "year": 3, "section": "A", "gender": "Female"},
            {"student_id": 2003, "name": "Rohan Gupta", "department": "IT", "year": 3, "section": "B", "gender": "Male"}
        ]).to_excel(writer, sheet_name="Students", index=False)
        
        pd.DataFrame([
            {"student_id": 2001, "subject": "Python", "internal": 18, "mid1": 22, "mid2": 24, "assignment": 9, "final": 82},
            {"student_id": 2001, "subject": "DBMS", "internal": 17, "mid1": 20, "mid2": 21, "assignment": 8, "final": 74},
            {"student_id": 2002, "subject": "Python", "internal": 20, "mid1": 25, "mid2": 25, "assignment": 10, "final": 90},
            {"student_id": 2002, "subject": "DBMS", "internal": 19, "mid1": 23, "mid2": 24, "assignment": 9, "final": 88},
            {"student_id": 2003, "subject": "Python", "internal": 14, "mid1": 15, "mid2": 16, "assignment": 7, "final": 58},
            {"student_id": 2003, "subject": "DBMS", "internal": 12, "mid1": 14, "mid2": 15, "assignment": 6, "final": 52}
        ]).to_excel(writer, sheet_name="Marks", index=False)
        
        pd.DataFrame([
            {"student_id": 2001, "subject": "Python", "total_classes": 50, "attended": 44},
            {"student_id": 2001, "subject": "DBMS", "total_classes": 48, "attended": 40},
            {"student_id": 2002, "subject": "Python", "total_classes": 50, "attended": 48},
            {"student_id": 2002, "subject": "DBMS", "total_classes": 48, "attended": 46},
            {"student_id": 2003, "subject": "Python", "total_classes": 50, "attended": 32},
            {"student_id": 2003, "subject": "DBMS", "total_classes": 48, "attended": 29}
        ]).to_excel(writer, sheet_name="Attendance", index=False)
        
    return output.getvalue()
