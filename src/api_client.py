"""
Module: api_client.py
Purpose: Lightweight HTTP client enabling Streamlit to communicate with
the FastAPI backend for Authentication, Analytics, Predictions, and File Ingestion.
Includes automatic failover to local services if the backend is not actively running.
"""

import os
import requests
from typing import Optional, Dict, Any

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

class BackendAPIClient:
    def __init__(self, base_url: str = DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    def is_backend_online(self) -> bool:
        """Pings the FastAPI /health endpoint to check server availability."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=1.5)
            return res.status_code == 200
        except Exception:
            return False

    def authenticate(self, username: str = "streamlit_admin", password: str = "StreamlitAdminPass123!") -> bool:
        """
        Authenticates against FastAPI backend, registering default service account if needed.
        """
        # Try Login
        login_url = f"{self.base_url}/api/auth/login"
        payload = {"username_or_email": username, "password": password}
        try:
            res = requests.post(login_url, json=payload, timeout=3)
            if res.status_code == 200:
                self.token = res.json().get("access_token")
                return True
        except Exception:
            return False

        # Try Register if not exists
        reg_url = f"{self.base_url}/api/auth/register"
        reg_payload = {
            "username": username,
            "email": f"{username}@institution.edu",
            "password": password,
            "role": "ADMIN"
        }
        try:
            res = requests.post(reg_url, json=reg_payload, timeout=3)
            if res.status_code in [200, 201]:
                # Now login
                login_res = requests.post(login_url, json=payload, timeout=3)
                if login_res.status_code == 200:
                    self.token = login_res.json().get("access_token")
                    return True
        except Exception:
            return False

        return False

    def _get_headers(self) -> Dict[str, str]:
        if not self.token:
            self.authenticate()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_overview_kpis(self) -> Optional[Dict[str, Any]]:
        """GET /api/analytics/overview"""
        try:
            res = requests.get(f"{self.base_url}/api/analytics/overview", headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def get_attendance_analytics(self) -> Optional[Dict[str, Any]]:
        """GET /api/analytics/attendance"""
        try:
            res = requests.get(f"{self.base_url}/api/analytics/attendance", headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def get_performance_analytics(self) -> Optional[Dict[str, Any]]:
        """GET /api/analytics/performance"""
        try:
            res = requests.get(f"{self.base_url}/api/analytics/performance", headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def get_subjects_analytics(self) -> Optional[Dict[str, Any]]:
        """GET /api/analytics/subjects"""
        try:
            res = requests.get(f"{self.base_url}/api/analytics/subjects", headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def predict_performance(
        self,
        attendance_pct: float,
        internal: float,
        mid1: float,
        mid2: float,
        assignment: float,
        student_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """POST /api/predictions"""
        payload = {
            "attendance_pct": float(attendance_pct),
            "internal": float(internal),
            "mid1": float(mid1),
            "mid2": float(mid2),
            "assignment": float(assignment),
            "student_name": student_name
        }
        try:
            res = requests.post(f"{self.base_url}/api/predictions", json=payload, headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """GET /api/model/info"""
        try:
            res = requests.get(f"{self.base_url}/api/model/info", headers=self._get_headers(), timeout=4)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def get_model_metrics(self) -> Optional[Dict[str, Any]]:
        """GET /api/model/metrics"""
        try:
            res = requests.get(f"{self.base_url}/api/model/metrics", headers=self._get_headers(), timeout=4)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    def upload_dataset(self, file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """POST /api/datasets/upload"""
        if not self.token:
            self.authenticate()
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        files = {"file": (filename, file_bytes, "application/octet-stream")}
        try:
            res = requests.post(f"{self.base_url}/api/datasets/upload", files=files, headers=headers, timeout=25)
            if res.status_code in [200, 201]:
                return res.json()
        except Exception:
            pass
        return None

# Global client singleton
api_client = BackendAPIClient()
