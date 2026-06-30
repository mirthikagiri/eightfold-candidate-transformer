from typing import Dict, Any

import pandas as pd

from app.adapters.base import BaseAdapter


class CSVAdapter(BaseAdapter):
    """
    Adapter for Recruiter CSV files.

    Expected columns:
    - name
    - email
    - phone
    - current_company
    - title
    """

    def extract(self, source_path: str) -> Dict[str, Any]:
        try:
            df = pd.read_csv(source_path)

            if df.empty:
                return {}

            row = df.iloc[0]

            return {
                "full_name": self._safe_get(row, "name"),
                "emails": self._build_list(row, "email"),
                "phones": self._build_list(row, "phone"),
                "headline": self._safe_get(row, "title"),
                "current_company": self._safe_get(row, "current_company"),
                "source": "recruiter_csv"
            }

        except Exception as e:
            print(f"[CSVAdapter] Error reading CSV: {e}")
            return {}

    @staticmethod
    def _safe_get(row, column_name):
        """
        Safely fetch a value from a row.
        Returns None if missing or NaN.
        """
        try:
            value = row.get(column_name)

            if pd.isna(value):
                return None

            return str(value).strip()

        except Exception:
            return None

    @staticmethod
    def _build_list(row, column_name):
        """
        Convert a single CSV field into a list.
        Returns [] when missing.
        """
        value = CSVAdapter._safe_get(row, column_name)

        if not value:
            return []

        return [value]