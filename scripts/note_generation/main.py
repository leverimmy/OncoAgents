import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import sleep
from typing import Any

from note_generation_prompt import (
    COM_MAP,
    COMMUNICATION_STYLES,
    EDU_MAP,
    EDUCATION_LEVELS,
    FIN_MAP,
    FINANCIAL_STATUSES,
    PATIENT_CASE,
    PER_MAP,
    PERSONALITIES,
    PROMPT_1,
    PROMPT_2,
    PROMPT_3,
    QUESTIONAIRE_INPUT,
    REITERATE_PROMPT,
)
from openai import OpenAI

# Add current directory to path so we can import src
sys.path.append(os.path.abspath("../"))

from src.conversation import Conversation

# Helper Functions
def infer_personality(q5, q6, q7, q8, q9, q10, q11, q12):
    impatient = q5
    anxious = (q6 + q7) / 2
    over_optimistic = (q8 + q9) / 2
    distrustful = ((5 - q10) + q11) / 2
    verbose = q12

    max_score = max(impatient, anxious, over_optimistic, distrustful, verbose)

    if max_score < 4:
        return "neutral"
    else:
        max_personalities = []
        if impatient == max_score:
            max_personalities.append("impatient")
        if anxious == max_score:
            max_personalities.append("anxious")
        if over_optimistic == max_score:
            max_personalities.append("over_optimistic")
        if distrustful == max_score:
            max_personalities.append("distrustful")
        if verbose == max_score:
            max_personalities.append("verbose")
        return random.choice(max_personalities)

def get_persona(raw_text: str) -> tuple[str, str, dict]:
    raw_text = raw_text.strip()

    def extract_score(text, q_num):
        pattern = rf"第{q_num}题：.*?得分(\d+)"
        m = re.search(pattern, text, re.S)
        return int(m.group(1)) if m else None

    q1 = raw_text.split("第1题：")[1].split("\n")[0].strip()
    q2 = raw_text.split("第2题：")[1].split("\n")[0].strip()
    q3 = raw_text.split("第3题：")[1].split("\n")[0].strip()
    q4 = raw_text.split("第4题：")[1].split("\n")[0].strip()
    q5 = extract_score(raw_text, 5)
    q6 = extract_score(raw_text, 6)
    q7 = extract_score(raw_text, 7)
    q8 = extract_score(raw_text, 8)
    q9 = extract_score(raw_text, 9)
    q10 = extract_score(raw_text, 10)
    q11 = extract_score(raw_text, 11)
    q12 = extract_score(raw_text, 12)
    q13 = raw_text.split("第13题：")[1].strip()

    assistant_name = q1
    patient_id = q2
    education_level = EDUCATION_LEVELS[EDU_MAP[q3]]
    financial_status = FINANCIAL_STATUSES[FIN_MAP[q4]]
    personality = PERSONALITIES[PER_MAP[infer_personality(q5, q6, q7, q8, q9, q10, q11, q12)]]
    communication_style = COMMUNICATION_STYLES[COM_MAP[q13]]

    return assistant_name, patient_id, {
        "social_background": {
            "education_level": education_level,
            "financial_status": financial_status,
        },
        "characteristics": {
            "personality": personality,
            "communication_style": communication_style,
        },
    }

client = OpenAI(
    api_key="0",
    base_url="http://localhost:8000/v1",
)
model_name = "Qwen/Qwen3-8B"

def get_llm_output(prompt: str, is_json: bool = True) -> dict:
    cnt = 0
    while True:
        cnt += 1
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            content = response.choices[0].message.content
            if "</think>" in content:
                content = content.split("</think>")[1].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            if is_json:
                return json.loads(content)
            else:
                return content
        except Exception as e:
            print(f"Error during LLM call: {e}")
            if cnt >= 5:
                return {}
            print(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
            sleep(2 ** cnt - 1)
    
def get_examination_data_from_txt(raw_text: str) -> dict:
    prompt = PROMPT_1.format(patient_case_text=raw_text)
    case_data = get_llm_output(prompt)
    return case_data

def get_examination_data_from_img(img_path: str) -> dict:
    prompt = PROMPT_2.format(raw_text=img_path)
    case_data = get_llm_output(prompt)
    return case_data

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
    do_eval_doctor: bool,
    output_dir: str,
    idx: int,
) -> tuple[str, dict]:
    file_name = input_file.name
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        patient_data = {
            "personal_info": data["personal_info"],
            "symptom": data["symptom"],
            "reiterated_symptom": data["reiterated_symptom"],
        }
        examination_data = {
            "symptom": data["symptom"],
            "auxiliary_examination": data["auxiliary_examination"],
            "diagnosis": data["diagnosis"],
            "treatment": data["treatment"],
        }

        conversation = Conversation(
            file_name=f"{idx}_{file_name}",
            patient_data=patient_data,
            examination_data=examination_data,
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
            do_eval_doctor=do_eval_doctor,
        )

        conversation.run_conversation()
        result = conversation.save_conversation(output_dir)
    return f"{idx}_{file_name}", result

