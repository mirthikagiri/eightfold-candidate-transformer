class ProvenanceTracker:

    def build(
        self,
        csv_data,
        resume_data,
        canonical
    ):

        provenance = {}

        for field in canonical.keys():

            if field in resume_data and resume_data.get(field):

                provenance[field] = {
                    "source": "resume_pdf",
                    "method": "extraction"
                }

            elif field in csv_data and csv_data.get(field):

                provenance[field] = {
                    "source": "recruiter_csv",
                    "method": "structured_import"
                }

        return provenance