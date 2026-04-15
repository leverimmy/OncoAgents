import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath("../../"))

from src.prompt import DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE
from src.utils import SafeDict, render_diagnosis_data, render_user_profile


def render_output(turn: dict):
    keywords = [
        item.get("query", "") for item in turn.get("message", {}).get("explanation", [])
    ]
    return f"""
{{
    "analysis": "{turn.get("message", {}).get("analysis", "")}",
    "stage": "{turn.get("message", {}).get("stage", "")}",
    "strategy": "{turn.get("message", {}).get("strategy", "")}",
    "keywords": {keywords}
}}
""".strip()

def get_dialogue_history(conversation_history: list[dict[str, str]], current_index: int):
    dialogue_history = []
    for i in range(current_index):
        turn = conversation_history[i]
        dialogue_history.append(
            {"speaker": turn["speaker"], "message": turn["message"]["response"]}
        )
    return json.dumps(dialogue_history, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Select dataset for SFT process.')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing the raw dataset.')
    parser.add_argument('--output_file', type=str, required=True, help='File to save the processed dataset.')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for file in input_dir.glob('*.json'):
        with open(file, encoding='utf-8') as f:
            data = json.load(f)
        conversation_history = data.get("conversation_history", [])

        for i, turn in enumerate(conversation_history):

            flag = True
            if i - 1 < 0 or i + 1 >= len(conversation_history):
                flag = False

            # 筛选 PAS Score 有提升的 Doctor 回合
            if flag and conversation_history[i - 1].get("speaker") == "Patient" \
                and conversation_history[i].get("speaker") == "Doctor" \
                and conversation_history[i + 1].get("speaker") == "Patient":
                last_score = conversation_history[i - 1].get("message", {}).get("pas_score")
                next_score = conversation_history[i + 1].get("message", {}).get("pas_score")
                if next_score < last_score:
                    flag = False

            # 筛选 stage 判断正确的回合
            if flag and conversation_history[i - 1].get("speaker") == "Patient" \
                and conversation_history[i].get("speaker") == "Doctor":
                last_stage = conversation_history[i - 1].get("message", {}).get("stage")
                current_stage = conversation_history[i].get("message", {}).get("stage")
                if last_stage != current_stage:
                    flag = False

            if flag and turn.get("speaker") == "Doctor":
                format_args = SafeDict(
                    user_profile=render_user_profile(data.get("patient_data", {}), "Doctor"),
                    diagnosis_data=render_diagnosis_data(data.get("examination_data", {}), with_exams=True),
                    dialogue_history=get_dialogue_history(conversation_history, i)
                )
                result = {
                    "instruction": DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE.format_map(format_args),
                    "input": "",
                    "output": render_output(turn),
                }
                results.append(result)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
