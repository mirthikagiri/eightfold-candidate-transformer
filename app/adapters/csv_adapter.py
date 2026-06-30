from typing import Any, Dict, List

import pandas as pd

from app.adapters.base import BaseAdapter
from app.normalizers.email import normalize_email_with_report
from app.normalizers.location import normalize_location
from app.normalizers.phone import normalize_phone_with_report
from app.normalizers.result import NormalizationReport


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

    SOURCE = "recruiter_csv"

    def extract(self, source_path: str) -> Dict[str, Any]:
        report = NormalizationReport()
        try:
            df = pd.read_csv(source_path)

            if df.empty:
                return {"source": self.SOURCE, "_normalization_report": report.to_list()}

            row = df.iloc[0]
            uncertain_fields: List[str] = []

            raw_phone = self._safe_get(row, "phone")
            phones = []
            if raw_phone:
                normalized_phone, phone_entry = normalize_phone_with_report(
                    raw_phone,
                    source=self.SOURCE,
                    field="phone",
                )
                report.add(phone_entry)
                if normalized_phone:
                    phones.append(normalized_phone)
                else:
                    uncertain_fields.append("phones")

            raw_email = self._safe_get(row, "email")
            emails = []
            if raw_email:
                normalized_email, email_entry = normalize_email_with_report(
                    raw_email,
                    source=self.SOURCE,
                    field="email",
                )
                report.add(email_entry)
                if normalized_email:
                    emails.append(normalized_email)
                else:
                    uncertain_fields.append("emails")

            location = normalize_location(self._safe_get(row, "location"))

            return {
                "full_name": self._safe_get(row, "name"),
                "emails": emails,
                "phones": phones,
                "headline": self._safe_get(row, "title"),
                "current_company": self._safe_get(row, "current_company"),
                "location": location,
                "source": self.SOURCE,
                "_uncertain_fields": uncertain_fields,
                "_normalization_report": report.to_list(),
            }

        except Exception as e:
            print(f"[CSVAdapter] Error reading CSV: {e}")
            return {
                "source": self.SOURCE,
                "_normalization_report": report.to_list(),
            }

    @staticmethod
    def _safe_get(row, column_name):
        try:
            value = row.get(column_name)

            if pd.isna(value):
                return None

            return str(value).strip()

        except Exception:
            return None
