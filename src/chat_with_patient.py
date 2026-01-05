import asyncio
from src.emotional_patient import EmotionalPatient
from src.conversation import Conversation


async def main():
    emotional_patient = EmotionalPatient(
        user_profile="""
        {
            "personal_info": {
                "name": "张先生",
                "age": 55,
                "gender": "男",
                "occupation": "退休工人",
                "personality": "遇到挫折时会感到担忧，在交流中喜欢提出很多问题，文化程度不高",
                "lifestyle_habits": {
                    "smoking_status": "长期吸烟（每天20支烟、30年以上）",
                    "alcohol_use": "偶尔饮酒",
                    "physical_activity": "较少运动，喜欢看电视休闲",
                    "diet": "饮食以油腻、肉类为主，蔬菜摄入相对较少"
                }
            },
            "symptom": {
                "chief_complaint": "长期咳嗽约一年，经常伴有少量血痰",
                "additional_symptoms": ["胸闷", "疲乏无力"],
                "symptom_duration": "1年"
            }
        }
        """.strip()
    )

    conversation = Conversation(
        patient_id="007",
        patient_data=emotional_patient,
        diagnosis_id="007",
        diagnosis_data={
            "symptom": {
                "chief_complaint": "长期咳嗽约一年，经常伴有少量血痰",
                "additional_symptoms": ["胸闷", "疲乏无力"],
                "symptom_duration": "1年"
            },
            "diagnosis": "非小细胞肺癌，临床分期 T2N1M0",
            "treatment": {
                "initial_plan": [
                    "外科手术切除左肺病灶",
                    "术后辅助化疗"
                ],
                "follow_up_plan": [
                    "每3个月复查胸部CT和肿瘤标志物",
                    "如有复发可能考虑靶向治疗或免疫治疗"
                ]
            }
        },
        patient_model_name="gpt-4o",
        strategy_model_name="gpt-4o",
        reply_model_name="gpt-4o",
        tom_model_name="gpt-4o",
        max_turns=20,
        human_in_the_loop=True,
        has_expert_knowledge=False,
    )
    result = await conversation.run_conversation()
    conversation.save_conversation("final_conversation_human")


if __name__ == '__main__':
    asyncio.run(main())
