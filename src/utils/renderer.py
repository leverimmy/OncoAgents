def render_user_profile(patient_data: dict[str, str], role: str = "Patient", with_symptoms: bool = True) -> str:
    education_level = patient_data["personal_info"]["social_background"]["education_level"]
    financial_status = patient_data["personal_info"]["social_background"]["financial_status"]
    personality = patient_data["personal_info"]["characteristics"]["personality"]
    communication_style = patient_data["personal_info"]["characteristics"]["communication_style"]
    reiterated_symptom = patient_data["reiterated_symptom"]
    symptom = patient_data["symptom"]

    if with_symptoms:
        if role == "Patient":
            return f"""
-   **受教育水平**：{education_level}
-   **经济状况**：{financial_status}
-   **性格特点**：{personality}
-   **沟通风格**：{communication_style}
-   **当前症状**：{reiterated_symptom}
""".strip()
        else:
            return f"""
-   **受教育水平**：{education_level}
-   **经济状况**：{financial_status}
-   **性格特点**：{personality}
-   **沟通风格**：{communication_style}
-   **当前症状**
    -   **主诉**：{symptom['chief_complaint']}
    -   **附加症状**：{symptom['additional_symptom']}
    -   **症状持续时间**：{symptom['symptom_duration']}
""".strip()
    else:
        return f"""
-   **受教育水平**：{education_level}
-   **经济状况**：{financial_status}
-   **性格特点**：{personality}
-   **沟通风格**：{communication_style}
""".strip()

def render_diagnosis_data(examination_data: dict[str, str], with_exams: bool = False) -> str:
    disease_name = examination_data["diagnosis"]["disease_name"]
    stage = examination_data["diagnosis"]["stage"]
    plan = examination_data["treatment"]["plan"]
    course = examination_data["treatment"]["course"]
    auxiliary_examination = examination_data["auxiliary_examination"]

    result = f"""
-   **疾病名称**：{disease_name}
-   **分期**：{stage}
-   **推荐治疗方案**：{plan}
""".strip()
    
    if len(course) > 0:
        result += f"\n-   **治疗周期**：{course}"
    if with_exams and len(auxiliary_examination) > 0:
        result += "\n-   **辅助检查结果**："
        for aux in auxiliary_examination:
            result += f"\n    -   **{aux['check_type']}-{aux['item']}**"
            result += f"\n        -   **检查结果**：{aux['result']}"
    return result

def render_personal_info(patient_data: dict[str, str]) -> str:
    name = patient_data.get("personal_info", {}).get("demographics", {}).get("name", "未知")
    age = patient_data.get("personal_info", {}).get("demographics", {}).get("age", "未知")
    gender = patient_data.get("personal_info", {}).get("demographics", {}).get("gender", "未知")
    smoking_status = patient_data.get("personal_info", {}).get("personal_history", {}).get("smoking_status", "未知")
    alcohol_use = patient_data.get("personal_info", {}).get("personal_history", {}).get("alcohol_use", "未知")
    family_history = patient_data.get("personal_info", {}).get("personal_history", {}).get("family_history", "未知")
    marriage_childbearing_history = patient_data.get("personal_info", {}).get("personal_history", {}).get("marriage_childbearing_history", "未知")

    symptom = patient_data.get("symptom", {})
    return f"""
-   **姓名**：{name}
-   **年龄**：{age}
-   **性别**：{gender}
-   **吸烟史**：{smoking_status}
-   **饮酒史**：{alcohol_use}
-   **家族史**：{family_history}
-   **婚育史**：{marriage_childbearing_history}
-   **当前症状**
    -   **主诉**：{symptom['chief_complaint']}
    -   **附加症状**：{symptom['additional_symptom']}
    -   **症状持续时间**：{symptom['symptom_duration']}
""".strip()
