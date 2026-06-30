class ConfidenceScorer:

    SOURCE_WEIGHTS = {
        "resume_pdf": 0.90,
        "recruiter_csv": 0.80
    }

    def score_field(
        self,
        field_name,
        csv_data,
        resume_data
    ):

        csv_exists = bool(
            csv_data.get(field_name)
        )

        resume_exists = bool(
            resume_data.get(field_name)
        )

        if csv_exists and resume_exists:

            return 0.95

        if resume_exists:

            return 0.90

        if csv_exists:

            return 0.80

        return 0.0

    def score_profile(
        self,
        canonical,
        csv_data,
        resume_data
    ):

        scores = {}

        for field in canonical:

            scores[field] = self.score_field(
                field,
                csv_data,
                resume_data
            )

        overall = (
            sum(scores.values())
            / len(scores)
            if scores
            else 0
        )

        return scores, round(overall, 2)