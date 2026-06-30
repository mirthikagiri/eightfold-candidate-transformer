from typing import Dict, Any

from app.normalizers.skills import normalize_skills


class MergeEngine:
    """
    Merge candidate data from multiple sources into
    a canonical candidate record.
    """

    def merge(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        canonical = {}

        # Name
        canonical["full_name"] = (
            resume_data.get("full_name")
            or csv_data.get("full_name")
        )

        # Headline
        canonical["headline"] = (
            resume_data.get("headline")
            or csv_data.get("headline")
        )

        # Emails
        canonical["emails"] = sorted(
            list(
                set(
                    csv_data.get("emails", [])
                    + resume_data.get("emails", [])
                )
            )
        )

        # Phones
        canonical["phones"] = sorted(
            list(
                set(
                    csv_data.get("phones", [])
                    + resume_data.get("phones", [])
                )
            )
        )

        # Skills
        canonical["skills"] = normalize_skills(
            list(
                set(
                    csv_data.get("skills", [])
                    + resume_data.get("skills", [])
                )
            )
        )

        canonical["source_count"] = 2

        return canonical