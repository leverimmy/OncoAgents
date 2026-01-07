import argparse
import asyncio
import os
import json
from src.conversation import Conversation


async def main(
    data_dir: str,
    data_id: int,
    patient_model_name: str,
    strategy_model_name: str,
    reply_model_name: str,
    tom_model_name: str,
    max_turns: int,
    has_expert_knowledge: bool,
    human_in_the_loop: bool,
    is_emotional_patient: bool,
    output_dir: str,
):
    with open(os.path.join(data_dir, f"{data_id}.json"), "r", encoding="utf-8") as f:
        case = json.load(f)
        patient_data = {
            "personal_info": case["personal_info"],
            "symptom": case["symptom"],
        }
        diagnosis_data = {
            "symptom": case["symptom"],
            "diagnosis": case["diagnosis"],
            "treatment": case["treatment"],
        }

    conversation = Conversation(
        patient_id=f"{data_id}",
        patient_data=patient_data,
        diagnosis_id=f"{data_id}",
        diagnosis_data=diagnosis_data,
        patient_model_name=patient_model_name,
        strategy_model_name=strategy_model_name,
        reply_model_name=reply_model_name,
        tom_model_name=tom_model_name,
        max_turns=max_turns,
        has_expert_knowledge=has_expert_knowledge,
        human_in_the_loop=human_in_the_loop,
        is_emotional_patient=is_emotional_patient,
    )

    result = await conversation.run_conversation()
    conversation.save_conversation(
        os.path.join(
            output_dir, f"final_conversation{'_human' if human_in_the_loop else ''}"
        )
    )
    print("Final Conversation Result:", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run conversation with patient.")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/patient_cases",
        help="Directory for patient and diagnosis data.",
    )
    parser.add_argument(
        "--id", type=int, default=7, help="Patient and diagnosis ID number."
    )

    parser.add_argument(
        "--patient_model", type=str, default="gpt-4o", help="Patient model name."
    )
    parser.add_argument(
        "--strategy_model", type=str, default="gpt-4o", help="Strategy model name."
    )
    parser.add_argument(
        "--reply_model", type=str, default="gpt-4o", help="Reply model name."
    )
    parser.add_argument(
        "--tom_model", type=str, default="gpt-4o", help="Theory of Mind model name."
    )

    parser.add_argument(
        "--max_turns",
        type=int,
        default=20,
        help="Maximum number of conversation turns.",
    )

    parser.add_argument(
        "--expert_knowledge",
        action="store_true",
        help="Enable expert knowledge in strategy model.",
    )
    parser.add_argument(
        "--human_in_the_loop",
        action="store_true",
        help="Enable human in the loop for replies.",
    )
    parser.add_argument(
        "--is_emotional_patient",
        action="store_true",
        help="Set patient as emotional or not.",
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default="results",
        help="Directory to save conversation results.",
    )

    args = parser.parse_args()
    asyncio.run(
        main(
            data_dir=args.data_dir,
            data_id=args.id,
            patient_model_name=args.patient_model,
            strategy_model_name=args.strategy_model,
            reply_model_name=args.reply_model,
            tom_model_name=args.tom_model,
            max_turns=args.max_turns,
            has_expert_knowledge=args.expert_knowledge,
            human_in_the_loop=args.human_in_the_loop,
            is_emotional_patient=args.is_emotional_patient,
            output_dir=args.output_dir,
        )
    )
