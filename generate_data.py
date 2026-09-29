"""
Data Generation Script for Student Performance Analytics Platform
Generates realistic multi-department student data, marks across subjects, 
and attendance records with intentional anomalies for demonstrating data cleaning.
"""

import os
import random
import pandas as pd
import numpy as np

def generate_student_datasets(output_dir="data/raw", num_students=150, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    
    os.makedirs(output_dir, exist_ok=True)
    
    departments = ["AIDS", "CSE", "IT", "ECE"]
    years = [2, 3, 4]
    sections = ["A", "B"]
    genders = ["Male", "Female"]
    
    first_names_male = [
        "Ravi", "Kiran", "Rahul", "Aditya", "Vikram", "Arjun", "Suresh", "Karthik", 
        "Sai", "Rohit", "Manish", "Gautam", "Varun", "Nikhil", "Deepak", "Pranav",
        "Abhishek", "Harish", "Siddharth", "Vishal", "Anand", "Rohan", "Dinesh", "Tarun"
    ]
    first_names_female = [
        "Priya", "Ananya", "Sneha", "Kavya", "Divya", "Pooja", "Meera", "Swathi", 
        "Shreya", "Neha", "Ritu", "Tanvi", "Ishita", "Aishwarya", "Shruti", "Bhavya",
        "Sowmya", "Keerthi", "Lavanya", "Harini", "Preeti", "Sunita", "Anusha", "Deepika"
    ]
    last_names = [
        "Sharma", "Verma", "Reddy", "Patel", "Kumar", "Iyer", "Rao", "Nair", 
        "Singh", "Gupta", "Das", "Joshi", "Mishra", "Choudhury", "Bose", "Kulkarni",
        "Deshmukh", "Menon", "Pillai", "Prasad", "Bhat", "Chatterjee"
    ]
    
    subjects = ["Python", "DBMS", "Statistics", "Java", "Machine Learning"]
    
    # 1. Generate Students
    students = []
    base_id = 1001
    
    for i in range(num_students):
        s_id = base_id + i
        gender = random.choice(genders)
        if gender == "Male":
            first_name = random.choice(first_names_male)
        else:
            first_name = random.choice(first_names_female)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        dept = random.choice(departments)
        year = random.choice(years)
        sec = random.choice(sections)
        
        students.append({
            "student_id": s_id,
            "name": full_name,
            "department": dept,
            "year": year,
            "section": sec,
            "gender": gender
        })
        
    df_students = pd.DataFrame(students)
    
    # 2. Generate Marks & Attendance with realistic correlation
    # We assign an underlying academic capability factor (0.4 to 0.98) and attendance factor (0.5 to 0.99)
    # with positive correlation to simulate real educational distributions
    marks_records = []
    attendance_records = []
    
    for _, stu in df_students.iterrows():
        s_id = stu["student_id"]
        
        # Base ability (normal distribution centered around 72 with standard deviation 12)
        base_ability = np.clip(np.random.normal(loc=72, scale=14), 30, 98)
        
        # Attendance factor: correlated with ability + noise
        att_prob = np.clip((base_ability / 100.0) * 0.8 + np.random.normal(0.2, 0.1), 0.40, 0.98)
        
        for subj in subjects:
            # Subject specific variance
            subj_diff = {
                "Python": 3,
                "DBMS": 0,
                "Statistics": -4,
                "Java": -2,
                "Machine Learning": -1
            }.get(subj, 0)
            
            # Subject final performance based on ability + attendance + noise
            subj_score = np.clip(base_ability + subj_diff + (att_prob - 0.75) * 15 + np.random.normal(0, 5), 25, 99)
            
            # Component marks
            # Internal max 20
            internal = int(np.clip(round((subj_score / 100) * 20 + np.random.normal(0, 1.5)), 6, 20))
            # Mid 1 max 25
            mid1 = int(np.clip(round((subj_score / 100) * 25 + np.random.normal(0, 2)), 8, 25))
            # Mid 2 max 25 (students often improve or stay consistent)
            mid2 = int(np.clip(round((subj_score / 100) * 25 + np.random.normal(1, 2)), 8, 25))
            # Assignment max 10
            assignment = int(np.clip(round((subj_score / 100) * 10 + np.random.normal(0.5, 1)), 3, 10))
            # Final max 100
            final = int(np.clip(round(subj_score + np.random.normal(0, 3)), 20, 100))
            
            marks_records.append({
                "student_id": s_id,
                "subject": subj,
                "internal": internal,
                "mid1": mid1,
                "mid2": mid2,
                "assignment": assignment,
                "final": final
            })
            
            # Attendance
            total_classes = random.choice([48, 50, 52, 54])
            attended = int(np.clip(round(total_classes * att_prob + np.random.normal(0, 2)), 15, total_classes))
            
            attendance_records.append({
                "student_id": s_id,
                "subject": subj,
                "total_classes": total_classes,
                "attended": attended
            })
            
    df_marks = pd.DataFrame(marks_records)
    df_attendance = pd.DataFrame(attendance_records)
    
    # 3. Inject deliberate anomalies into RAW data for testing data cleaning pipeline
    # (a) Missing values
    # Missing names
    df_students.loc[5, "name"] = None
    df_students.loc[18, "department"] = None
    
    # Missing marks
    df_marks.loc[12, "final"] = np.nan
    df_marks.loc[34, "mid1"] = np.nan
    df_marks.loc[78, "internal"] = np.nan
    
    # Missing attendance
    df_attendance.loc[15, "attended"] = np.nan
    
    # (b) Duplicate rows
    dup_student = df_students.iloc[2:4].copy()
    df_students = pd.concat([df_students, dup_student], ignore_index=True)
    
    dup_mark = df_marks.iloc[10:12].copy()
    df_marks = pd.concat([df_marks, dup_mark], ignore_index=True)
    
    dup_att = df_attendance.iloc[5:7].copy()
    df_attendance = pd.concat([df_attendance, dup_att], ignore_index=True)
    
    # (c) Invalid marks (e.g. > 100 or negative marks)
    df_marks.loc[25, "final"] = 115     # Invalid (> 100)
    df_marks.loc[45, "internal"] = -8   # Invalid (< 0)
    df_marks.loc[60, "mid2"] = 35       # Invalid (> 25)
    
    # (d) Invalid attendance (attended > total_classes)
    df_attendance.loc[22, "attended"] = 65  # Invalid (> total_classes 50)
    
    # Save raw CSVs
    students_path = os.path.join(output_dir, "students.csv")
    marks_path = os.path.join(output_dir, "marks.csv")
    attendance_path = os.path.join(output_dir, "attendance.csv")
    
    df_students.to_csv(students_path, index=False)
    df_marks.to_csv(marks_path, index=False)
    df_attendance.to_csv(attendance_path, index=False)
    
    print(f"Generated raw datasets successfully in '{output_dir}':")
    print(f" - students.csv: {len(df_students)} rows (includes duplicates and missing)")
    print(f" - marks.csv: {len(df_marks)} rows (includes invalid marks & NaNs)")
    print(f" - attendance.csv: {len(df_attendance)} rows (includes invalid counts)")

if __name__ == "__main__":
    generate_student_datasets()

