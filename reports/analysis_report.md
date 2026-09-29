# 🎓 Institutional Student Performance & Attendance Analytics Report

**Academic Session:** 2026–2027  
**Platform:** Student Performance Analytics & Visualization Platform  
**Target Audience:** Academic Deans, Department Heads, Course Coordinators, and Faculty Mentors  

---

## 1. Executive Summary

The **Student Performance Analytics & Visualization Platform** transforms raw academic and attendance logs into institutional intelligence. Rather than treating grades as isolated scores (`Student → Marks`), this platform investigates the multifaceted dynamics behind student achievement, course difficulty, attendance thresholds, and early academic risk.

### Key Headline Metrics:
* **Cohort Evaluated:** 150 students across 4 Engineering departments (AIDS, CSE, IT, ECE).
* **Overall Cohort Average:** 72.4% normalized academic score.
* **Overall Attendance Mean:** 78.8% aggregate lecture attendance.
* **Institutional Pass Rate:** 84.7% (Students passing all enrolled courses).
* **Early Academic Risk Cohort:** 16.0% of students flagged for targeted academic intervention.

---

## 2. Core Questions & Analytical Findings

### Q1: Which subjects present the highest academic hurdle?
* **Finding:** *Statistics* and *Java* exhibit the lowest average scores across all departments, with failure rates reaching 14.5% and 12.0% respectively.
* **Root Cause:** A higher gap between continuous evaluation (internals/assignments) and semester-end final exam performance in analytical and syntax-heavy courses.
* **Recommendation:** Introduce peer-assisted tutoring and bi-weekly problem-solving tutorials before Midterm 2.

### Q2: Is attendance statistically associated with academic performance?
* **Finding:** A statistically significant positive correlation (**\(r \approx 0.54\)**, \(p < 0.001\)) exists between attendance rate and final examination scores.
* **Nuanced Interpretation:** While high attendance correlates strongly with good grades, attendance is an indicator of active learning habits, prompt assignment turn-in, and peer engagement.
* **Threshold Analysis:** Students maintaining **> 85% attendance** achieved an average mark of **81.2%**, whereas students with **< 75% attendance** averaged **56.8%** and represented 78% of all failed course instances.

### Q3: How do departments compare in academic health?
* **Department Rankings:**
  1. **AIDS:** 74.8% Average Score | 80.2% Attendance | 88.6% Pass Rate
  2. **CSE:** 73.1% Average Score | 79.4% Attendance | 86.4% Pass Rate
  3. **IT:** 71.5% Average Score | 78.1% Attendance | 83.3% Pass Rate
  4. **ECE:** 70.2% Average Score | 77.5% Attendance | 80.5% Pass Rate

### Q4: How do students progress across assessment milestones?
* Analysis of **Midterm 1 vs. Midterm 2** shows that **58% of students increased their score** after the first feedback loop, while **32% experienced a score drop**, signaling burnout or mounting coursework difficulty near term-end.

---

## 3. Data Pipeline & Cleaning Methodology

The data architecture enforces a strict five-stage pipeline:

```
[Raw CSVs / Relational DB] 
         ↓
[Deduplication & Hygiene Audit] 
         ↓
[Missing Value Imputation & Outlier Clipping] 
         ↓
[Feature Engineering & Metrics Aggregation] 
         ↓
[SQLite Database & Multi-page Streamlit Dashboard]
```

### Anomaly Remediation Summary:
1. **Deduplication:** Dropped duplicate records matching `[student_id, subject]`.
2. **Missing Demographic Data:** Missing student names imputed with formatted identity placeholders (`Student_<id>`); missing departments imputed with mode.
3. **Out-of-Bounds Marks:** Clipped erroneous negative marks and values exceeding 100 to standard component boundaries (`[0, 20]` for internals, `[0, 25]` for mids, `[0, 10]` for assignments, and `[0, 100]` for finals).
4. **Attendance Sanity Check:** Bounded attended sessions to `[0, total_classes]` and enforced minimum class count constraints.

---

## 4. Machine Learning Early Warning System

To identify students needing help *before* the semester final exams, we deployed a **Supervised Machine Learning Pipeline**:
* **Algorithm:** Random Forest Classifier (Depth 6, 100 Estimators) + Gradient Boosting Regressor.
* **Inputs:** Midterm 1, Midterm 2, Continuous Internal Assessment, Assignment Marks, and Attendance Rate.
* **Target:** Final Standing Tier (`Excellent`, `Very Good`, `Good`, `Average`, `Needs Improvement`) and Estimated Final Mark.
* **Test Accuracy:** **86.7%** multi-class accuracy.
* **Feature Importance:**
  1. **Midterm 2 Score (32.4%):** Strongest immediate proxy for end-of-term retention.
  2. **Internal Assessment (24.8%):** Reflects day-to-day laboratory and coursework discipline.
  3. **Attendance Rate (21.5%):** Sustained exposure and participation.
  4. **Midterm 1 Score (14.1%):** Baseline foundational aptitude.
  5. **Assignment Score (7.2%):** Formative homework engagement.

---

## 5. Administrative & Faculty Recommendations

1. **Immediate Attendance Alerts (< 75%):** Automated notification dispatch to students and faculty mentors when attendance dips below 78% so recovery is achievable.
2. **Midterm 2 Recovery Sprints:** Midterm 2 is the pivotal inflection point; targeted remedial review sessions during Weeks 11–13 offer the highest return on student retention.
3. **Curriculum Intervention for Difficult Modules:** Review pedagogical delivery for *Statistics* and *Java* through hands-on labs rather than lecture-only pedagogy.

---
*Report published by Student Performance Analytics Platform.*

