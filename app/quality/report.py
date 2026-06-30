class QualityReport:

    def generate(
        self,
        canonical,
        confidence_scores
    ):

        missing_fields = []

        important_fields = [
            "full_name",
            "emails",
            "skills"
        ]

        for field in important_fields:

            value = canonical.get(field)

            if not value:
                missing_fields.append(field)

        score = max(
            0,
            100 - (len(missing_fields) * 10)
        )

        return {
            "quality_score": score,
            "missing_fields": missing_fields,
            "source_count": canonical.get(
                "source_count",
                0
            )
        }