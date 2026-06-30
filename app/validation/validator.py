from app.projection.models import ProjectionPlan


class ProjectionValidator:

    def validate(
        self,
        output,
        plan: ProjectionPlan
    ):

        errors = []

        for field in plan.fields:

            if field.required:

                value = output.get(
                    field.path
                )

                if value is None:

                    errors.append(
                        f"{field.path} is required"
                    )

        return errors