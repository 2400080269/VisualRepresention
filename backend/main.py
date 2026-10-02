"""
Main FastAPI application entrypoint for Student Performance Analytics Platform.
Provides API routing, CORS middleware, global error handling, and health diagnostics.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.database.connection import init_db
from backend.api.auth import router as auth_router
from backend.api.datasets import router as datasets_router
from backend.api.students import router as students_router
from backend.api.analytics import router as analytics_router
from backend.api.predictions import router as predictions_router
from backend.api.models import router as models_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    logger.info("Initializing Student Performance Analytics Backend API...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    logger.info(f"Database target: {settings.DATABASE_URL}")
    init_db()
    yield
    logger.info("Shutting down API server gracefully...")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend API supporting the AI-Powered Student Performance Analytics & "
        "Early-Warning System. Provides endpoints for Authentication, Dataset Ingestion, "
        "Student Records, Analytical Aggregations, ML Grade Predictions, and Model Metrics."
    ),
    openapi_tags=[
        {"name": "System", "description": "System health and status checks"},
        {"name": "Authentication", "description": "User registration, JWT login, and profile"},
        {"name": "Datasets", "description": "Dataset file upload, validation, and quality audit"},
        {"name": "Students", "description": "Student academic profiles and risk queries"},
        {"name": "Analytics", "description": "Performance, attendance, and subject statistics"},
        {"name": "Predictions", "description": "Machine learning grade inference and early warning"},
        {"name": "Model", "description": "Trained ML model specifications and performance metrics"},
    ],
    lifespan=lifespan
)

# Configure CORS
origins = settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "error": exc.detail,
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        error_details.append({
            "field": field,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })
    logger.warning(f"Validation error on {request.url.path}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "status_code": 422,
            "error": "Validation failed",
            "details": error_details,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    # Never expose internal raw stack trace to the user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": 500,
            "error": "Internal server error occurred. Please contact the administrator.",
            "path": request.url.path
        }
    )

# -----------------------------------------------------------------------------
# Base Diagnostic Routes
# -----------------------------------------------------------------------------
@app.get("/", tags=["System"], summary="API Root Status")
async def root():
    return {
        "success": True,
        "message": f"Welcome to the {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health", tags=["System"], summary="API Health Check")
async def health_check():
    db_exists = os.path.exists(settings.SQLITE_DB_PATH)
    clf_model_exists = os.path.exists(settings.MODELS_DIR / "classifier.joblib")
    reg_model_exists = os.path.exists(settings.MODELS_DIR / "regressor.joblib")

    return {
        "status": "healthy",
        "api_version": settings.VERSION,
        "database": {
            "connected": db_exists,
            "target": str(settings.SQLITE_DB_PATH.name)
        },
        "machine_learning": {
            "classifier_available": clf_model_exists,
            "regressor_available": reg_model_exists
        }
    }

# Include API Routers
app.include_router(auth_router)
app.include_router(datasets_router)
app.include_router(students_router)
app.include_router(analytics_router)
app.include_router(predictions_router)
app.include_router(models_router)
