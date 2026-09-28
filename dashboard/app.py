"""
Streamlit Web Application: Student Performance Analytics & Visualization Platform
Interactive, multi-page data analytics dashboard for academic insights, student deep-dives,
subject benchmarking, attendance correlation, predictive ML, and live SQL exploration.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add src to system path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src.data_cleaning import DataCleaner
from src.data_processing import DataProcessor
from src.database import DatabaseManager
from src.analysis import PerformanceAnalyzer
from src.ml_predictor import StudentPerformancePredictor
from src.utils import PALETTE, CATEGORY_COLORS, RISK_COLORS, generate_student_report_card, convert_df_to_csv, df_to_markdown_safe
from src.file_uploader import parse_uploaded_academic_data, generate_sample_excel_template

# Safe statsmodels detection for Plotly OLS trendlines
try:
    import statsmodels.api
    HAS_STATSMODELS = True
except Exception:
    HAS_STATSMODELS = False

# ====================================================================
# STREAMLIT APP CONFIGURATION
# ====================================================================
st.set_page_config(
    page_title="Student Performance Analytics Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1F2937;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-excellent { background-color: #DEF7EC; color: #03543F; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
    .badge-good { background-color: #E1EFFE; color: #1E429F; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
    .badge-average { background-color: #FEF08A; color: #713F12; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
    .badge-risk { background-color: #FDE8E8; color: #9B1C1C; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ====================================================================
# DATA LOADING & CACHING
# ====================================================================
@st.cache_data
def load_processed_data():
    summary_path = os.path.join(PROJECT_ROOT, "data", "processed", "master_student_summary.csv")
    details_path = os.path.join(PROJECT_ROOT, "data", "processed", "subject_performance_detailed.csv")
    db_path = os.path.join(PROJECT_ROOT, "data", "student_performance.db")
    
    if not (os.path.exists(summary_path) and os.path.exists(details_path)):
        return None, None
        
    df_summary = pd.read_csv(summary_path)
    df_details = pd.read_csv(details_path)
    return df_summary, df_details


def run_pipeline_if_missing():
    with st.spinner("Executing end-to-end data pipeline (Cleaning, SQL, ML Models)..."):
        from run_pipeline import run_full_pipeline
        run_full_pipeline(num_students=150, force_regenerate=True)
        st.cache_data.clear()
        st.success("Pipeline generated successfully! Refreshing dashboard...")
        st.rerun()


# Initialize or retrieve data from session state
if "df_summary" not in st.session_state or "df_details" not in st.session_state:
    raw_sum, raw_det = load_processed_data()
    if raw_sum is None or raw_det is None:
        st.warning("⚠️ Processed datasets not found. Initializing data pipeline for the first run...")
        if st.button("🚀 Initialize & Run Analytics Pipeline Now", type="primary"):
            run_pipeline_if_missing()
        st.stop()
    st.session_state["df_summary"] = raw_sum
    st.session_state["df_details"] = raw_det
    st.session_state["data_source_name"] = "Default Demo Dataset (150 Students)"

df_summary = st.session_state["df_summary"]
df_details = st.session_state["df_details"]

analyzer = PerformanceAnalyzer(df_summary, df_details)
db = DatabaseManager(db_path=os.path.join(PROJECT_ROOT, "data", "student_performance.db"))

# ====================================================================
# SIDEBAR NAVIGATION & GLOBAL FILTERS
# ====================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=60)
    st.markdown("### **Academic Intelligence**")
    st.caption("Student Performance & Attendance Analytics")
    
    # Active Dataset indicator
    st.info(f"📁 **Active Data:** {st.session_state.get('data_source_name', 'Default Demo')}")
    st.markdown("---")
    
    # Navigation
    menu = st.radio(
        "Navigation",
        [
            "📊 Overview & KPIs",
            "📤 Upload & Process Data",
            "👤 Student Deep-Dive",
            "📚 Subject Analytics",
            "⏱️ Attendance & Correlation",
            "🤖 ML Performance Predictor",
            "💻 SQL Query Explorer",
            "📥 Export & Reports"
        ],
        index=0
    )
    st.markdown("---")
    
    st.markdown("#### **Global Filters**")
    
    # Department filter
    dept_options = ["All"] + sorted(list(df_summary["department"].unique()))
    selected_dept = st.selectbox("Department", dept_options)
    
    # Year filter
    year_options = ["All"] + sorted(list(df_summary["year"].unique()))
    selected_year = st.selectbox("Academic Year", year_options)
    
    # Section filter
    sec_options = ["All"] + sorted(list(df_summary["section"].unique()))
    selected_sec = st.selectbox("Section", sec_options)
    
    # Performance Category filter
    perf_options = ["All", "Excellent", "Very Good", "Good", "Average", "Needs Improvement"]
    selected_perf = st.selectbox("Performance Tier", perf_options)
    
    # Apply filtering
    filtered_summary = df_summary.copy()
    filtered_details = df_details.copy()
    
    if selected_dept != "All":
        filtered_summary = filtered_summary[filtered_summary["department"] == selected_dept]
        filtered_details = filtered_details[filtered_details["department"] == selected_dept]
        
    if selected_year != "All":
        filtered_summary = filtered_summary[filtered_summary["year"] == int(selected_year)]
        filtered_details = filtered_details[filtered_details["year"] == int(selected_year)]
        
    if selected_sec != "All":
        filtered_summary = filtered_summary[filtered_summary["section"] == selected_sec]
        filtered_details = filtered_details[filtered_details["section"] == selected_sec]
        
    if selected_perf != "All":
        filtered_summary = filtered_summary[filtered_summary["performance_category"] == selected_perf]
        filtered_details = filtered_details[filtered_details["student_id"].isin(filtered_summary["student_id"])]
        
    st.caption(f"Showing **{len(filtered_summary)}** of {len(df_summary)} students")
    
    if st.button("🔄 Reset Filters"):
        st.rerun()

# ====================================================================
# PAGE 1: OVERVIEW & KPIS
# ====================================================================
if menu == "📊 Overview & KPIs":
    st.markdown('<div class="main-header">🎓 Student Performance Analytics Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Executive Academic Dashboard & Institutional Performance Insights</div>', unsafe_allow_html=True)
    
    if len(filtered_summary) == 0:
        st.warning("No student records match the selected filter criteria. Please adjust your filters.")
        st.stop()
        
    kpis = analyzer.get_kpis(filtered_summary)
    
    # Metric cards row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Enrolled</div>
            <div class="metric-val">{kpis['total_students']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Marks</div>
            <div class="metric-val">{kpis['avg_marks']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Class Average Attendance</div>
            <div class="metric-val">{kpis['avg_attendance']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Overall Pass Rate</div>
            <div class="metric-val" style="color: {'#10B981' if kpis['pass_rate'] >= 75 else '#EF4444'}">{kpis['pass_rate']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Students At Risk</div>
            <div class="metric-val" style="color: {'#EF4444' if kpis['at_risk_count'] > 0 else '#10B981'}">{kpis['at_risk_count']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Top and Lowest Performers Highlights
    h1, h2 = st.columns(2)
    with h1:
        st.info(f"🏆 **Top Performer:** {kpis['top_performer']} (ID: {kpis['top_performer_id']}) — **{kpis['top_performer_marks']}% Average**")
    with h2:
        st.warning(f"⚠️ **Needs Immediate Academic Support:** {kpis['lowest_performer']} (ID: {kpis['lowest_performer_id']}) — **{kpis['lowest_performer_marks']}% Average**")
        
    st.markdown("### 📈 Academic Trends & Distributions")
    row1_c1, row1_c2 = st.columns([3, 2])
    
    with row1_c1:
        st.markdown("#### **Subject-wise Average Marks**")
        subj_summary = analyzer.get_subject_performance_summary(filtered_details)
        fig_subj = px.bar(
            subj_summary,
            x="subject",
            y="avg_normalized_score",
            color="avg_normalized_score",
            color_continuous_scale="Blues",
            text="avg_normalized_score",
            labels={"subject": "Subject Course", "avg_normalized_score": "Average Score (%)"},
            title="Class Average Marks by Subject"
        )
        fig_subj.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_subj.update_layout(yaxis_range=[0, 100], template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig_subj, use_container_width=True)
        
    with row1_c2:
        st.markdown("#### **Pass vs Fail Ratio**")
        pass_fail_counts = filtered_summary["pass_status"].value_counts().reset_index()
        pass_fail_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            pass_fail_counts,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={"Passed": "#10B981", "Failed": "#EF4444"},
            hole=0.45,
            title="Academic Clearance Proportion"
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(template="plotly_white", margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Row 2: Attendance vs Marks & Grade Distribution
    row2_c1, row2_c2 = st.columns([3, 2])
    with row2_c1:
        st.markdown("#### **Attendance % vs Average Academic Marks**")
        fig_scatter = px.scatter(
            filtered_summary,
            x="overall_attendance_pct",
            y="average_marks",
            color="performance_category",
            color_discrete_map=CATEGORY_COLORS,
            hover_data=["student_id", "name", "department", "risk_level"],
            trendline="ols" if HAS_STATSMODELS else None,
            labels={"overall_attendance_pct": "Attendance (%)", "average_marks": "Average Academic Score (%)"},
            title="Correlation: Class Attendance vs Performance"
        )
        fig_scatter.update_layout(template="plotly_white", legend_title="Standing Tier")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with row2_c2:
        st.markdown("#### **Performance Category Distribution**")
        perf_dist = analyzer.get_performance_distribution(filtered_summary)
        fig_bar = px.bar(
            perf_dist,
            x="Category",
            y="Count",
            color="Category",
            color_discrete_map=CATEGORY_COLORS,
            text="Count",
            title="Students Count by Grading Category"
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(template="plotly_white", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Leaderboards
    st.markdown("### 🏅 Student Leaderboard & Performance Registry")
    tab_all, tab_top, tab_low = st.tabs(["📋 Filtered Student Registry", "🥇 Top 5 Performers", "⚠️ Attention Required (Bottom 5)"])
    
    display_cols = [
        "student_id", "name", "department", "year", "section", 
        "average_marks", "gpa", "overall_attendance_pct", 
        "performance_category", "risk_level", "pass_status"
    ]
    
    with tab_all:
        search_query = st.text_input("🔍 Quick Search by Name or Roll No:", "")
        table_df = filtered_summary[display_cols].copy()
        if search_query:
            table_df = table_df[
                table_df["name"].str.contains(search_query, case=False, na=False) |
                table_df["student_id"].astype(str).str.contains(search_query)
            ]
        st.dataframe(
            table_df.sort_values(by="average_marks", ascending=False),
            use_container_width=True,
            column_config={
                "average_marks": st.column_config.ProgressColumn("Avg Marks %", format="%.1f%%", min_value=0, max_value=100),
                "overall_attendance_pct": st.column_config.ProgressColumn("Attendance %", format="%.1f%%", min_value=0, max_value=100),
                "gpa": st.column_config.NumberColumn("GPA (10.0)", format="%.2f"),
                "student_id": st.column_config.NumberColumn("Roll No", format="%d")
            }
        )
        
    with tab_top:
        top5 = filtered_summary.sort_values(by="average_marks", ascending=False).head(5)[display_cols]
        st.table(top5)
        
    with tab_low:
        bot5 = filtered_summary.sort_values(by="average_marks", ascending=True).head(5)[display_cols]
        st.table(bot5)


# ====================================================================
# PAGE: UPLOAD & PROCESS DATA
# ====================================================================
elif menu == "📤 Upload & Process Data":
    st.markdown('<div class="main-header">📤 Upload & Process Academic Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload your own institution\'s Excel or CSV files to clean, analyze, and visualize them instantly</div>', unsafe_allow_html=True)

    # Active status banner
    active_ds = st.session_state.get('data_source_name', 'Default Demo')
    col_banner, col_reset = st.columns([3, 1])
    with col_banner:
        st.info(f"📂 **Currently Loaded Data:** `{active_ds}` ({len(df_summary)} students)")
    with col_reset:
        if st.button("↩️ Reset to Demo Dataset"):
            raw_sum, raw_det = load_processed_data()
            st.session_state["df_summary"] = raw_sum
            st.session_state["df_details"] = raw_det
            st.session_state["data_source_name"] = "Default Demo Dataset (150 Students)"
            st.success("Reverted to Default Demo Dataset!")
            st.rerun()

    st.markdown("---")
    
    # Template download card
    st.markdown("### 📥 Need a Template? Download Pre-Formatted Sample")
    st.caption("Download this sample Excel template with pre-filled multi-sheet structure (Students, Marks, Attendance) to test your own data.")
    sample_excel = generate_sample_excel_template()
    st.download_button(
        label="📥 Download Sample Excel Template (.xlsx)",
        data=sample_excel,
        file_name="student_academic_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="secondary"
    )
    
    st.markdown("---")
    st.markdown("### 📁 Choose Your Upload Method")
    tab_single, tab_multi = st.tabs(["📄 Option A: Single File (Multi-Sheet Excel or Unified CSV/Excel)", "📑 Option B: Three Separate Files (Students, Marks, Attendance)"])
    
    with tab_single:
        st.markdown("**Upload a single Excel file (.xlsx) or CSV (.csv)**")
        st.caption("Accepts a multi-sheet Excel file (with sheets for Students, Marks, Attendance) OR a combined table with columns for student details, marks, and attendance.")
        uploaded_single = st.file_uploader(
            "Select All-in-One Academic File", 
            type=["xlsx", "xls", "csv"], 
            key="uploader_single"
        )
        
    with tab_multi:
        st.markdown("**Upload 3 separate files for Students, Marks, and Attendance**")
        c_u1, c_u2, c_u3 = st.columns(3)
        with c_u1:
            u_st = st.file_uploader("1. Students Demographics", type=["csv", "xlsx", "xls"], key="u_st")
        with c_u2:
            u_mk = st.file_uploader("2. Course Marks", type=["csv", "xlsx", "xls"], key="u_mk")
        with c_u3:
            u_at = st.file_uploader("3. Attendance Records", type=["csv", "xlsx", "xls"], key="u_at")
            
    st.markdown("---")
    
    # Process Button
    if st.button("🚀 Clean, Process & Update Dashboard", type="primary"):
        target_st = None
        target_mk = None
        target_at = None
        desc_info = ""
        
        try:
            with st.spinner("Parsing uploaded file(s)..."):
                if uploaded_single is not None:
                    target_st, target_mk, target_at, desc_info = parse_uploaded_academic_data(uploaded_single)
                elif u_st is not None and u_mk is not None and u_at is not None:
                    target_st, target_mk, target_at, desc_info = parse_uploaded_academic_data(u_st, u_mk, u_at)
                else:
                    st.error("⚠️ Please select and upload file(s) before clicking Process.")
                    st.stop()
                    
            st.success(f"✅ Successfully detected format: **{desc_info}**")
            
            # Step 1: Clean Data
            with st.spinner("🧹 Running Data Quality & Anomaly Cleaning Pipeline..."):
                cleaner = DataCleaner()
                clean_st = cleaner.clean_students(target_st)
                clean_mk = cleaner.clean_marks(target_mk)
                clean_at = cleaner.clean_attendance(target_at)
                
            # Step 2: Feature Engineering
            with st.spinner("⚙️ Calculating Academic Scores, GPAs, and Standing Tiers..."):
                processor = DataProcessor()
                new_details, new_summary = processor.process_and_merge(clean_st, clean_mk, clean_at, save_master=False)
                
            # Step 3: Populate Database
            with st.spinner("🗄️ Ingesting into Relational Database..."):
                db.populate_database(clean_st, new_details, new_summary)
                
            # Step 4: Retrain ML Models
            with st.spinner("🤖 Retraining ML Grade Predictor on New Data..."):
                predictor = StudentPerformancePredictor()
                predictor.train_models(new_details)
                
            # Update Session State
            st.session_state["df_summary"] = new_summary
            st.session_state["df_details"] = new_details
            st.session_state["data_source_name"] = f"Custom Upload ({len(new_summary)} Students)"
            
            st.balloons()
            st.success(f"🎉 Analysis Complete! Loaded **{len(new_summary)} student profiles** and **{len(new_details)} course enrollments**.")
            
            # Display Cleaning Audit Log
            st.markdown("### 📋 Data Cleaning Audit Log")
            st.caption("Here are the data hygiene and anomaly corrections performed on your uploaded dataset:")
            st.dataframe(pd.DataFrame(cleaner.cleaning_audit_log), use_container_width=True)
            
            st.info("👉 **All Dashboard pages have been updated!** Click '📊 Overview & KPIs' in the sidebar to explore your new data.")
            
        except Exception as e:
            st.error(f"❌ Error processing uploaded file: {str(e)}")
            st.caption("Please check that your file includes valid student IDs and marks or download the sample template above.")


# ====================================================================
# PAGE 2: STUDENT DEEP-DIVE
# ====================================================================
elif menu == "👤 Student Deep-Dive":
    st.markdown('<div class="main-header">👤 Individual Student Performance Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Granular Academic Transcript, Course-level Diagnostics & Trajectory</div>', unsafe_allow_html=True)
    
    # Student Selector
    student_list = df_summary[["student_id", "name", "department"]].sort_values(by="student_id")
    student_labels = [f"{row['student_id']} - {row['name']} ({row['department']})" for _, row in student_list.iterrows()]
    
    col_sel, _ = st.columns([2, 1])
    with col_sel:
        chosen_label = st.selectbox("Select Student:", student_labels)
        
    chosen_id = int(chosen_label.split(" - ")[0])
    student_row = df_summary[df_summary["student_id"] == chosen_id].iloc[0]
    student_subjs = df_details[df_details["student_id"] == chosen_id].copy()
    
    # Student Profile Card
    st.markdown("---")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f"**Roll Number:** `{student_row['student_id']}`")
        st.markdown(f"**Full Name:** `{student_row['name']}`")
        st.markdown(f"**Gender:** `{student_row['gender']}`")
    with p2:
        st.markdown(f"**Department:** `{student_row['department']}`")
        st.markdown(f"**Year & Section:** `Year {student_row['year']} (Sec {student_row['section']})`")
        st.markdown(f"**Total Courses:** `{student_row['total_subjects']}`")
    with p3:
        st.markdown(f"**Average Marks:** `{student_row['average_marks']}%`")
        st.markdown(f"**Cumulative GPA:** `{student_row['gpa']} / 10.0`")
        st.markdown(f"**Performance Tier:** `{student_row['performance_category']}`")
    with p4:
        st.markdown(f"**Attendance Rate:** `{student_row['overall_attendance_pct']}%`")
        st.markdown(f"**Standing Status:** `{student_row['pass_status']}`")
        st.markdown(f"**Risk Profile:** `{student_row['risk_level']}`")
        
    st.markdown("---")
    
    # Detailed course table
    st.markdown("### 📋 Course Performance Breakdown")
    st.dataframe(
        student_subjs[[
            "subject", "internal", "mid1", "mid2", "assignment", "final", 
            "normalized_score", "attendance_pct", "subject_status", "subject_performance_cat"
        ]],
        use_container_width=True,
        column_config={
            "internal": st.column_config.NumberColumn("Internal (20)", format="%.1f"),
            "mid1": st.column_config.NumberColumn("Midterm 1 (25)", format="%.1f"),
            "mid2": st.column_config.NumberColumn("Midterm 2 (25)", format="%.1f"),
            "assignment": st.column_config.NumberColumn("Assignment (10)", format="%.1f"),
            "final": st.column_config.NumberColumn("Final Exam (100)", format="%.1f"),
            "normalized_score": st.column_config.ProgressColumn("Overall Score %", format="%.1f%%", min_value=0, max_value=100),
            "attendance_pct": st.column_config.ProgressColumn("Attendance %", format="%.1f%%", min_value=0, max_value=100),
        }
    )

    # Charts: Radar Chart & Exam Progression
    c_rad, c_line = st.columns(2)
    
    with c_rad:
        st.markdown("#### **Course Competency vs Class Average**")
        # Compute class average for each of student's subjects
        class_subj_avg = df_details.groupby("subject")["normalized_score"].mean().to_dict()
        
        categories = student_subjs["subject"].tolist()
        student_scores = student_subjs["normalized_score"].tolist()
        benchmark_scores = [round(class_subj_avg.get(s, 70), 1) for s in categories]
        
        # Close the polygon for radar chart
        categories_closed = categories + [categories[0]]
        student_closed = student_scores + [student_scores[0]]
        benchmark_closed = benchmark_scores + [benchmark_scores[0]]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=student_closed,
            theta=categories_closed,
            fill='toself',
            name=student_row['name'],
            line_color='#2563EB'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=benchmark_closed,
            theta=categories_closed,
            fill='toself',
            name='Class Benchmark',
            line_color='#9CA3AF',
            opacity=0.5
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            template="plotly_white",
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_line:
        st.markdown("#### **Examination Progression (Mid 1 ➔ Mid 2 ➔ Final Scaled)**")
        # Prepare progression data
        prog_data = []
        for _, sub in student_subjs.iterrows():
            prog_data.append({"Subject": sub["subject"], "Exam": "Mid 1 (Scaled %)", "Score": round((sub["mid1"] / 25.0) * 100, 1)})
            prog_data.append({"Subject": sub["subject"], "Exam": "Mid 2 (Scaled %)", "Score": round((sub["mid2"] / 25.0) * 100, 1)})
            prog_data.append({"Subject": sub["subject"], "Exam": "Final Exam (%)", "Score": round(sub["final"], 1)})
            
        df_prog = pd.DataFrame(prog_data)
        fig_line = px.line(
            df_prog,
            x="Exam",
            y="Score",
            color="Subject",
            markers=True,
            labels={"Score": "Normalized Score (%)", "Exam": "Assessment Milestone"},
            title=f"Assessment Trajectory for {student_row['name']}"
        )
        fig_line.update_layout(yaxis_range=[0, 105], template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)

    # Export Report Card
    st.markdown("### 📄 Official Report Card Generation")
    report_text = generate_student_report_card(student_row, student_subjs)
    
    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="📥 Download Academic Transcript (.txt)",
            data=report_text,
            file_name=f"transcript_student_{student_row['student_id']}.txt",
            mime="text/plain",
            type="primary"
        )
    with col_dl2:
        with st.expander("👁️ View Generated Academic Transcript Preview"):
            st.code(report_text, language="text")


# ====================================================================
# PAGE 3: SUBJECT ANALYTICS
# ====================================================================
elif menu == "📚 Subject Analytics":
    st.markdown('<div class="main-header">📚 Subject Curriculum Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluation of Course Difficulty, Score Distributions, and Failure Rates</div>', unsafe_allow_html=True)
    
    all_subjects = sorted(list(df_details["subject"].unique()))
    chosen_subj = st.selectbox("Select Subject Course for Deep Analysis:", all_subjects)
    
    subj_data = filtered_details[filtered_details["subject"] == chosen_subj].copy()
    
    if len(subj_data) == 0:
        st.warning(f"No records found for subject '{chosen_subj}' under current global filters.")
        st.stop()
        
    # Metrics
    mean_val = round(subj_data["normalized_score"].mean(), 1)
    median_val = round(subj_data["normalized_score"].median(), 1)
    highest_val = round(subj_data["normalized_score"].max(), 1)
    lowest_val = round(subj_data["normalized_score"].min(), 1)
    pass_pct = round((subj_data["subject_passed"].sum() / len(subj_data)) * 100.0, 1)
    avg_subj_att = round(subj_data["attendance_pct"].mean(), 1)
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Enrolled", len(subj_data))
    m2.metric("Subject Average", f"{mean_val}%")
    m3.metric("Median Score", f"{median_val}%")
    m4.metric("Highest Mark", f"{highest_val}%")
    m5.metric("Lowest Mark", f"{lowest_val}%")
    m6.metric("Pass Rate", f"{pass_pct}%")
    
    st.markdown("---")
    
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"#### **Marks Distribution for {chosen_subj}**")
        fig_hist = px.histogram(
            subj_data,
            x="normalized_score",
            nbins=15,
            color="subject_status",
            color_discrete_map={"Pass": "#10B981", "Fail": "#EF4444"},
            marginal="box",
            labels={"normalized_score": "Normalized Course Marks (%)"},
            title=f"Score Spread & Outliers ({chosen_subj})"
        )
        fig_hist.update_layout(template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with sc2:
        st.markdown("#### **Evaluation Components Breakdown**")
        # Component comparison
        comp_df = pd.DataFrame({
            "Component": ["Internal (20)", "Mid 1 (25)", "Mid 2 (25)", "Assignment (10)", "Final (100)"],
            "Class Average": [
                round(subj_data["internal"].mean(), 1),
                round(subj_data["mid1"].mean(), 1),
                round(subj_data["mid2"].mean(), 1),
                round(subj_data["assignment"].mean(), 1),
                round(subj_data["final"].mean(), 1)
            ],
            "Max Possible": [20, 25, 25, 10, 100]
        })
        comp_df["Achievement %"] = ((comp_df["Class Average"] / comp_df["Max Possible"]) * 100).round(1)
        
        fig_comp = px.bar(
            comp_df,
            x="Component",
            y="Achievement %",
            text="Achievement %",
            color="Achievement %",
            color_continuous_scale="Viridis",
            title=f"Class Mastery per Assessment Component"
        )
        fig_comp.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_comp.update_layout(yaxis_range=[0, 110], template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig_comp, use_container_width=True)

    # Subject ranking table
    st.markdown(f"### 🏆 Top & At-Risk Students in {chosen_subj}")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("**Top 5 Scorers**")
        top_s = subj_data.sort_values(by="normalized_score", ascending=False).head(5)
        st.dataframe(top_s[["student_id", "name", "department", "normalized_score", "attendance_pct"]], use_container_width=True)
        
    with s_col2:
        st.markdown("**Students At Risk in this Subject (Failed or < 50%)**")
        weak_s = subj_data[subj_data["normalized_score"] < 50.0].sort_values(by="normalized_score", ascending=True)
        if len(weak_s) > 0:
            st.dataframe(weak_s[["student_id", "name", "department", "normalized_score", "attendance_pct"]], use_container_width=True)
        else:
            st.success("🎉 All students achieved 50% or above in this subject!")


# ====================================================================
# PAGE 4: ATTENDANCE & CORRELATION
# ====================================================================
elif menu == "⏱️ Attendance & Correlation":
    st.markdown('<div class="main-header">⏱️ Attendance & Academic Association Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating Attendance Thresholds, Regression Correlation & Hall Ticket Eligibility</div>', unsafe_allow_html=True)
    
    corr_stats = analyzer.compute_attendance_correlation(filtered_summary)
    
    # Statistical Callout Box
    st.info(f"""
    🔬 **Statistical Association Report:**
    - **Pearson Correlation (\(r\)):** `{corr_stats.get('pearson_r', 0.0)}` (p-value: `{corr_stats.get('p_value', 1.0)}`)
    - **Coefficient of Determination (\(R^2\)):** `{corr_stats.get('r_squared', 0.0)}` (Explains ~{round(corr_stats.get('r_squared', 0)*100, 1)}% of variance)
    - **Methodological Disclaimer:** {corr_stats.get('interpretation', '')}
    """)
    
    ac1, ac2 = st.columns([3, 2])
    with ac1:
        st.markdown("#### **Attendance vs Performance Scatter Plot with OLS Regression**")
        fig_scatter_att = px.scatter(
            filtered_summary,
            x="overall_attendance_pct",
            y="average_marks",
            color="attendance_category",
            color_discrete_map={
                "Good (>85%)": "#10B981",
                "Normal (75-85%)": "#3B82F6",
                "At Risk (<75%)": "#EF4444"
            },
            hover_name="name",
            hover_data=["student_id", "department", "pass_status"],
            trendline="ols" if HAS_STATSMODELS else None,
            labels={"overall_attendance_pct": "Attendance (%)", "average_marks": "Average Academic Score (%)"}
        )
        # Add 75% critical threshold vertical line
        fig_scatter_att.add_vline(x=75, line_dash="dash", line_color="#EF4444", annotation_text="75% Mandatory Cutoff")
        fig_scatter_att.update_layout(template="plotly_white")
        st.plotly_chart(fig_scatter_att, use_container_width=True)
        
    with ac2:
        st.markdown("#### **Attendance Tier Breakdown**")
        att_tier = filtered_summary.groupby("attendance_category").agg(
            students=("student_id", "count"),
            avg_marks=("average_marks", "mean"),
            pass_count=("all_passed", "sum")
        ).reset_index()
        att_tier["pass_rate"] = ((att_tier["pass_count"] / att_tier["students"]) * 100).round(1)
        att_tier["avg_marks"] = att_tier["avg_marks"].round(1)
        
        fig_tier = px.bar(
            att_tier,
            x="attendance_category",
            y="avg_marks",
            color="attendance_category",
            color_discrete_map={
                "Good (>85%)": "#10B981",
                "Normal (75-85%)": "#3B82F6",
                "At Risk (<75%)": "#EF4444"
            },
            text="avg_marks",
            title="Average Marks by Attendance Standing"
        )
        fig_tier.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_tier.update_layout(yaxis_range=[0, 100], template="plotly_white", showlegend=False)
        st.plotly_chart(fig_tier, use_container_width=True)

    st.markdown("---")
    
    # Practical Faculty Tool: Attendance Shortage Intervention Table
    st.markdown("### 🚨 Attendance Shortage & Hall Ticket Eligibility Tracker (< 75%)")
    st.caption("Identifies students who are currently ineligible for semester examinations and calculates how many consecutive classes they must attend to cross the 75% bar.")
    
    shortage_students = filtered_summary[filtered_summary["overall_attendance_pct"] < 75.0].copy()
    if len(shortage_students) > 0:
        # Calculate classes needed to reach 75%: (attended + x) / (total + x) = 0.75  =>  x = (0.75*total - attended) / 0.25
        shortage_students["classes_needed_for_75"] = shortage_students.apply(
            lambda r: max(0, int(np.ceil((0.75 * r["total_classes"] - r["total_attended"]) / 0.25))),
            axis=1
        )
        st.dataframe(
            shortage_students[[
                "student_id", "name", "department", "year", "section", 
                "total_classes", "total_attended", "overall_attendance_pct", 
                "classes_needed_for_75", "average_marks", "risk_level"
            ]],
            use_container_width=True,
            column_config={
                "overall_attendance_pct": st.column_config.ProgressColumn("Attendance %", format="%.1f%%", min_value=0, max_value=100),
                "classes_needed_for_75": st.column_config.NumberColumn("Classes Needed to Reach 75%", help="Consecutive classes required"),
                "student_id": st.column_config.NumberColumn("Roll No", format="%d")
            }
        )
    else:
        st.success("🎉 Excellent! No students have attendance below 75% under the current filters.")


# ====================================================================
# PAGE 5: ML PERFORMANCE PREDICTOR
# ====================================================================
elif menu == "🤖 ML Performance Predictor":
    st.markdown('<div class="main-header">🤖 Predictive Grade Modeling & What-If Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pre-Final Risk Early Warning System Powered by Supervised Machine Learning</div>', unsafe_allow_html=True)
    
    predictor = StudentPerformancePredictor(model_dir=os.path.join(PROJECT_ROOT, "data", "models"))
    loaded = predictor.load_models()
    
    if not loaded:
        with st.spinner("Training predictive machine learning models on dataset..."):
            metrics = predictor.train_models(df_details)
            st.success(f"Models trained successfully! Classifier Accuracy: {metrics['classifier_accuracy']}%")
            
    st.markdown("### 🎛️ Interactive 'What-If' Scenario Simulator")
    st.caption("Adjust mid-semester marks and attendance to simulate the student's predicted final exam outcome and risk standing.")
    
    s1, s2 = st.columns([1, 1])
    with s1:
        sim_att = st.slider("Attendance Percentage (%)", min_value=40.0, max_value=100.0, value=82.0, step=1.0)
        sim_internal = st.slider("Internal Continuous Assessment (Max: 20)", min_value=0.0, max_value=20.0, value=16.0, step=0.5)
        sim_mid1 = st.slider("Midterm Exam 1 (Max: 25)", min_value=0.0, max_value=25.0, value=19.0, step=0.5)
        sim_mid2 = st.slider("Midterm Exam 2 (Max: 25)", min_value=0.0, max_value=25.0, value=21.0, step=0.5)
        sim_assign = st.slider("Assignment & Project Work (Max: 10)", min_value=0.0, max_value=10.0, value=8.5, step=0.5)
        
        predict_btn = st.button("🔮 Run Model Inference", type="primary")

    with s2:
        res = predictor.predict(sim_att, sim_internal, sim_mid1, sim_mid2, sim_assign)
        
        # Display Results
        pred_cat = res["predicted_category"]
        pred_final = res["predicted_final_score"]
        pred_overall = res["estimated_overall_percentage"]
        is_risk = res["is_at_risk"]
        
        cat_color = CATEGORY_COLORS.get(pred_cat, "#3B82F6")
        
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 2px solid {cat_color}; border-radius: 12px; padding: 20px; margin-top: 10px;">
            <h3 style="margin-top:0; color: #1E3A8A;">Model Inference Results</h3>
            <p style="font-size: 1.1rem; margin-bottom: 5px;">
                Predicted Standing: <span style="background-color: {cat_color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{pred_cat}</span>
            </p>
            <p style="font-size: 1.1rem; margin-bottom: 5px;">
                Estimated Final Exam Mark: <b>{pred_final} / 100</b>
            </p>
            <p style="font-size: 1.1rem; margin-bottom: 5px;">
                Projected Overall Academic %: <b>{pred_overall}%</b>
            </p>
            <p style="font-size: 1.1rem; margin-bottom: 0;">
                Risk Status: <b style="color: {'#EF4444' if is_risk else '#10B981'};">{res['risk_label']}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Category Probabilities
        prob_df = pd.DataFrame(list(res["category_probabilities"].items()), columns=["Category", "Probability (%)"])
        fig_prob = px.bar(
            prob_df,
            x="Category",
            y="Probability (%)",
            color="Category",
            color_discrete_map=CATEGORY_COLORS,
            title="Model Class Likelihood Distribution (%)"
        )
        fig_prob.update_layout(template="plotly_white", showlegend=False, margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig_prob, use_container_width=True)

    # Automated Recommendations
    st.markdown("#### 💡 AI Faculty & Student Recommendations:")
    for rec in res["recommendations"]:
        st.markdown(f"- {rec}")

    st.markdown("---")
    st.markdown("### 📊 Model Architecture & Explainability (Feature Importance)")
    st.markdown("""
    The system employs an **Ensemble Random Forest Classifier** combined with a **Gradient Boosting Regressor** 
    to evaluate feature attribution across continuous assessment inputs.
    """)
    if predictor.metrics_ and "feature_importances" in predictor.metrics_:
        imp_df = pd.DataFrame(
            list(predictor.metrics_["feature_importances"].items()),
            columns=["Feature", "Relative Importance"]
        ).sort_values(by="Relative Importance", ascending=True)
        
        fig_imp = px.bar(
            imp_df,
            x="Relative Importance",
            y="Feature",
            orientation='h',
            color="Relative Importance",
            color_continuous_scale="Blues",
            title="Feature Predictive Weight in Determining Final Grade"
        )
        fig_imp.update_layout(template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig_imp, use_container_width=True)


# ====================================================================
# PAGE 6: SQL QUERY EXPLORER
# ====================================================================
elif menu == "💻 SQL Query Explorer":
    st.markdown('<div class="main-header">💻 SQL Analytics Playground</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live SQL Query Execution Against the Relational Database Engine</div>', unsafe_allow_html=True)
    st.markdown("This playground demonstrates relational SQL querying, aggregations, window functions, and analytics for database workflows.")
    
    # Pre-built queries
    prebuilt_queries = {
        "1. Department-wise Performance Benchmarks": """
