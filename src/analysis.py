"""
Module: analysis.py
Purpose: Statistical analysis, hypothesis testing, correlation computation,
performance ranking, and statistical summaries for the platform.
"""

import pandas as pd
import numpy as np
from scipy import stats

class PerformanceAnalyzer:
    def __init__(self, df_summary=None, df_details=None):
        self.df_summary = df_summary
        self.df_details = df_details

    def set_data(self, df_summary, df_details):
        self.df_summary = df_summary
        self.df_details = df_details

    def get_kpis(self, filtered_df=None):
        """Calculates headline KPI metrics for the dashboard overview."""
        df = filtered_df if filtered_df is not None else self.df_summary
        if df is None or len(df) == 0:
            return {}

        total_students = len(df)
        avg_marks = round(df["average_marks"].mean(), 1)
        median_marks = round(df["average_marks"].median(), 1)
        std_marks = round(df["average_marks"].std(), 1)
        avg_attendance = round(df["overall_attendance_pct"].mean(), 1)
        pass_count = (df["pass_status"] == "Passed").sum()
        pass_rate = round((pass_count / total_students) * 100.0, 1)
        
        top_student = df.sort_values(by="average_marks", ascending=False).iloc[0]
        lowest_student = df.sort_values(by="average_marks", ascending=True).iloc[0]
        
        at_risk_count = (df["risk_level"].isin(["High Risk", "Moderate Risk"])).sum()
        at_risk_pct = round((at_risk_count / total_students) * 100.0, 1)

        return {
            "total_students": total_students,
            "avg_marks": avg_marks,
            "median_marks": median_marks,
            "std_marks": std_marks,
            "avg_attendance": avg_attendance,
            "pass_count": pass_count,
            "pass_rate": pass_rate,
            "top_performer": top_student["name"],
            "top_performer_marks": top_student["average_marks"],
            "top_performer_id": top_student["student_id"],
            "lowest_performer": lowest_student["name"],
            "lowest_performer_marks": lowest_student["average_marks"],
            "lowest_performer_id": lowest_student["student_id"],
            "at_risk_count": at_risk_count,
            "at_risk_pct": at_risk_pct
        }

    def compute_attendance_correlation(self, df=None):
        """
        Calculates Pearson and Spearman correlation between attendance and academic score,
        with regression statistics and nuanced statistical interpretation.
        """
        data = df if df is not None else self.df_summary
        if data is None or len(data) < 3:
            return {}

        x = data["overall_attendance_pct"].values
        y = data["average_marks"].values

        pearson_corr, p_value = stats.pearsonr(x, y)
        spearman_corr, sp_p_val = stats.spearmanr(x, y)
        slope, intercept, r_value, _, std_err = stats.linregress(x, y)

        interpretation = (
            "A statistically significant positive correlation is observed between attendance rate and average academic marks. "
            "Note: This reflects an academic association/tendency, not direct standalone causation, as regular attendance often "
            "coincides with active continuous study, timely assignment submission, and classroom engagement."
            if pearson_corr > 0.4 and p_value < 0.05 else
            "Moderate or weak association observed between attendance and final marks in this subset."
        )

        return {
            "pearson_r": round(pearson_corr, 3),
            "p_value": float(f"{p_value:.4e}"),
            "spearman_rho": round(spearman_corr, 3),
            "r_squared": round(pearson_corr ** 2, 3),
            "slope": round(slope, 3),
            "intercept": round(intercept, 2),
            "interpretation": interpretation
        }

    def get_subject_performance_summary(self, filtered_details=None):
        """Aggregates subject-level averages, pass rates, and exam progression."""
        df = filtered_details if filtered_details is not None else self.df_details
        if df is None or len(df) == 0:
            return pd.DataFrame()

        summary = df.groupby("subject").agg(
            enrolled=("student_id", "count"),
            avg_normalized_score=("normalized_score", "mean"),
            median_score=("normalized_score", "median"),
            highest_score=("normalized_score", "max"),
            lowest_score=("normalized_score", "min"),
            avg_final=("final", "mean"),
            avg_mid1=("mid1", "mean"),
            avg_mid2=("mid2", "mean"),
            avg_internal=("internal", "mean"),
            avg_assignment=("assignment", "mean"),
            avg_attendance=("attendance_pct", "mean"),
            passed_count=("subject_passed", "sum")
        ).reset_index()

        summary["pass_percentage"] = (
            (summary["passed_count"] / summary["enrolled"]) * 100.0
        ).round(1)
        
        # Round numerical columns
        for col in ["avg_normalized_score", "median_score", "avg_final", "avg_mid1", "avg_mid2", "avg_internal", "avg_assignment", "avg_attendance"]:
            summary[col] = summary[col].round(1)
            
        summary = summary.sort_values(by="avg_normalized_score", ascending=False)
        return summary

    def get_performance_distribution(self, df=None):
        """Returns frequency and proportion across performance tiers."""
        data = df if df is not None else self.df_summary
        order = ["Excellent", "Very Good", "Good", "Average", "Needs Improvement"]
        counts = data["performance_category"].value_counts().reindex(order, fill_value=0).reset_index()
        counts.columns = ["Category", "Count"]
        counts["Percentage"] = ((counts["Count"] / len(data)) * 100).round(1)
        return counts

    def get_department_comparison(self):
        """Compares academic outcomes across departments."""
        if self.df_summary is None:
            return pd.DataFrame()
            
        dept_comp = self.df_summary.groupby("department").agg(
            students=("student_id", "count"),
            avg_marks=("average_marks", "mean"),
            median_marks=("average_marks", "median"),
            avg_attendance=("overall_attendance_pct", "mean"),
            pass_count=("all_passed", "sum")
        ).reset_index()
        
        dept_comp["pass_rate"] = ((dept_comp["pass_count"] / dept_comp["students"]) * 100).round(1)
        dept_comp["avg_marks"] = dept_comp["avg_marks"].round(1)
        dept_comp["median_marks"] = dept_comp["median_marks"].round(1)
        dept_comp["avg_attendance"] = dept_comp["avg_attendance"].round(1)
        return dept_comp.sort_values(by="avg_marks", ascending=False)

if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    print("Performance Analyzer ready.")

