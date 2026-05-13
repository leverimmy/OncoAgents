import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import sleep

from dotenv import load_dotenv
from openai import OpenAI
from revise_prompt import INDEX_HUMANITY_PROMPT, INDEX_SAFETY_PROMPT, REVISE_PROMPT
from tqdm import tqdm

sys.path.append(os.path.abspath("../../"))

from src.prompt import DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE
from src.utils import SafeDict, render_diagnosis_data, render_user_profile

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)
model_name = "o3"

def get_llm_output(prompt: str) -> dict:
    cnt = 0
    while True:
        try:
            cnt += 1
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=4096,
            )
            content = response.choices[0].message.content.strip()
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            return json.loads(content)
        except Exception as e:
            print(f"请求失败，正在重试... 错误信息: {e}")
            if cnt >= 5:
                print("重试次数过多，返回空结果")
                return {}
            else:
                sleep(2 ** cnt - 1)

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

def get_dialogue_history_with_index(conversation_history: list[dict[str, str]], with_index: bool, current_index: int = -1):
    if with_index:
        dialogue_history = []
        if current_index == -1:
            current_index = len(conversation_history) - 1
        for i in range(current_index + 1):
            turn = conversation_history[i]
            if turn["speaker"] == "Doctor":
                dialogue_history.append({
                    "index": i,
                    "speaker": turn["speaker"],
                    "message": {
                        "analysis": turn.get("message", {}).get("analysis", ""),
                        "stage": turn.get("message", {}).get("stage", ""),
                        "strategy": turn.get("message", {}).get("strategy", ""),
                        "keywords": [
                            item.get("query", "") for item in turn.get("message", {}).get("explanation", [])
                        ],
                        "response": turn.get("message", {}).get("response", ""),
                    }
                })
            else:
                dialogue_history.append({
                    "index": i,
                    "speaker": turn["speaker"],
                    "message": {
                        "stage": turn.get("message", {}).get("stage", ""),
                        "analysis": turn.get("message", {}).get("analysis", ""),
                        "response": turn.get("message", {}).get("response", ""),
                    }
                })
        return json.dumps(dialogue_history, ensure_ascii=False)
    else:
        dialogue_history = []
        for i in range(current_index + 1):
            turn = conversation_history[i]
            dialogue_history.append(
                {"speaker": turn["speaker"], "message": turn["message"]["response"]}
            )
        return json.dumps(dialogue_history, ensure_ascii=False)


TRANSLATION = {
    "medical_factual_errors": "医学事实错误",
    "inappropriate_assurance_overconfidence": "不当保证/过度确定",
    "risk_concealment": "风险隐瞒",
    "evidence_support_consistency": "证据支撑一致度",

    "information_comprehensibility": "信息可理解性",
    "response_quality": "回应质量",
    "respect_nonjudgment": "尊重与非评判",
    "autonomy_support": "自主性支持",
}

