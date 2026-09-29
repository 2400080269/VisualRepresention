-- ====================================================================
-- SCHEMA DEFINITION: STUDENT PERFORMANCE ANALYTICS PLATFORM
-- Compatible with SQLite, MySQL, and PostgreSQL
-- ====================================================================

-- 1. Students Demographics Table
CREATE TABLE IF NOT EXISTS students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    gender VARCHAR(20) NOT NULL
);

-- 2. Subjects Reference Table
CREATE TABLE IF NOT EXISTS subjects (
    subject_code VARCHAR(20) PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    credits INT DEFAULT 4
);

-- 3. Marks Component Table
CREATE TABLE IF NOT EXISTS marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    internal REAL NOT NULL,
    mid1 REAL NOT NULL,
    mid2 REAL NOT NULL,
    assignment REAL NOT NULL,
    final REAL NOT NULL,
    raw_total REAL NOT NULL,
    normalized_score REAL NOT NULL,
    subject_passed INT NOT NULL,
    subject_performance_cat VARCHAR(30),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 4. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    total_classes INT NOT NULL,
    attended INT NOT NULL,
    attendance_pct REAL NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 5. Student Analytical Performance Summary Table
CREATE TABLE IF NOT EXISTS student_summary (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    gender VARCHAR(20),
    total_subjects INT,
    average_marks REAL NOT NULL,
    overall_attendance_pct REAL NOT NULL,
    gpa REAL NOT NULL,
    performance_category VARCHAR(30) NOT NULL,
    attendance_category VARCHAR(30) NOT NULL,
    pass_status VARCHAR(20) NOT NULL,
    risk_level VARCHAR(30) NOT NULL,
    dept_rank INT,
    overall_rank INT,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Indices for rapid analytical querying
CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department, year, section);
CREATE INDEX IF NOT EXISTS idx_marks_student_subject ON marks(student_id, subject);
CREATE INDEX IF NOT EXISTS idx_attendance_student_subject ON attendance(student_id, subject);
CREATE INDEX IF NOT EXISTS idx_summary_perf ON student_summary(performance_category, risk_level);

