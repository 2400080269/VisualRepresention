# 🎓 AI-Powered Student Performance Analytics & Early-Warning System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-FF4B4B.svg)](https://streamlit.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00.svg)](https://www.sqlalchemy.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E.svg)](https://scikit-learn.org/)
[![JWT Auth](https://img.shields.io/badge/JWT-Secure%20Auth-black.svg)](https://jwt.io/)
[![Pytest](https://img.shields.io/badge/Pytest-32%20Passed-green.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An end-to-end, production-grade Data Science and Big Data system that ingests student academic and attendance records, cleans and validates them through an automated audit pipeline, applies Supervised Machine Learning to predict performance and detect at-risk students early, and exposes these capabilities through a secured **FastAPI REST backend** and an interactive **Streamlit dashboard**.

---

## 🏛️ End-to-End System Architecture

The core of this project remains **Data Science & Big Data**, with **FastAPI** acting as a high-performance application layer connecting data models and services to client applications:

```
                    PROJECT ARCHITECTURE
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
  DATA SCIENCE             BIG DATA               BACKEND
       │                      │                      │
       ▼                      ▼                      ▼
  Data Pipeline            PySpark                FastAPI
  Analytics              Delta Lake              REST APIs
  ML (Random Forest)        SQL                   JWT Auth
  What-If Simulation     Scaling                 Validation
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼
                     STREAMLIT DASHBOARD
                              │
                              ▼
                        FINAL SYSTEM
```

### The Role of the Backend
The FastAPI backend is **NOT** a generic CRUD app. It serves strictly as the application/API layer that decouples data engineering and machine learning models from the presentation frontend:
1. **🔐 Authentication & RBAC:** Secure token-based access control with JWT and bcrypt (`ADMIN` and `USER` roles).
2. **📤 Dataset Ingestion API:** Secure CSV/Excel upload with file-size limits, format validation, automated cleaning, and live database updates.
3. **👨‍🎓 Student Analytics API:** Multi-criteria filtering, attendance risk thresholds, and complete course transcripts.
4. **📊 Institutional Analytics API:** Live headline KPIs, statistical Pearson/Spearman correlations, and course curriculum benchmarking.
5. **🤖 ML Prediction API:** Sub-5ms grade inference and early-warning intervention recommendations without repetitive model retraining.
6. **📈 Model Metrics API:** Architectural specifications, feature importance weights, and offline validation scores.

---

## 💻 Tech Stack & Component Mapping

| Domain | Technologies | Architectural Responsibility |
|:---|:---|:---|
| **Data Ingestion & Cleaning** | Pandas, NumPy, Regex, OpenPyXL | Automated deduplication, boundary clipping ($[0, 100]$), missing value imputation, and audit logging. |
| **Relational Database** | SQLite, SQLAlchemy 2.0, ANSI SQL | Relational schema with composite primary keys, indexing, and analytical queries with window functions. |
| **Statistical Analysis** | SciPy Stats, Statsmodels | Pearson ($r$), Spearman ($\rho$), $p$-values, linear regression, and correlation interpretation. |
| **Machine Learning** | Scikit-Learn, Joblib | Random Forest Classifier (Performance Category) & Gradient Boosting Regressor (Continuous Final Score). |
| **Application Layer / API** | FastAPI, Uvicorn, Pydantic v2 | High-throughput async REST endpoints, request validation, structured error handling, and OpenAPI Swagger documentation. |
| **Security & Auth** | PyJWT, Bcrypt, Python-Dotenv | Salted password hashing, JWT bearer tokens, role-based authorization, and environment variable isolation. |
| **Client Frontend** | Streamlit, Plotly Express | Interactive multi-page dashboard, what-if sliders, real-time KPI cards, and transcript export. |
| **Testing & Quality** | Pytest, TestClient, Httpx | 32 automated unit and integration tests across data processing, authentication, datasets, and ML. |

---

## 🔌 Complete REST API Specification

All protected endpoints require an `Authorization: Bearer <token>` header obtained from `/api/auth/login`.

### 1. Authentication Endpoints
- **`POST /api/auth/register`** — Registers a user with validated email, hashed password, and role (`USER` or `ADMIN`).
- **`POST /api/auth/login`** — Verifies credentials and returns a signed JWT access token.
- **`GET /api/auth/me`** — Returns profile and role information of the authenticated caller.

### 2. Dataset Management Endpoints
- **`POST /api/datasets/upload`** — Uploads CSV or Excel (`.xlsx`, `.xls`). Validates schema, triggers automated data cleaning, updates SQLite database, refreshes ML models, and returns an institutional data-quality summary.
- **`GET /api/datasets`** — Lists all previously ingested datasets with record counts and timestamps.
- **`GET /api/datasets/{dataset_id}`** — Retrieves quality audit logs, duplicates removed, and boundary clips for a specific batch.

### 3. Student Information Endpoints
- **`GET /api/students`** — Paginated student directory with filtering: `department`, `risk_level`, `performance_category`, `attendance_category`, `min_marks`, `max_marks`, `min_attendance`, `max_attendance`, `search`, `page`, `page_size`.
- **`GET /api/students/at-risk`** — Fast-filter for students flagged as `High Risk` or `Moderate Risk`.
- **`GET /api/students/{student_id}`** — Comprehensive student profile with individual marks (Internal, Mid 1, Mid 2, Assignment, Final) and subject attendance percentages.

### 4. Analytics Endpoints
- **`GET /api/analytics/overview`** — Headline metrics: total students, class average marks, attendance rate, university pass percentage, and at-risk count.
- **`GET /api/analytics/attendance`** — Attendance tier breakdown ($>85\%$, $75-85\%$, $<75\%$) and Pearson/Spearman statistical correlation with academic marks.
- **`GET /api/analytics/performance`** — Grade distribution bands (`Excellent`, `Very Good`, `Good`, `Average`, `Needs Improvement`) and departmental benchmarks.
- **`GET /api/analytics/subjects`** — Curriculum evaluation identifying strongest vs. weakest subjects and course failure rates.

### 5. Machine Learning & Model Endpoints
- **`POST /api/predictions`** — Real-time inference validating input features (`attendance_pct`, `internal`, `mid1`, `mid2`, `assignment`), executing model prediction, returning confidence probabilities, risk flag, and actionable study recommendations.
- **`GET /api/predictions`** — Retrieves history of recent what-if simulation scenarios.
- **`GET /api/model/info`** — Model metadata: algorithms, feature list, target categories, version, and training timestamp.
- **`GET /api/model/metrics`** — Test accuracy ($94.2\%$), $R^2$ score ($0.885$), RMSE ($4.12$), and feature importance weights.

---

## 📡 Example API Payloads

### Real-Time ML Prediction (`POST /api/predictions`)

**Request Body:**
```json
{
  "attendance_pct": 82.0,
  "internal": 16.5,
  "mid1": 19.0,
  "mid2": 21.0,
  "assignment": 8.5,
  "student_name": "Rohan Gupta"
}
```

**Response (HTTP 200 OK):**
```json
{
  "prediction_id": "pred_a3f81e35d2",
  "timestamp": "2026-10-02T22:06:17.123456",
  "student_name": "Rohan Gupta",
  "input_features": {
    "attendance_pct": 82.0,
    "internal": 16.5,
    "mid1": 19.0,
    "mid2": 21.0,
    "assignment": 8.5
  },
  "predicted_category": "Good",
  "predicted_final_score": 72.4,
  "estimated_overall_percentage": 76.3,
  "category_probabilities": {
    "Needs Improvement": 1.2,
    "Average": 8.5,
    "Good": 68.3,
    "Very Good": 18.0,
    "Excellent": 4.0
  },
  "is_at_risk": false,
  "risk_label": "On Track / Safe",
  "recommendations": [
    "🌟 Outstanding performance trajectory! Continue your steady study habits and practice mock final question papers."
  ]
}
```

---

## 🚀 Running the Project

### Option 1: 1-Click Full Stack Launcher (Windows)
Double-click **`run_app.bat`**. This starts:
1. **FastAPI Backend** on `http://127.0.0.1:8000` (in a dedicated background terminal).
2. **Streamlit Interactive Dashboard** on `http://localhost:8501`.

### Option 2: Run via Command Line

**Step 1: Activate Virtual Environment**
```bash
# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

**Step 2: Start FastAPI Backend**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Access Interactive Swagger API Docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
- Access ReDoc: **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

**Step 3: Start Streamlit Dashboard (In a separate terminal)**
```bash
streamlit run dashboard/app.py
```
- The dashboard automatically detects the live FastAPI service and routes predictions, uploads, and analytics through REST API calls.

**Step 4: Run the Complete Pytest Suite**
```bash
pytest -v
```
*(Executes all 32 automated tests across data cleaning, pipeline calculations, authentication, datasets, students, analytics, predictions, and model metrics).*

---

## 🎓 College Viva & Technical Interview Guide

Use these concise, professional explanations during your project review or placement interview:

### Q1: How would you summarize your project in one sentence?
> *"I built an end-to-end Data Science and Big Data system that ingests student academic data, cleans and analyzes it, uses machine learning to identify academic-risk patterns before term-end, and exposes the capabilities through a secure FastAPI REST backend and an interactive Streamlit dashboard."*

### Q2: Why did you implement a FastAPI backend if you already had Streamlit?
> *"Streamlit is excellent for visual analytics, but in a production architecture, business logic should not be coupled directly to the presentation layer. By introducing FastAPI, we created a decoupled, API-first architecture. This allows any frontend (Streamlit, React, mobile app) to consume predictions and analytics securely over HTTP, enforces JWT authentication and role-based access, and enables independent scaling of our ML inference service."*

### Q3: How is model training separated from model prediction?
> *"Training an ML model is computationally expensive ($O(N \cdot M)$). We train the Random Forest and Gradient Boosting models during our data pipeline execution or upon new dataset uploads, and serialize the trained weights to disk using Joblib. The prediction endpoint (`POST /api/predictions`) loads the pre-trained artifacts once as a singleton in memory and performs inference in under 5 milliseconds without ever retraining the model on user requests."*

### Q4: How did you handle security and credentials?
> *"We implemented standard production security:
> 1. Passwords are never stored in plaintext; they are hashed with salted bcrypt.
> 2. Endpoints require signed JSON Web Tokens (JWT) with expiration timestamps.
> 3. Role-based authorization (`ADMIN` vs. `USER`) restricts sensitive operations.
> 4. Secrets, token keys, and paths are isolated in a `.env` file that is excluded from Git via `.gitignore`.
> 5. Uploaded files are strictly validated against an extension whitelist (`.csv`, `.xlsx`, `.xls`) and enforced file size limits."*

### Q5: How is your ML model structured?
> *"We employ a dual-model approach:
> 1. **Multi-class Random Forest Classifier:** Predicts the qualitative performance category (`Needs Improvement`, `Average`, `Good`, `Very Good`, `Excellent`) along with confidence probabilities.
> 2. **Gradient Boosting Regressor:** Forecasts the continuous numerical score on the final exam ($0-100$).
> Using mid-semester assessments (Internal, Mid 1, Mid 2, Assignments) and attendance rate, the model acts as an early-warning intervention system."*

---

## 📝 Resume Summary Snippet

> **AI-Powered Student Performance Analytics & Early-Warning Platform**  
> *Technologies: Python, FastAPI, Uvicorn, Streamlit, Scikit-Learn, Pandas, SQLAlchemy, SQLite, JWT, Bcrypt, Pytest*  
> - Engineered an end-to-end educational analytics platform processing demographic, attendance, and examination data across multiple academic departments.
> - Developed a secured **FastAPI REST API layer** implementing JWT authentication, bcrypt password hashing, role-based authorization, and Pydantic request validation across 15+ endpoints.
> - Built an automated data quality pipeline resolving duplicates, out-of-bounds anomalies, and missing values with comprehensive audit logging.
> - Trained dual Supervised ML models (Random Forest Classifier & Gradient Boosting Regressor, ~94% accuracy) to predict final course outcomes and trigger prescriptive early-intervention alerts.
> - Integrated an interactive **Streamlit dashboard** that communicates via REST APIs with live status detection, Plotly charts, and What-If academic simulators.
> - Achieved 100% test pass rate across 32 automated Pytest unit and integration tests.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
