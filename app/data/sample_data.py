from __future__ import annotations

import random


def generate_employee_data(rows: int = 250, seed: int | None = None) -> list[dict[str, object]]:
    rng = random.Random(seed)

    departments = ["Sales", "R&D", "HR"]
    education_fields = [
        "Life Sciences",
        "Medical",
        "Marketing",
        "Technical Degree",
        "Human Resources",
        "Other",
    ]
    job_roles = [
        "Sales Executive",
        "Sales Representative",
        "Research Scientist",
        "Laboratory Technician",
        "Manufacturing Director",
        "Manager",
        "Research Director",
        "Human Resources",
        "Healthcare Representative",
    ]
    genders = ["Male", "Female"]

    records: list[dict[str, object]] = []
    for index in range(rows):
        age = rng.randint(18, 60)
        satisfaction = rng.randint(1, 4)
        department = rng.choices(departments, weights=[0.40, 0.52, 0.08], k=1)[0]

        # Slightly higher attrition if younger and lower satisfaction.
        base = 0.12
        if age < 30:
            base += 0.05
        if satisfaction <= 2:
            base += 0.07
        if department == "Sales":
            base += 0.03

        attrition = "Yes" if rng.random() < min(base, 0.65) else "No"

        records.append(
            {
                "EmployeeID": f"EMP-{1000 + index}",
                "Age": age,
                "Department": department,
                "EducationField": rng.choice(education_fields),
                "Gender": rng.choice(genders),
                "JobRole": rng.choice(job_roles),
                "JobSatisfaction": satisfaction,
                "Attrition": attrition,
            }
        )

    return records

