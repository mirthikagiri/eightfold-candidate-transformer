SKILL_MAP = {
    "py": "python",
    "python3": "python",
    "python programming": "python",

    "js": "javascript",
    "node": "nodejs",

    "reactjs": "react",
    "react.js": "react",

    "postgres": "postgresql",

    "mongo": "mongodb"
}


def normalize_skill(skill: str | None) -> str | None:

    if not skill:
        return None

    skill = skill.strip().lower()

    return SKILL_MAP.get(skill, skill)


def normalize_skills(skills: list[str]) -> list[str]:

    normalized = []

    for skill in skills:
        value = normalize_skill(skill)

        if value:
            normalized.append(value)

    return sorted(list(set(normalized)))