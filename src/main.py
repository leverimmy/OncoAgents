import argparse
import asyncio
import json
import os

from src.conversation import Conversation


async def main(
    data_dir: str,
    patient_id: int,
    diagnosis_id: int,
    patient_model_name: str,
    strategy_model_name: str,
    reply_model_name: str,
    tom_model_name: str,
    mdt_model_name: str,
    max_turns: int,
    has_expert_knowledge: bool,
    human_in_the_loop: bool,
    is_emotional_patient: bool,
    output_dir: str,
):
    # 合成患者画像
    full_data = {}
    with open(os.path.join(data_dir, "background", f"{patient_id}.json"), encoding="utf-8") as f:
        full_data = json.load(f)
    with open(os.path.join(data_dir, "diagnosis", f"{diagnosis_id}.json"), encoding="utf-8") as f:
        diagnosis_data = json.load(f)
        for k, v in diagnosis_data.items():
            if k in full_data and isinstance(full_data[k], dict):
                full_data[k].update(v)
            else:
                full_data[k] = v
    
    patient_data = {
        "personal_info": full_data["personal_info"],
        "symptom": full_data["symptom"],
    }
    examination_data = {
        "physical_examination": full_data.get("physical_examination", ""),
        "auxiliary_examination": full_data.get("auxiliary_examination", ""),
    }

    conversation = Conversation(
        patient_id=patient_id,
        patient_data=patient_data,
        diagnosis_id=diagnosis_id,
        diagnosis_data=diagnosis_data,
        examination_data=examination_data,
        patient_model_name=patient_model_name,
        strategy_model_name=strategy_model_name,
        reply_model_name=reply_model_name,
        tom_model_name=tom_model_name,
        mdt_model_name=mdt_model_name,
        max_turns=max_turns,
        has_expert_knowledge=has_expert_knowledge,
        human_in_the_loop=human_in_the_loop,
        is_emotional_patient=is_emotional_patient,
    )

    result = await conversation.run_conversation()
    conversation.save_conversation(
        os.path.join(
            output_dir, f"final_conversation{'_human' if human_in_the_loop else ''}{'' if has_expert_knowledge else '_no_knowledge'}"
        )
    )
    print("Final Conversation Result:", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run conversation with patient.")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/",
        help="Directory for patient and diagnosis data.",
    )
    parser.add_argument(
        "--characteristic_id", type=int, default=1, help="Characteristic ID number."
    )
    parser.add_argument(
        "--diagnosis_id", type=int, default=1, help="Diagnosis ID number."
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
        "--mdt_model", type=str, default="gpt-4o", help="MDT agent model name."
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
            patient_id=args.characteristic_id,
            diagnosis_id=args.diagnosis_id,
            patient_model_name=args.patient_model,
            strategy_model_name=args.strategy_model,
            reply_model_name=args.reply_model,
            tom_model_name=args.tom_model,
            mdt_model_name=args.mdt_model,
            max_turns=args.max_turns,
            has_expert_knowledge=args.expert_knowledge,
            human_in_the_loop=args.human_in_the_loop,
            is_emotional_patient=args.is_emotional_patient,
            output_dir=args.output_dir,
        )
    )
