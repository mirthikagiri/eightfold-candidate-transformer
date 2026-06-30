import fitz
import re
from typing import Dict, Any

from app.adapters.base import BaseAdapter


class ResumeAdapter(BaseAdapter):
    """
    Extract candidate information from resume PDF.
    """

    EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    PHONE_PATTERN = r"(?:\+91[- ]?)?[6-9]\d{9}"

    def extract(self, source_path: str) -> Dict[str, Any]:
        try:
            text = self._extract_text(source_path)
            print("\n+===resume text===+\n", text)

            emails = self._extract_emails(text)
            phones = self._extract_phones(text)
            name = self._extract_name(text)
            skills = self._extract_skills(text)

            return {
                "full_name": name,
                "emails": emails,
                "phones": phones,
                "skills": skills,
                "source": "resume_pdf"
            }

        except Exception as e:
            print(f"[ResumeAdapter] Error: {e}")
            return {}

    def _extract_text(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)

        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()

        return text

    def _extract_emails(self, text: str):
        emails = re.findall(self.EMAIL_PATTERN, text)

        return list(set(email.strip() for email in emails))

    def _extract_phones(self, text: str):
        phones = re.findall(self.PHONE_PATTERN, text)

        return list(set(phone.strip() for phone in phones))

    def _extract_name(self, text: str):
        """
        Simple heuristic:
        Assume first non-empty line is candidate name.
        """
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if len(line) > 2:
                return line

        return None

    def _extract_skills(self, text: str):
        """
        Simple keyword extraction.
        We'll improve later.
        """

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
            "linux"
        }

        text_lower = text.lower()

        found = []

        for skill in skill_keywords:
            if skill in text_lower:
                found.append(skill)

        return sorted(list(set(found)))