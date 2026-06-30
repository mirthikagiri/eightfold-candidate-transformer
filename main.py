import json

from app.services.pipeline import (
    CandidatePipeline
)


def main():

    result = (
        CandidatePipeline()
        .run(
            csv_path="sample_data/recruiter.csv",
            resume_path="sample_data/resume.pdf",
            config_path="configs/default.json"
        )
    )

    if result["errors"]:

        print("\nValidation Errors:")

        for error in result["errors"]:
            print(error)

        return

    with open(
        "output/profile.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result["projected"],
            f,
            indent=4
        )

    print(
        "Output saved to output/profile.json"
    )


if __name__ == "__main__":
    main()