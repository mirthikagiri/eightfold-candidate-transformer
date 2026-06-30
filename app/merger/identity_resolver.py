import hashlib
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List

from app.normalizers.email import normalize_email
from app.normalizers.phone import normalize_phone


class IdentityResolver:
    """
    Determine whether records from multiple sources belong to the same candidate.
    """

    NAME_MATCH_THRESHOLD = 0.85

    def resolve(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        match_keys: List[str] = []
        scores: List[float] = []

        email_score = self._score_email_match(csv_data, resume_data)
        if email_score > 0:
            match_keys.append("email")
            scores.append(email_score)

        phone_score = self._score_phone_match(csv_data, resume_data)
        if phone_score > 0:
            match_keys.append("phone")
            scores.append(phone_score)

        name_score = self._score_name_match(csv_data, resume_data)
        if name_score >= self.NAME_MATCH_THRESHOLD:
            match_keys.append("name")
            scores.append(name_score)

        if not scores:
            identity_score = 0.0
        elif len(match_keys) >= 2:
            identity_score = min(0.99, max(scores) + 0.05)
        else:
            identity_score = round(max(scores), 2)

        return {
            "identity_score": round(identity_score, 2),
            "match_keys": match_keys,
        }

    def generate_candidate_id(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> str:
        for source in (resume_data, csv_data):
            emails = source.get("emails") or []
            for email in emails:
                normalized = normalize_email(email)
                if normalized:
                    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
                    return f"cand_{digest}"

        name = resume_data.get("full_name") or csv_data.get("full_name") or ""
        phone = ""
        for source in (resume_data, csv_data):
            phones = source.get("phones") or []
            if phones:
                phone = normalize_phone(phones[0]) or phones[0]
                break

        seed = f"{name}|{phone}".strip().lower()
        if seed and seed != "|":
            digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
            return f"cand_{digest}"

        return f"cand_{hashlib.sha256(b'unknown').hexdigest()[:12]}"

    def _score_email_match(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> float:
        csv_emails = {
            normalized
            for email in csv_data.get("emails", [])
            if (normalized := normalize_email(email))
        }
        resume_emails = {
            normalized
            for email in resume_data.get("emails", [])
            if (normalized := normalize_email(email))
        }

        if csv_emails and resume_emails and csv_emails & resume_emails:
            return 0.95
        return 0.0

    def _score_phone_match(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> float:
        csv_phones = self._normalized_phones(csv_data.get("phones", []))
        resume_phones = self._normalized_phones(resume_data.get("phones", []))

        if csv_phones and resume_phones and csv_phones & resume_phones:
            return 0.90

        csv_digits = {self._digits_only(phone) for phone in csv_data.get("phones", [])}
        resume_digits = {
            self._digits_only(phone) for phone in resume_data.get("phones", [])
        }
        csv_digits.discard("")
        resume_digits.discard("")

        if csv_digits and resume_digits and csv_digits & resume_digits:
            return 0.85

        return 0.0

    def _score_name_match(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> float:
        csv_name = self._normalize_name(csv_data.get("full_name"))
        resume_name = self._normalize_name(resume_data.get("full_name"))

        if not csv_name or not resume_name:
            return 0.0

        ratio = SequenceMatcher(None, csv_name, resume_name).ratio()
        return round(ratio, 2)

    def _normalized_phones(self, phones: List[str]) -> set[str]:
        normalized = set()
        for phone in phones:
            value = normalize_phone(phone)
            if value:
                normalized.add(value)
        return normalized

    @staticmethod
    def _normalize_name(name: Any) -> str:
        if not name or not isinstance(name, str):
            return ""
        cleaned = re.sub(r"[^a-zA-Z\s]", "", name.lower())
        return " ".join(cleaned.split())

    @staticmethod
    def _digits_only(value: str) -> str:
        return re.sub(r"\D", "", value or "")
