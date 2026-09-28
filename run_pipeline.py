"""
Script: run_pipeline.py
Purpose: Master end-to-end pipeline orchestrator.
Executes:
1. Synthetic raw dataset generation (with controlled anomalies)
2. Comprehensive data cleaning and audit logging
3. Feature engineering and analytical summary computation
4. SQLite relational database schema creation and table population
5. Machine learning model training (grade classification + regressor)
6. Generation of high-level validation diagnostics
"""

import sys
import os
import time

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from generate_data import generate_student_datasets
from data_cleaning import DataCleaner
from data_processing import DataProcessor
from database import DatabaseManager
from ml_predictor import StudentPerformancePredictor

def run_full_pipeline(num_students=150, force_regenerate=True):
    print("=" * 70)
    print(">>> STARTING STUDENT PERFORMANCE ANALYTICS PIPELINE")
    print("=" * 70)
    start_time = time.time()
    
    # -------------------------------------------------------------
    # Step 1: Raw Data Ingestion / Generation
    # -------------------------------------------------------------
    raw_dir = "data/raw"
    students_raw_file = os.path.join(raw_dir, "students.csv")
    
    if force_regenerate or not os.path.exists(students_raw_file):
        print(f"\n[1/5] Ingesting/Generating raw datasets in '{raw_dir}' (Count: {num_students})...")
        generate_student_datasets(output_dir=raw_dir, num_students=num_students)
    else:
        print(f"\n[1/5] Using existing raw datasets from '{raw_dir}'...")

    # -------------------------------------------------------------
    # Step 2: Data Cleaning & Anomaly Resolution
    # -------------------------------------------------------------
    print("\n[2/5] Executing Data Cleaning Pipeline...")

    cleaner = DataCleaner(raw_data_dir=raw_dir)
    df_students_clean, df_marks_clean, df_att_clean, audit_log = cleaner.clean_all(
        save_processed=True, processed_dir="data/processed"
    )
    print(f" -> Completed data cleaning. Resolved {len(audit_log)} audit events.")

    # -------------------------------------------------------------
    # Step 3: Feature Engineering & Master Data Aggregation
    # -------------------------------------------------------------
    print("\n[3/5] ⚙️ Executing Feature Engineering & Metric Calculations...")
    processor = DataProcessor(processed_data_dir="data/processed")
    df_details, df_summary = processor.process_and_merge(
        df_students_clean, df_marks_clean, df_att_clean, save_master=True
    )
    print(f" -> Processed {len(df_summary)} student profiles and {len(df_details)} course enrollments.")
    print(f" -> Overall Average Marks: {df_summary['average_marks'].mean():.2f}%")
    print(f" -> Overall Pass Rate: {((df_summary['pass_status'] == 'Passed').mean() * 100):.1f}%")
    print(f" -> Overall Average Attendance: {df_summary['overall_attendance_pct'].mean():.1f}%")

    # -------------------------------------------------------------
    # Step 4: Relational SQL Database Population
    # -------------------------------------------------------------
    print("\n[4/5] [DB] Ingesting cleaned data into Relational SQLite Database...")
    db = DatabaseManager(db_path="data/student_performance.db", schema_path="sql/schema.sql")
    db.populate_database(df_students_clean, df_details, df_summary)

    # -------------------------------------------------------------
    # Step 5: Machine Learning Model Training
    # -------------------------------------------------------------
    print("\n[5/5] [ML] Training Machine Learning Grade Predictor & Regressor...")
    predictor = StudentPerformancePredictor(model_dir="data/models")
    metrics = predictor.train_models(df_details)
    print(f" -> Classifier Test Accuracy: {metrics['classifier_accuracy']}%")
    print(f" -> Regressor Test R^2 Score: {metrics['regressor_r2']}")
    print(f" -> Top Feature Weights: {metrics['feature_importances']}")

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 70)
    print(f"[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s")
    print("=" * 70)
    print("Ready to launch the Streamlit Interactive Dashboard:")
    print("Run command:  streamlit run dashboard/app.py")
    print("=" * 70)

if __name__ == "__main__":
    run_full_pipeline()
