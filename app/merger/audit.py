class AuditTrail:

    def generate(
        self,
        canonical,
        csv_data,
        resume_data
    ):

        audit = {}

        for field in canonical:

            audit[field] = {
                "selected_source": (
                    "resume_pdf"
                    if resume_data.get(field)
                    else "recruiter_csv"
                ),
                "resolution_policy":
                    "resume_priority"
            }

        return audit