def simulate_case(input_file: Path):
    futures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in range(5):
            futures.append(
                executor.submit(
                    run_one_file,
                    input_file=input_file,
                    patient_model_name="o3",
                    strategy_model_name="Qwen/Qwen3-8B-DPO",
                    reply_model_name="gpt-5-chat",
                    mdt_model_name="qwen3-8b",
                    judge_model_name="o3",
                    url="http://localhost:8002/v1",
                    max_turns=15,
                    human_in_the_loop=False,
                    has_expert_knowledge=True,
                    is_emotional_patient=True,
                    is_baseline=False,
                    do_eval_doctor=False,
                    output_dir=input_file.parent / "result",
                    idx=i+1,
                )
            )

        for future in as_completed(futures):
            file_name, result = future.result()
            print(f"Finished processing {file_name}")


def _extract_case_for_note(data: dict[str, Any]) -> dict[str, Any]:
    """只保留生成 note 需要的字段，减少 prompt 冗余。"""
    return {
        "file_name": data.get("file_name"),
        "patient_profile": {
            "demographics": (
                data.get("patient_data", {})
                .get("personal_info", {})
                .get("demographics", {})
            ),
            "social_background": (
                data.get("patient_data", {})
                .get("personal_info", {})
                .get("social_background", {})
            ),
            "characteristics": (
                data.get("patient_data", {})
                .get("personal_info", {})
                .get("characteristics", {})
            ),
            "reiterated_symptom": data.get("patient_data", {}).get("reiterated_symptom"),
        },
        "diagnosis": (
            data.get("examination_data", {})
            .get("diagnosis", {})
        ),
        "treatment": (
            data.get("examination_data", {})
            .get("treatment", {})
        ),
        "conversation_history": data.get("conversation_history", []),
        "patient_scores": (
            data.get("scores", {}).get("patient_scores", [])
        ),
        "completed_turns": data.get("completed_turns"),
        "negotiation_result": data.get("negotiation_result"),
    }


def get_note(input_file: Path) -> str:
    results_dir = input_file.parent / "results"
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    case_files = sorted(results_dir.glob("**/*.json"))
    if not case_files:
        raise FileNotFoundError(f"No JSON files found in: {results_dir}")

    cases_for_prompt = []
    for file in case_files:
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
        cases_for_prompt.append(_extract_case_for_note(data))

    cases_json = json.dumps(cases_for_prompt, ensure_ascii=False, indent=2)
    prompt = PROMPT_3.format(cases_json=cases_json)

    final_note = get_llm_output(prompt)

    return final_note

def render_note(note: dict) -> list[str]:

    return [f"""
## 沟通关键点

-   **实用沟通策略**：{note["keypoints"]["communication_strategy"]}
-   **稳定情绪的方法**：{note["keypoints"]["emotional_stabilization"]}
-   **最重要的雷区**：{note["keypoints"]["red_flag"]}
""".strip(), f"""
## 高概率问题清单

{"\n".join([f"{idx+1}.   [{q['category']}]：“{q['utterance']}”" for idx, q in enumerate(note["likely_questions"])])}
""".strip(), f"""
## 临场可以直接说

{"\n".join([f"-   “{line}”" for line in note["ready_to_use_lines"]])}
""".strip()]

def get_reiterated_symptom(chief_complaint: str, additional_symptom: str, symptom_duration: str, education_level: str) -> str:
    prompt = REITERATE_PROMPT.format(
        chief_complaint=chief_complaint,
        additional_symptom=additional_symptom,
        symptom_duration=symptom_duration,
        education_level=education_level,
    )
    reiterated_symptom = get_llm_output(prompt, is_json=False)
    return reiterated_symptom

# Page Layout
if __name__ == "__main__":
    random.seed(42)

    assistant_name, patient_id, persona = get_persona(QUESTIONAIRE_INPUT)
    print(f"Assistant Name: {assistant_name}, Patient ID: {patient_id}\nPersona: {json.dumps(persona, ensure_ascii=False, indent=2)}")
    patient_case = get_examination_data_from_txt(PATIENT_CASE)
    print(json.dumps(patient_case, ensure_ascii=False, indent=4))
    data = patient_case
    data["personal_info"]["social_background"] = persona["social_background"]
    data["personal_info"]["characteristics"] = persona["characteristics"]
    data["reiterated_symptom"] = get_reiterated_symptom(
        chief_complaint=data["symptom"]["chief_complaint"],
        additional_symptom=data["symptom"]["additional_symptom"],
        symptom_duration=data["symptom"]["symptom_duration"],
        education_level=persona["social_background"]["education_level"],
    )

    file_path_name = Path(f"../../results/notes/{assistant_name}/{patient_id}/case.json")
    file_path_name.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    simulate_case(file_path_name)
    note = get_note(file_path_name)
    with open(Path(f"../../results/notes/{assistant_name}/{patient_id}/note.json"), "w", encoding="utf-8") as f:
        json.dump(note, f, ensure_ascii=False, indent=4)
    rendered_note = render_note(note)
    with open(Path(f"../../results/notes/{assistant_name}/{patient_id}/rendered_note.md"), "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(rendered_note))
    print(render_note(note))
