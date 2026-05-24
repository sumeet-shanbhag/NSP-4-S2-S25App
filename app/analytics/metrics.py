from __future__ import annotations

AGE_LABELS = ["Under 25", "25-34", "35-44", "45-54", "Over 55"]


def _age_group(age: int) -> str:
    if age < 25:
        return "Under 25"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    return "Over 55"


def build_kpis(rows: list[dict[str, object]]) -> dict[str, float]:
    employees = len(rows)
    attrition_count = sum(1 for row in rows if row["Attrition"] == "Yes")
    active_employees = employees - attrition_count
    attrition_rate = (attrition_count / employees * 100) if employees else 0
    avg_age = (sum(int(row["Age"]) for row in rows) / employees) if employees else 0

    return {
        "Employee Count": employees,
        "Attrition Count": attrition_count,
        "Attrition Rate": round(attrition_rate, 2),
        "Active Employees": active_employees,
        "Avg. Age": round(avg_age, 1),
    }


def department_attrition(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["Attrition"] != "Yes":
            continue
        key = str(row["Department"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {"Department": name, "Count": count}
        for name, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    ]


def attrition_by_age_group(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = {label: 0 for label in AGE_LABELS}
    for row in rows:
        if row["Attrition"] != "Yes":
            continue
        counts[_age_group(int(row["Age"]))] += 1
    return [{"AgeGroup": label, "Count": counts[label]} for label in AGE_LABELS]


def education_attrition(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["Attrition"] != "Yes":
            continue
        key = str(row["EducationField"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {"EducationField": name, "Count": count}
        for name, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    ]


def gender_attrition(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["Attrition"] != "Yes":
            continue
        key = str(row["Gender"])
        counts[key] = counts.get(key, 0) + 1
    return [{"Gender": name, "Count": count} for name, count in counts.items()]


def job_satisfaction_table(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    role_counts: dict[str, dict[int, int]] = {}
    for row in rows:
        role = str(row["JobRole"])
        level = int(row["JobSatisfaction"])
        if role not in role_counts:
            role_counts[role] = {1: 0, 2: 0, 3: 0, 4: 0}
        role_counts[role][level] += 1

    table: list[dict[str, object]] = []
    total = {1: 0, 2: 0, 3: 0, 4: 0}
    for role in sorted(role_counts.keys()):
        row = {"JobRole": role}
        grand_total = 0
        for level in [1, 2, 3, 4]:
            value = role_counts[role][level]
            row[str(level)] = value
            total[level] += value
            grand_total += value
        row["Grand Total"] = grand_total
        table.append(row)

    table.append(
        {
            "JobRole": "Grand Total",
            "1": total[1],
            "2": total[2],
            "3": total[3],
            "4": total[4],
            "Grand Total": sum(total.values()),
        }
    )
    return table

