from typing import Any, Dict, List

import pandas as pd

from app.adapters.base import BaseAdapter
from app.normalizers.email import normalize_email
from app.normalizers.location import normalize_location
from app.normalizers.phone import normalize_phone


class CSVAdapter(BaseAdapter):
    """
    Adapter for Recruiter CSV files.

    Expected columns:
    - name
    - email
    - phone
    - current_company
    - title
    - location (optional)
    """

    def extract(self, source_path: str) -> Dict[str, Any]:
        try:
            df = pd.read_csv(source_path)

            if df.empty:
                return {"source": "recruiter_csv"}

            row = df.iloc[0]
            uncertain_fields: List[str] = []

            raw_phone = self._safe_get(row, "phone")
            phones = []
            if raw_phone:
                normalized_phone = normalize_phone(raw_phone)
                phones.append(normalized_phone or raw_phone)
                if normalized_phone is None:
                    uncertain_fields.append("phones")

            raw_email = self._safe_get(row, "email")
            emails = []
            if raw_email:
                normalized_email = normalize_email(raw_email)
                if normalized_email:
                    emails.append(normalized_email)

            location = normalize_location(self._safe_get(row, "location"))

            return {
                "full_name": self._safe_get(row, "name"),
                "emails": emails,
                "phones": phones,
                "headline": self._safe_get(row, "title"),
                "current_company": self._safe_get(row, "current_company"),
                "location": location,
                "source": "recruiter_csv",
                "_uncertain_fields": uncertain_fields,
            }

        except Exception as e:
            print(f"[CSVAdapter] Error reading CSV: {e}")
            return {"source": "recruiter_csv"}

    @staticmethod
    def _safe_get(row, column_name):
        try:
            value = row.get(column_name)

            if pd.isna(value):
                return None

            return str(value).strip()

        except Exception:
            return None
