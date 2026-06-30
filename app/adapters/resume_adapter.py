import re
from typing import Any, Dict, List, Optional

import fitz

from app.adapters.base import BaseAdapter
from app.normalizers.email import normalize_email
from app.normalizers.location import normalize_location
from app.normalizers.phone import normalize_phone


class ResumeAdapter(BaseAdapter):
    """
    Extract candidate information from resume PDF.
    """

    EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    PHONE_PATTERN = r"(?:\+91[- ]?)?[6-9]\d{9}"
    LINK_PATTERN = r"https?://[^\s)>]+"
    LOCATION_PATTERN = r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?),\s*(India|IN|USA|US|UK)\b"
    YEARS_PATTERN = r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience"
    EDUCATION_MARKERS = (
        "institute",
        "university",
        "college",
        "b.e",
        "b.tech",
        "m.e",
        "m.tech",
        "bachelor",
        "master",
        "education",
    )

    def extract(self, source_path: str) -> Dict[str, Any]:
        try:
            text = self._extract_text(source_path)
            if not text.strip():
                return {"source": "resume_pdf", "_uncertain_fields": ["full_name"]}

            uncertain_fields: List[str] = []

            emails = self._extract_emails(text)
            phones = self._extract_phones(text, uncertain_fields)
            name = self._extract_name(text)
            if not name:
                uncertain_fields.append("full_name")

            skills = self._extract_skills(text)
            links = self._extract_links(text)
            location = self._extract_location(text)
            years_experience = self._extract_years_experience(text)
            experience = self._extract_experience(text)
            education = self._extract_education(text)
            headline = self._extract_headline(text)

            return {
                "full_name": name,
                "emails": emails,
                "phones": phones,
                "skills": skills,
                "links": links,
                "location": location,
                "years_experience": years_experience,
                "experience": experience,
                "education": education,
                "headline": headline,
                "source": "resume_pdf",
                "_uncertain_fields": sorted(set(uncertain_fields)),
            }

        except Exception as e:
            print(f"[ResumeAdapter] Error: {e}")
            return {"source": "resume_pdf", "_uncertain_fields": ["full_name"]}

    def _extract_text(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _extract_emails(self, text: str) -> List[str]:
        emails = re.findall(self.EMAIL_PATTERN, text)
        normalized = []
        for email in emails:
            value = normalize_email(email)
            if value:
                normalized.append(value)
        return sorted(set(normalized))

    def _extract_phones(
        self,
        text: str,
        uncertain_fields: List[str],
    ) -> List[str]:
        phones = re.findall(self.PHONE_PATTERN, text)
        normalized = []
        for phone in phones:
            value = normalize_phone(phone.strip())
            if value:
                normalized.append(value)
            else:
                uncertain_fields.append("phones")
        return sorted(set(normalized))

    def _extract_name(self, text: str) -> Optional[str]:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 2 and not line.lower().startswith(
                ("email", "phone", "skills", "experience", "education")
            ):
                return line
        return None

    def _extract_headline(self, text: str) -> Optional[str]:
        for line in text.split("\n"):
            cleaned = line.strip()
            if not cleaned or len(cleaned) > 80:
                continue

            lower = cleaned.lower()
            if any(marker in lower for marker in self.EDUCATION_MARKERS):
                continue

            if any(
                token in lower
                for token in (
                    "engineer",
                    "developer",
                    "intern",
                    "architect",
                    "manager",
                    "analyst",
                    "consultant",
                )
            ):
                return cleaned
        return None

    def _extract_skills(self, text: str) -> List[str]:
        skill_keywords = {
            "python",
            "java",
            "c++",
            "c",
            "javascript",
            "react",
            "nodejs",
            "express",
            "mongodb",
            "mysql",
            "postgresql",
            "html",
            "css",
            "fastapi",
            "flask",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "git",
            "linux",
        }

        text_lower = text.lower()
        found = []
        for skill in skill_keywords:
            if skill in text_lower:
                found.append(skill)
        return sorted(set(found))

    def _extract_links(self, text: str) -> List[str]:
        links = re.findall(self.LINK_PATTERN, text)
        return sorted(set(link.rstrip(".,)") for link in links))

    def _extract_location(self, text: str) -> Optional[Dict[str, Optional[str]]]:
        match = re.search(self.LOCATION_PATTERN, text)
        if not match:
            return None
        city = match.group(1).strip()
        if "\n" in city or len(city) > 40:
            return None
        return normalize_location(f"{city}, {match.group(2).strip()}")

    def _extract_years_experience(self, text: str) -> Optional[float]:
        match = re.search(self.YEARS_PATTERN, text, re.IGNORECASE)
        if not match:
            return None
        return float(match.group(1))

    def _extract_experience(self, text: str) -> List[dict]:
        entries = []
        section = self._extract_section(text, "experience")
        if not section:
            return entries

        for block in re.split(r"\n\s*\n", section):
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines:
                continue
            entry = {"title": lines[0]}
            if len(lines) > 1:
                entry["organization"] = lines[1]
            entries.append(entry)
        return entries

    def _extract_education(self, text: str) -> List[dict]:
        entries = []
        section = self._extract_section(text, "education")
        if not section:
            return entries

        for block in re.split(r"\n\s*\n", section):
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines:
                continue
            entry = {"institution": lines[0]}
            if len(lines) > 1:
                entry["degree"] = lines[1]
            entries.append(entry)
        return entries

    @staticmethod
    def _extract_section(text: str, section_name: str) -> str:
        pattern = rf"{section_name}\s*:?\s*(.*?)(?:\n[A-Z][a-z]+\s*:|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()
