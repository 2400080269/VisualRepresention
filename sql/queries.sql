-- ====================================================================
-- ANALYTICAL SQL QUERIES: STUDENT PERFORMANCE ANALYTICS PLATFORM
-- Demonstrates production SQL proficiency for data analyst & data engineering interviews
-- ====================================================================

-- 1. Department-wise Academic Performance Benchmark
-- Computes student count, average marks, average attendance, and overall GPA per department.
SELECT 
    department,
    COUNT(student_id) AS total_students,
    ROUND(AVG(average_marks), 2) AS dept_avg_marks,
    ROUND(AVG(overall_attendance_pct), 2) AS dept_avg_attendance,
    ROUND(AVG(gpa), 2) AS dept_avg_gpa
FROM student_summary
GROUP BY department
ORDER BY dept_avg_marks DESC;


-- 2. Subject Difficulty Ranking & Failure Rate
-- Identifies which subjects have the lowest scores and highest failure rates.
SELECT 
    m.subject,
    COUNT(m.student_id) AS total_enrolled,
    ROUND(AVG(m.normalized_score), 2) AS subject_avg_marks,
    ROUND(MIN(m.normalized_score), 1) AS lowest_marks,
    ROUND(MAX(m.normalized_score), 1) AS highest_marks,
    SUM(CASE WHEN m.subject_passed = 1 THEN 1 ELSE 0 END) AS total_passed,
    SUM(CASE WHEN m.subject_passed = 0 THEN 1 ELSE 0 END) AS total_failed,
    ROUND((SUM(CASE WHEN m.subject_passed = 1 THEN 1.0 ELSE 0.0 END) / COUNT(m.student_id)) * 100.0, 2) AS pass_percentage
FROM marks m
GROUP BY m.subject
ORDER BY subject_avg_marks ASC;


-- 3. Top 3 Students Per Department (Window Functions)
-- Uses DENSE_RANK() to find top performers partitioned by department.
WITH RankedStudents AS (
    SELECT 
        student_id,
        name,
        department,
        year,
        section,
        average_marks,
        overall_attendance_pct,
        performance_category,
        DENSE_RANK() OVER (PARTITION BY department ORDER BY average_marks DESC) AS dept_position
    FROM student_summary
)
SELECT 
    student_id,
    name,
    department,
    dept_position,
    average_marks,
    overall_attendance_pct,
    performance_category
FROM RankedStudents
WHERE dept_position <= 3
ORDER BY department, dept_position ASC;


-- 4. Attendance Impact Analysis (Binned Academic Association)
-- Groups students by attendance tiers to observe mark variations.
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


-- 5. Early Warning System: At-Risk Students Requiring Immediate Faculty Intervention
-- Flags students with attendance < 75% or average marks < 50 or subject backlogs.
SELECT 
    s.student_id,
    s.name,
    s.department,
    s.year,
    s.section,
    s.average_marks,
    s.overall_attendance_pct,
    s.risk_level,
    (SELECT COUNT(*) FROM marks m WHERE m.student_id = s.student_id AND m.subject_passed = 0) AS failed_subjects_count
FROM student_summary s
WHERE s.risk_level IN ('High Risk', 'Moderate Risk')
ORDER BY s.risk_level ASC, s.overall_attendance_pct ASC, s.average_marks ASC;


-- 6. Exam Progression: Mid 1 vs Mid 2 Performance Trajectory
-- Measures whether students improved from Midterm 1 to Midterm 2 across subjects.
SELECT 
    subject,
    ROUND(AVG(mid1), 2) AS avg_mid1,
    ROUND(AVG(mid2), 2) AS avg_mid2,
    ROUND(AVG(mid2 - mid1), 2) AS avg_growth,
    SUM(CASE WHEN mid2 > mid1 THEN 1 ELSE 0 END) AS students_improved,
    SUM(CASE WHEN mid2 < mid1 THEN 1 ELSE 0 END) AS students_declined,
    SUM(CASE WHEN mid2 = mid1 THEN 1 ELSE 0 END) AS students_unchanged
FROM marks
GROUP BY subject
ORDER BY avg_growth DESC;


-- 7. Section-wise Performance Comparison within Department
-- Helps administration compare teaching outcomes across sections.
SELECT 
    department,
    section,
    COUNT(student_id) AS student_strength,
    ROUND(AVG(average_marks), 2) AS section_avg_marks,
    ROUND(AVG(overall_attendance_pct), 2) AS section_avg_attendance,
    ROUND(SUM(CASE WHEN pass_status = 'Passed' THEN 1.0 ELSE 0.0 END) / COUNT(student_id) * 100.0, 2) AS section_pass_rate
FROM student_summary
GROUP BY department, section
ORDER BY department, section;
