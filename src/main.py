import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

from src.conversation import Conversation


def run_one_file(
    input_file: Path,
    patient_model_name: str,
    strategy_model_name: str,
    reply_model_name: str,
    mdt_model_name: str,
    judge_model_name: str,
    url: str | None,
    max_turns: int,
    human_in_the_loop: bool,
    has_expert_knowledge: bool,
    is_emotional_patient: bool,
    is_baseline: bool,
    do_eval_patient: bool,
    do_eval_doctor: bool,
    output_dir: str,
) -> str:
    file_name = input_file.name
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)
        patient_data = {
            "personal_info": data["personal_info"],
            "symptom": data["symptom"],
            "reiterated_symptom": data["reiterated_symptom"],
        }
        diagnosis_data = {
            "personal_info": data["personal_info"],
            "symptom": data["symptom"],
            "physical_examination": data["physical_examination"],
            "auxiliary_examination": data["auxiliary_examination"],
            "diagnosis": data["diagnosis"],
            "treatment": data["treatment"],
        }

        conversation = Conversation(
            file_name=file_name,
            patient_data=patient_data,
            diagnosis_data=diagnosis_data,
            patient_model_name=patient_model_name,
            strategy_model_name=strategy_model_name,
            reply_model_name=reply_model_name,
            mdt_model_name=mdt_model_name,
            judge_model_name=judge_model_name,
            url=url,
            max_turns=max_turns,
            human_in_the_loop=human_in_the_loop,
            has_expert_knowledge=has_expert_knowledge,
            is_emotional_patient=is_emotional_patient,
            is_baseline=is_baseline,
            do_eval_patient=do_eval_patient,
            do_eval_doctor=do_eval_doctor,
        )

        conversation.run_conversation()
        conversation.save_conversation(output_dir)
    return file_name

def main(
    input_dir: str,
    patient_model_name: str,
    strategy_model_name: str,
    reply_model_name: str,
    mdt_model_name: str,
    judge_model_name: str,
    url: str | None,
    max_turns: int,
    human_in_the_loop: bool,
    has_expert_knowledge: bool,
    is_emotional_patient: bool,
    is_baseline: bool,
    do_eval_patient: bool,
    do_eval_doctor: bool,
    output_dir: str,
    max_workers: int,
):
    input_dir = Path(input_dir)
    input_files = sorted(input_dir.glob("*.json"))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(
                run_one_file,
                f,
                patient_model_name=patient_model_name,
                strategy_model_name=strategy_model_name,
                reply_model_name=reply_model_name,
                mdt_model_name=mdt_model_name,
                judge_model_name=judge_model_name,
                url=url,
                max_turns=max_turns,
                human_in_the_loop=human_in_the_loop,
                has_expert_knowledge=has_expert_knowledge,
                is_emotional_patient=is_emotional_patient,
                is_baseline=is_baseline,
                do_eval_patient=do_eval_patient,
                do_eval_doctor=do_eval_doctor,
                output_dir=output_dir,
            ): f
            for f in input_files
        }

        ok = 0
        fail = 0

        for fut in tqdm(as_completed(futures), total=len(futures), desc="Conversations"):
            input_file = futures[fut]
            try:
                file_name = fut.result()
                ok += 1
                # print(f"[OK] {file_name}: {result}")
            except Exception as e:
                fail += 1
                print(f"[FAIL] {input_file.name}: {repr(e)}")

        print(f"[DONE] total={len(input_files)} ok={ok} fail={fail}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run conversation with patient.")
    parser.add_argument(
        "--input_dir",
        type=str,
        help="Directory for patient and diagnosis data.",
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
        "--mdt_model", type=str, default="gpt-4o", help="MDT agent model name."
    )
    parser.add_argument(
        "--judge_model", type=str, default="gpt-4o", help="Judge model name."
    )
    parser.add_argument(
        "--url", type=str, default="", help="URL for API calls.",
    )

    parser.add_argument(
        "--max_turns",
        type=int,
        default=20,
        help="Maximum number of conversation turns.",
    )
    parser.add_argument(
        "--human_in_the_loop",
        action="store_true",
        help="Enable human in the loop for replies.",
    )
    parser.add_argument(
        "--expert_knowledge",
        action="store_true",
        help="Enable expert knowledge in strategy model.",
    )
    parser.add_argument(
        "--is_emotional_patient",
        action="store_true",
        help="Set patient as emotional or not.",
    )
    parser.add_argument(
        "--is_baseline", action="store_true", help="Whether to use baseline doctor reply prompt."
    )
    parser.add_argument(
        "--do_eval_patient", action="store_true", help="Whether to do patient evaluation."
    )
    parser.add_argument(
        "--do_eval_doctor", action="store_true", help="Whether to do doctor evaluation."
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory to save conversation results.",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="Maximum number of worker threads for concurrent conversation runs.",
    )

    args = parser.parse_args()
    main(
        input_dir=args.input_dir,
        patient_model_name=args.patient_model,
        strategy_model_name=args.strategy_model,
        reply_model_name=args.reply_model,
        mdt_model_name=args.mdt_model,
        judge_model_name=args.judge_model,
        url=args.url if len(args.url) > 0 else None,
        max_turns=args.max_turns,
        human_in_the_loop=args.human_in_the_loop,
        has_expert_knowledge=args.expert_knowledge,
        is_emotional_patient=args.is_emotional_patient,
        is_baseline=args.is_baseline,
        do_eval_patient=args.do_eval_patient,
        do_eval_doctor=args.do_eval_doctor,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
    )
