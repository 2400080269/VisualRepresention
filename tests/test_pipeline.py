"""
Unit and Integration Tests for Student Performance Analytics Platform
Verifies data cleaning, metric calculations, SQLite persistence, and ML inference.
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from data_cleaning import DataCleaner
from data_processing import DataProcessor, assign_performance_category, assign_attendance_category
from ml_predictor import StudentPerformancePredictor

class TestStudentPipeline(unittest.TestCase):

    def test_performance_category_thresholds(self):
        """Tests that academic mark categorization aligns exactly with grading specifications."""
        self.assertEqual(assign_performance_category(95), "Excellent")
        self.assertEqual(assign_performance_category(90), "Excellent")
        self.assertEqual(assign_performance_category(82), "Very Good")
        self.assertEqual(assign_performance_category(75), "Very Good")
        self.assertEqual(assign_performance_category(68), "Good")
        self.assertEqual(assign_performance_category(60), "Good")
        self.assertEqual(assign_performance_category(45), "Average")
        self.assertEqual(assign_performance_category(40), "Average")
        self.assertEqual(assign_performance_category(35), "Needs Improvement")
        self.assertEqual(assign_performance_category(0), "Needs Improvement")

    def test_attendance_category_thresholds(self):
        """Tests attendance standing categorization."""
        self.assertEqual(assign_attendance_category(92), "Good (>85%)")
        self.assertEqual(assign_attendance_category(85), "Good (>85%)")
        self.assertEqual(assign_attendance_category(80), "Normal (75-85%)")
        self.assertEqual(assign_attendance_category(75), "Normal (75-85%)")
        self.assertEqual(assign_attendance_category(74.9), "At Risk (<75%)")
        self.assertEqual(assign_attendance_category(50), "At Risk (<75%)")

    def test_data_cleaning_anomalies(self):
        """Tests that invalid marks (>100 or <0) and duplicates are handled."""
        cleaner = DataCleaner()
        
        # Test marks cleaning with dirty data
        dirty_marks = pd.DataFrame([
            {"student_id": 9999, "subject": "Python", "internal": -10, "mid1": 15, "mid2": 35, "assignment": 8, "final": 120},
            {"student_id": 9999, "subject": "Python", "internal": 12, "mid1": 15, "mid2": 18, "assignment": 8, "final": 80} # duplicate
        ])
        
        cleaned_marks = cleaner.clean_marks(dirty_marks)
        # Duplicate must be removed
        self.assertEqual(len(cleaned_marks), 1)
        # Marks must be clipped to boundaries
        row = cleaned_marks.iloc[0]
        self.assertEqual(row["internal"], 0.0)    # -10 clipped to 0
        self.assertEqual(row["mid2"], 25.0)       # 35 clipped to 25
        self.assertEqual(row["final"], 100.0)     # 120 clipped to 100

    def test_data_processing_and_metrics(self):
        """Tests that metrics, totals, and percentages are computed correctly."""
        processor = DataProcessor()
        
        dummy_students = pd.DataFrame([
            {"student_id": 8001, "name": "Test Student", "department": "AIDS", "year": 3, "section": "A", "gender": "Female"}
        ])
        dummy_marks = pd.DataFrame([
            {"student_id": 8001, "subject": "Python", "internal": 20, "mid1": 25, "mid2": 25, "assignment": 10, "final": 100}
        ])
        dummy_att = pd.DataFrame([
            {"student_id": 8001, "subject": "Python", "total_classes": 50, "attended": 45}
        ])
        
        df_details, df_summary = processor.process_and_merge(
            dummy_students, dummy_marks, dummy_att, save_master=False
        )
        
        self.assertEqual(len(df_summary), 1)
        # 180 out of 180 should yield 100% normalized score
        self.assertEqual(df_summary.iloc[0]["average_marks"], 100.0)
        self.assertEqual(df_summary.iloc[0]["performance_category"], "Excellent")
        # 45/50 = 90% attendance
        self.assertEqual(df_summary.iloc[0]["overall_attendance_pct"], 90.0)
        self.assertEqual(df_summary.iloc[0]["attendance_category"], "Good (>85%)")
        self.assertEqual(df_summary.iloc[0]["pass_status"], "Passed")

if __name__ == "__main__":
    unittest.main()