SELECT 
    department,
    COUNT(student_id) AS total_students,
    ROUND(AVG(average_marks), 2) AS dept_avg_marks,
    ROUND(AVG(overall_attendance_pct), 2) AS dept_avg_attendance,
    ROUND(AVG(gpa), 2) AS dept_avg_gpa
FROM student_summary
GROUP BY department
ORDER BY dept_avg_marks DESC;
        """,
        "2. Subject Difficulty Ranking & Pass Rate": """
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
        """,
        "3. Top 3 Students Per Department (Window DENSE_RANK)": """
WITH RankedStudents AS (
    SELECT 
        student_id,
        name,
        department,
        average_marks,
        overall_attendance_pct,
        performance_category,
        DENSE_RANK() OVER (PARTITION BY department ORDER BY average_marks DESC) AS dept_position
    FROM student_summary
)
SELECT * FROM RankedStudents WHERE dept_position <= 3;
        """,
        "4. Attendance Impact Breakdown (<75%, 75-85%, >85%)": """
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
        """,
        "5. Early Warning: At-Risk Students Requiring Intervention": """
SELECT 
    student_id,
    name,
    department,
    year,
    section,
    average_marks,
    overall_attendance_pct,
    risk_level
FROM student_summary
WHERE risk_level IN ('High Risk', 'Moderate Risk')
ORDER BY overall_attendance_pct ASC;
        """,
        "6. Exam Trajectory: Mid 1 vs Mid 2 Performance Delta": """
