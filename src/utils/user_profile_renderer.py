import asyncio
from autogen_agentchat.messages import UserMessage

from src.backend.client import get_client


async def reiterate_symptom(symptom: dict[str, str], education_level: str) -> str:
    client = get_client("gpt-4o")
    query = await client.create(
        messages=[
            UserMessage(
                content=f"假设你是患者，请根据以下症状描述，按照患者的受教育水平，复述你的主要症状，确保通俗易懂且符合你的认知水平。\n\n症状描述: {symptom}\n受教育水平: {education_level}",
                source="User",
            )
        ],
    )
    
    return query.content

def render_user_profile(patient_data: dict[str, str]) -> str:
    education_level = patient_data["personal_info"]["social_background"]["education_level"]
    financial_status = patient_data["personal_info"]["social_background"]["financial_status"]
    personality = patient_data["personal_info"]["characteristics"]["personality"]
    communication_style = patient_data["personal_info"]["characteristics"]["communication_style"]
    symptom = patient_data["symptom"]

    return f"""
-   受教育水平：{education_level}
-   经济状况：{financial_status}
-   性格特点：{personality}
-   沟通风格：{communication_style}
-   当前症状：{asyncio.run(reiterate_symptom(symptom, education_level))}
""".strip()
