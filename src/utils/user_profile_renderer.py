def render_user_profile(patient_data: dict[str, str], role: str = "Patient", with_symptom: bool = True) -> str:
    education_level = patient_data["personal_info"]["social_background"]["education_level"]
    financial_status = patient_data["personal_info"]["social_background"]["financial_status"]
    personality = patient_data["personal_info"]["characteristics"]["personality"]
    communication_style = patient_data["personal_info"]["characteristics"]["communication_style"]
    reiterated_symptom = patient_data["reiterated_symptom"]
    symptom = patient_data["symptom"]

    if with_symptom:
        if role == "Patient":
            return f"""
-   受教育水平：{education_level}
-   经济状况：{financial_status}
-   性格特点：{personality}
-   沟通风格：{communication_style}
-   当前症状：{reiterated_symptom}
""".strip()
        else:
            return f"""
-   受教育水平：{education_level}
-   经济状况：{financial_status}
-   性格特点：{personality}
-   沟通风格：{communication_style}
-   当前症状
    -   主诉：{symptom['chief_complaint']}
    -   附加症状：{symptom['additional_symptom']}
    -   症状持续时间：{symptom['symptom_duration']}
""".strip()
    else:
        return f"""
-   受教育水平：{education_level}
-   经济状况：{financial_status}
-   性格特点：{personality}
-   沟通风格：{communication_style}
""".strip()