SELECT 
    subject,
    ROUND(AVG(mid1), 2) AS avg_mid1,
    ROUND(AVG(mid2), 2) AS avg_mid2,
    ROUND(AVG(mid2 - mid1), 2) AS avg_growth,
    SUM(CASE WHEN mid2 > mid1 THEN 1 ELSE 0 END) AS students_improved
FROM marks
GROUP BY subject
ORDER BY avg_growth DESC;
        """
    }
    
    preset_choice = st.selectbox("Choose a Pre-Built Analytical Query:", list(prebuilt_queries.keys()))
    default_sql = prebuilt_queries[preset_choice].strip()
    
    user_sql = st.text_area("SQL Editor (SQLite / ANSI Compatible):", value=default_sql, height=180)
    
    col_exec, col_down = st.columns([1, 4])
    with col_exec:
        execute_clicked = st.button("▶️ Execute Query", type="primary")
        
    try:
        sql_result = db.run_query(user_sql)
        st.success(f"Query returned **{len(sql_result)}** rows successfully.")
        st.dataframe(sql_result, use_container_width=True)
        
        # Download SQL Result
        csv_bytes = convert_df_to_csv(sql_result)
        st.download_button(
            label="📥 Download Query Result (CSV)",
            data=csv_bytes,
            file_name="sql_query_result.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"SQL Execution Error: {e}")


# ====================================================================
# PAGE 7: EXPORT & REPORTS
# ====================================================================
elif menu == "📥 Export & Reports":
    st.markdown('<div class="main-header">📥 Data Export & Executive Reporting</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate Filtered CSV Reports, Audit Logs, and Comprehensive Summaries</div>', unsafe_allow_html=True)
    
    st.markdown("### 📊 Export Active Filtered Datasets")
    st.write(f"Active Filters: Department: **{selected_dept}**, Year: **{selected_year}**, Section: **{selected_sec}**, Standing: **{selected_perf}**")
    
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.markdown("#### **Student Summary Report**")
        st.caption(f"{len(filtered_summary)} student profiles")
        csv_summary = convert_df_to_csv(filtered_summary)
        st.download_button(
            label="📥 Download Student Summary CSV",
            data=csv_summary,
            file_name=f"student_summary_{selected_dept}_{selected_year}.csv",
            mime="text/csv",
            type="primary"
        )
        
    with col_e2:
        st.markdown("#### **Course-Level Marks Report**")
        st.caption(f"{len(filtered_details)} course grade records")
        csv_details = convert_df_to_csv(filtered_details)
        st.download_button(
            label="📥 Download Detailed Marks CSV",
            data=csv_details,
            file_name=f"course_marks_{selected_dept}_{selected_year}.csv",
            mime="text/csv"
        )
        
    with col_e3:
        st.markdown("#### **Data Cleaning Audit Log**")
        audit_path = os.path.join(PROJECT_ROOT, "data", "processed", "cleaning_audit_log.csv")
        if os.path.exists(audit_path):
            df_audit = pd.read_csv(audit_path)
            csv_audit = convert_df_to_csv(df_audit)
            st.download_button(
                label="📥 Download Cleaning Audit Log",
                data=csv_audit,
                file_name="data_cleaning_audit_log.csv",
                mime="text/csv"
            )
        else:
            st.write("Audit log not found.")

    st.markdown("---")
    st.markdown("### 📑 Institutional Analysis Summary Report")
    
    kpis = analyzer.get_kpis(filtered_summary)
    dept_benchmarks = analyzer.get_department_comparison()
    subj_benchmarks = analyzer.get_subject_performance_summary(filtered_details)
    
    report_md = f"""# 🎓 Institutional Student Performance Analytics Report