def get_indices_from_judge(data: dict) -> list[dict]:
    format_args = SafeDict(
        user_profile=render_user_profile(data.get("patient_data", {}), "Doctor"),
        diagnosis_data=render_diagnosis_data(data.get("examination_data", {}), with_exams=True),
        dialogue_history=get_dialogue_history_with_index(data.get("conversation_history", []), with_index=True),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        safety_future = executor.submit(get_llm_output, INDEX_SAFETY_PROMPT.format_map(format_args))
        humanity_future = executor.submit(get_llm_output, INDEX_HUMANITY_PROMPT.format_map(format_args))
    
    indices2reasons = {}
    for future in as_completed([safety_future, humanity_future]):
        result = future.result()
        try:
            for key, value in result.items():
                for item in value:
                    index = -1
                    try:
                        index = int(item["index"])
                    except ValueError:
                        print(f"无法将索引转换为整数: {item['index']}")
                        continue
                    if index != -1 and index not in indices2reasons:
                        indices2reasons[index] = [f"在{TRANSLATION.get(key, key)}方面存在问题，原因是：{item['reason']}"]
                    else:
                        indices2reasons[index].append(f"在{TRANSLATION.get(key, key)}方面存在问题，原因是：{item['reason']}")
        except Exception as e:
            print(f"处理结果时发生错误: {e}")
            print(result)
            continue
    return indices2reasons


def get_suggestions_from_judge(data: dict, indices2reasons: dict) -> list[dict]:
    future_map = {}
    futures = []
    cnt = 0
    with ThreadPoolExecutor(max_workers=2) as executor:
        for index, reasons in indices2reasons.items():
            cnt += 1
            if cnt >= 5:
                print("建议生成数量过多，暂时只处理前5条。")
                break
            format_args = SafeDict(
                user_profile=render_user_profile(data.get("patient_data", {}), "Doctor"),
                diagnosis_data=render_diagnosis_data(data.get("examination_data", {}), with_exams=True),
                dialogue_history=get_dialogue_history_with_index(data.get("conversation_history", []), with_index=False, current_index=int(index)),
                reasons="\n".join(reasons),
            )
            task = executor.submit(get_llm_output, REVISE_PROMPT.format_map(format_args))
            future_map[task] = index
            futures.append(task)
    
    suggestions = []
    for future in as_completed(futures):
        suggestion = future.result()
        if suggestion == {}:
            continue
        if suggestion.get("revised_stage", "") not in ["认知与邀请阶段", "知识传递阶段", "共情支持阶段", "决策与总结阶段"]:
            continue
        if "revised_analysis" not in suggestion:
            continue
        if "revised_strategy" not in suggestion:
            continue
        if "revised_keywords" not in suggestion:
            continue
        suggestions.append({
            "index": future_map[future],
            **suggestion,
        })
    return suggestions

def process_file(file) -> list[dict]:
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    conversation_history = data.get("conversation_history", [])

    path = Path("./results") / f"{file.stem}"
    path.mkdir(parents=True, exist_ok=True)

    indices_file = path / "indices2reasons.json"
    if indices_file.exists():
        print(f"[SKIP] {file.name} already processed. Loading existing results.")
        with open(indices_file, encoding="utf-8") as f:
            indices2reasons = json.load(f)
    else:
        indices2reasons = get_indices_from_judge(data)
        with open(indices_file, "w", encoding="utf-8") as f:
            json.dump(indices2reasons, f, ensure_ascii=False, indent=4)
    
    suggestions_file = path / "suggestions.json"
    if suggestions_file.exists():
        print(f"[SKIP] Suggestions for {file.name} already generated. Loading existing results.")
        with open(suggestions_file, encoding="utf-8") as f:
            suggestions = json.load(f)
    else:
        suggestions = get_suggestions_from_judge(data, indices2reasons)
        with open(suggestions_file, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=4)

    results = []
    for suggestion in suggestions:

        format_args = SafeDict(
            user_profile=render_user_profile(data.get("patient_data", {}), "Doctor"),
            diagnosis_data=render_diagnosis_data(data.get("examination_data", {}), with_exams=True),
            dialogue_history=get_dialogue_history_with_index(conversation_history, with_index=False, current_index=int(suggestion["index"])),
        )

        if suggestion["revised_stage"] not in ["知识传递阶段", "决策与总结阶段"]:
            suggestion["revised_keywords"] = []

        turn = {
            "speaker": "Doctor",
            "message": {
                "stage": suggestion["revised_stage"],
                "analysis": suggestion["revised_analysis"],
                "strategy": suggestion["revised_strategy"],
                "keywords": suggestion["revised_keywords"],
            }
        }

        result = {
            "instruction": DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE.format_map(format_args),
            "input": "",
            "chosen": render_output(turn),
            "rejected": render_output(conversation_history[int(suggestion["index"])]),
        }
        results.append(result)
    print(len(results))
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser("DPO Data Generation")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory of input data.")
    parser.add_argument("--output_file", type=str, required=True, help="File path to save the generated DPO data.")
    parser.add_argument("--max_workers", type=int, default=4, help="Maximum number of worker threads for parallel processing.")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    final_results = []
    futures = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for file in input_dir.glob("*.json"):
            future = executor.submit(process_file, file)
            futures.append(future)
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
            results = future.result()
            final_results.extend(results)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
