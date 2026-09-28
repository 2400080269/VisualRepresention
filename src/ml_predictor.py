"""
Module: ml_predictor.py
Purpose: Machine Learning model training, evaluation, feature importance analysis,
and interactive what-if simulation for student grade prediction and early intervention.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, classification_report, r2_score, mean_squared_error

class StudentPerformancePredictor:
    def __init__(self, model_dir="data/models"):
        self.model_dir = model_dir
        self.clf = None
        self.reg = None
        self.feature_names = ["attendance_pct", "internal", "mid1", "mid2", "assignment"]
        self.classes_ = ["Needs Improvement", "Average", "Good", "Very Good", "Excellent"]
        self.metrics_ = {}
        os.makedirs(self.model_dir, exist_ok=True)

    def train_models(self, df_details):
        """
        Trains both:
        1. Multi-class Classifier: Predicts Performance Category
        2. Regressor: Predicts Continuous Final Semester Score (0-100)
        """
        # Ensure complete data
        df = df_details.dropna(subset=self.feature_names + ["final", "subject_performance_cat"]).copy()
        
        X = df[self.feature_names]
        y_cat = df["subject_performance_cat"]
        y_score = df["final"]

        # Stratified train/test split for classification
        X_train, X_test, y_cat_train, y_cat_test, y_score_train, y_score_test = train_test_split(
            X, y_cat, y_score, test_size=0.2, random_state=42, stratify=y_cat
        )

        # 1. Random Forest Classifier
        self.clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.clf.fit(X_train, y_cat_train)
        y_cat_pred = self.clf.predict(X_test)
        clf_acc = accuracy_score(y_cat_test, y_cat_pred)

        # 2. Gradient Boosting Regressor for final score
        self.reg = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        self.reg.fit(X_train, y_score_train)
        y_score_pred = self.reg.predict(X_test)
        r2 = r2_score(y_score_test, y_score_pred)
        rmse = np.sqrt(mean_squared_error(y_score_test, y_score_pred))

        # Feature importances
        feature_importances = dict(zip(self.feature_names, self.clf.feature_importances_.round(4)))

        self.metrics_ = {
            "classifier_accuracy": round(clf_acc * 100, 2),
            "regressor_r2": round(r2, 3),
            "regressor_rmse": round(rmse, 2),
            "feature_importances": feature_importances,
            "test_sample_size": len(X_test)
        }

        # Save models
        joblib.dump(self.clf, os.path.join(self.model_dir, "classifier.joblib"))
        joblib.dump(self.reg, os.path.join(self.model_dir, "regressor.joblib"))
        print(f"ML Models trained successfully. Accuracy: {self.metrics_['classifier_accuracy']}%, R²: {self.metrics_['regressor_r2']}")
        return self.metrics_

    def load_models(self):
        clf_path = os.path.join(self.model_dir, "classifier.joblib")
        reg_path = os.path.join(self.model_dir, "regressor.joblib")
        if os.path.exists(clf_path) and os.path.exists(reg_path):
            self.clf = joblib.load(clf_path)
            self.reg = joblib.load(reg_path)
            return True
        return False

    def predict(self, attendance_pct, internal, mid1, mid2, assignment):
        """
        Infers predicted performance category and expected final score with recommendations.
        """
        if self.clf is None or self.reg is None:
            if not self.load_models():
                raise RuntimeError("Models not trained or loaded yet.")

        input_data = pd.DataFrame([{
            "attendance_pct": float(attendance_pct),
            "internal": float(internal),
            "mid1": float(mid1),
            "mid2": float(mid2),
            "assignment": float(assignment)
        }])

        pred_cat = self.clf.predict(input_data)[0]
        pred_probs = self.clf.predict_proba(input_data)[0]
        prob_dict = {cls_name: round(prob * 100, 1) for cls_name, prob in zip(self.clf.classes_, pred_probs)}

        pred_final = float(np.clip(self.reg.predict(input_data)[0], 0, 100).round(1))

        # Calculate estimated total normalized score
        # internal (20) + mid1 (25) + mid2 (25) + assignment (10) + pred_final (100) = 180
        est_total = round(((internal + mid1 + mid2 + assignment + pred_final) / 180.0) * 100.0, 1)

        # Risk assessment
        is_at_risk = pred_cat in ["Needs Improvement", "Average"] or attendance_pct < 75.0 or pred_final < 40.0
        
        # Recommendations
        recommendations = []
        if attendance_pct < 75:
            recommendations.append("🚨 Attendance is below the mandatory 75% threshold. Prioritize attending all remaining lectures to secure exam eligibility.")
        if mid2 < mid1:
            recommendations.append("📉 Midterm 2 score dropped compared to Midterm 1. Review difficult concepts and schedule faculty doubt sessions.")
        if assignment < 7:
            recommendations.append("📝 Assignment marks are suboptimal. Focus on completing continuous assessments thoroughly to gain easy marks.")
        if internal < 14:
            recommendations.append("🎯 Internal marks need a boost. Participate actively in laboratory tests and tutorial discussions.")
        if not recommendations:
            recommendations.append("🌟 Outstanding performance trajectory! Continue your steady study habits and practice mock final question papers.")

        return {
            "predicted_category": pred_cat,
            "predicted_final_score": pred_final,
            "estimated_overall_percentage": est_total,
            "category_probabilities": prob_dict,
            "is_at_risk": is_at_risk,
            "risk_label": "High Risk / At Risk" if is_at_risk else "On Track / Safe",
            "recommendations": recommendations
        }

if __name__ == "__main__":
    predictor = StudentPerformancePredictor()
    print("Student Performance Predictor ready.")