Generated: Current Academic Session

## 1. Executive Summary
- **Total Students Evaluated:** {kpis.get('total_students', 0)}
- **Institutional Average Marks:** {kpis.get('avg_marks', 0)}%
- **Institutional Average Attendance:** {kpis.get('avg_attendance', 0)}%
- **Overall Pass Percentage:** {kpis.get('pass_rate', 0)}%
- **Students Requiring Academic Support (At Risk):** {kpis.get('at_risk_count', 0)} ({kpis.get('at_risk_pct', 0)}%)

## 2. Department Benchmarks
{df_to_markdown_safe(dept_benchmarks)}

## 3. Course Curriculum Benchmarks
{df_to_markdown_safe(subj_benchmarks[["subject", "enrolled", "avg_normalized_score", "pass_percentage", "avg_attendance"]])}

---
*Report generated by Student Performance Analytics Platform.*
"""
    with st.expander("👁️ Preview Institutional Summary Report"):
        st.markdown(report_md)
        
    st.download_button(
        label="📥 Download Executive Report (.md)",
        data=report_md.encode("utf-8"),
        file_name="academic_performance_report.md",
        mime="text/markdown"
    )

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Student Performance Analytics & Visualization Platform • Resume-Ready Full Stack Data Project</p>", unsafe_allow_html=True)

