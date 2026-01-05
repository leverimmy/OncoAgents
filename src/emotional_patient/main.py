import asyncio
from src.emotional_patient import EmotionalPatient

async def main() -> None:
    patient = EmotionalPatient(
        user_profile="""{
    "demographics": {
        "name": "Ethan Sterling",
        "gender": "Male",
        "age": "42",
        "occupation": "Investment Partner",
        "income_level": "high",
        "family_status": "Married, 2 children"
    },
    "psychographics": {
        "personality": "Rational, commanding, extremely fastidious",
        "decision_style": "Perfectionist, high-quality conscious consumer: shop carefully, systemically, searches the very best quality in products."
    },
    "dynamic_attributes": {
        "current_lifestyle": "He operates in a high-pressure corporate environment with frequent late-night client dinners featuring rich meals and aged scotch. His schedule allows only five hours of sleep nightly, which he counterbalances with morning cold plunges and performance supplements. Despite meticulous optimization efforts, chronic sleep deprivation affects his cognitive sharpness. He insists on bespoke suits and handcrafted Italian shoes, and his office features imported ergonomic furniture he rarely uses due to back-to-back meetings. On weekends, he attempts carefully planned educational activities with his children, though his wife reminds him to simply be present. His one indulgence is collecting rare single malt whiskies in a temperature-controlled cabinet."
    },
    "id": 0
}""")
    dialogue_history = []
    while True:
        user_input = input("User: ")
        dialogue_history.append({
            "speaker": "doctor",
            "message": user_input,
        })
        response = await patient.respond(dialogue_history)
        dialogue_history.append({
            "speaker": "emotional_patient",
            "message": response["response"]
        })
        print(f"EmotionalPatient Response: {response["response"]}")

if __name__ == "__main__":
    asyncio.run(main())
