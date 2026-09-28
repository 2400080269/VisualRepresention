"""
Module: database.py
Purpose: Database management, SQLite/MySQL persistence, schema creation,
and analytical query execution for the Student Performance Analytics Platform.
"""

import os
import sqlite3
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path="data/student_performance.db", schema_path="sql/schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        """Returns a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Applies the SQL schema to create all required tables and indices."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found at: {self.schema_path}")
            
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            print(f"Database schema initialized successfully at '{self.db_path}'")

    def populate_database(self, df_students, df_details, df_summary):
        """
        Inserts processed dataframes into the respective relational database tables:
        - students: Student demographics
        - marks: Detailed course marks (including normalized_score, raw_total, subject_passed)
        - attendance: Subject-level attendance (including attendance_pct)
        - student_summary: Aggregated student performance profiles
        """
        self.init_database()
        with self.get_connection() as conn:
            # 1. Populate students
            student_cols = ["student_id", "name", "department", "year", "section", "gender"]
            existing_st_cols = [c for c in student_cols if c in df_students.columns]
            df_students[existing_st_cols].to_sql("students", conn, if_exists="replace", index=False)
            
            # 2. Populate marks with calculated scores and pass status
            marks_cols = [
                "student_id", "subject", "internal", "mid1", "mid2", "assignment", 
                "final", "raw_total", "normalized_score", "subject_passed", "subject_performance_cat"
            ]
            existing_m_cols = [c for c in marks_cols if c in df_details.columns]
            df_details[existing_m_cols].to_sql("marks", conn, if_exists="replace", index=False)
            
            # 3. Populate attendance with attendance_pct
            att_cols = ["student_id", "subject", "total_classes", "attended", "attendance_pct"]
            existing_att_cols = [c for c in att_cols if c in df_details.columns]
            df_details[existing_att_cols].to_sql("attendance", conn, if_exists="replace", index=False)
            
            # 4. Populate student summary
            df_summary.to_sql("student_summary", conn, if_exists="replace", index=False)
            
            # Recreate indices if replaced
            try:
                cursor = conn.cursor()
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department, year, section);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_marks_student_subject ON marks(student_id, subject);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_perf ON student_summary(performance_category, risk_level);")
                conn.commit()
            except Exception as e:
                print(f"Index creation notice: {e}")
                
            print(f"Successfully populated database tables: students ({len(df_students)}), marks ({len(df_details)}), attendance ({len(df_details)}), student_summary ({len(df_summary)})")

    def run_query(self, query, params=None):
        """
        Executes a SQL query and returns results as a pandas DataFrame.
        """
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)

    # Pre-built analytical queries matching core project questions
    def get_department_benchmarks(self):
        query = """
        SELECT 
            department,
            COUNT(student_id) AS total_students,
            ROUND(AVG(average_marks), 2) AS dept_avg_marks,
            ROUND(AVG(overall_attendance_pct), 2) AS dept_avg_attendance,
            ROUND(AVG(gpa), 2) AS dept_avg_gpa
        FROM student_summary
        GROUP BY department
        ORDER BY dept_avg_marks DESC;
        """
        return self.run_query(query)

    def get_subject_statistics(self):
        query = """
        SELECT 
            subject,
            COUNT(student_id) AS total_enrolled,
            ROUND(AVG(normalized_score), 2) AS subject_avg_marks,
            ROUND(MIN(normalized_score), 1) AS lowest_marks,
            ROUND(MAX(normalized_score), 1) AS highest_marks,
            SUM(CASE WHEN subject_passed = 1 THEN 1 ELSE 0 END) AS total_passed,
            SUM(CASE WHEN subject_passed = 0 THEN 1 ELSE 0 END) AS total_failed,
            ROUND((SUM(CASE WHEN subject_passed = 1 THEN 1.0 ELSE 0.0 END) / COUNT(student_id)) * 100.0, 2) AS pass_percentage
        FROM marks
        GROUP BY subject
        ORDER BY subject_avg_marks ASC;
        """
        return self.run_query(query)

    def get_at_risk_students(self):
        query = """
        SELECT 
            student_id,
            name,
            department,
            year,
            section,
            average_marks,
            overall_attendance_pct,
            risk_level,
            performance_category
        FROM student_summary
        WHERE risk_level IN ('High Risk', 'Moderate Risk')
        ORDER BY risk_level ASC, overall_attendance_pct ASC;
        """
        return self.run_query(query)

    def get_attendance_tier_correlation(self):
        query = """
        SELECT 
            attendance_category,
            COUNT(student_id) AS student_count,
            ROUND(AVG(average_marks), 2) AS avg_marks,
            ROUND(MIN(average_marks), 2) AS min_marks,
            ROUND(MAX(average_marks), 2) AS max_marks,
            ROUND(SUM(CASE WHEN pass_status = 'Passed' THEN 1.0 ELSE 0.0 END) / COUNT(student_id) * 100.0, 2) AS pass_rate
        FROM student_summary
        GROUP BY attendance_category
        ORDER BY avg_marks DESC;
        """
        return self.run_query(query)

if __name__ == "__main__":
    db = DatabaseManager()
    print("Database Manager ready.")
