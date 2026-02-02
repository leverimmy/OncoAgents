import argparse
import asyncio
import datetime
import json
import re
from pathlib import Path

from tqdm.asyncio import tqdm

from src.backend import get_client
from src.json_schema import (
    ADDITONAL_INFO_JSON_SCHEMA,
    AUXILIARY_EXAMINATION_JSON_SCHEMA,
    PERSONAL_HISTORY_JSON_SCHEMA,
    SYMPTOM_JSON_SCHEMA,
)
from src.prompt import (
    ADDITIONAL_INFO_PROMPT,
    AUXILIARY_EXAMINATION_PROMPT,
    PERSONAL_HISTORY_PROMPT,
    SYMPTOM_PROMPT,
)
from src.utils import get_llm_output

CLIENT = get_client("Qwen3-8B", url="http://localhost:8000/v1/")

def pick(label: str, next_labels: list[str], *, text: str) -> str:
    """
    抽取形如：<label>：<内容>，直到遇到 next_labels 里的任意一个标签或文末。
    """
    # 允许中文/英文冒号，允许 label 前有空白或制表符
    # 内容用非贪婪匹配，遇到下一个标签就停止
    next_alt = "|".join(map(re.escape, next_labels)) if next_labels else r"$"
    pattern = rf"{re.escape(label)}\s*[：:\n]\s*(.*?)(?=\n\s*(?:{next_alt})\s*[：:\n]|\Z)"
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return ""
    # 清理：去掉多余空白行、行尾空格
    s = m.group(1)
    s = re.sub(r"[ \t]+\n", "\n", s)         # 行尾空格
    s = re.sub(r"\n{3,}", "\n\n", s)         # 过多空行
    return s.strip()

async def extract_sections(text: str):

    name = pick("姓名", ["职业"], text=text)
    age = pick("年龄", ["入院时间"], text=text)
    gender = pick("性别", ["现住址"], text=text)

    symptom_text = pick("主诉", ["既往史"], text=text)
    personal_history_text = pick("个人史", ["婚育史", "家族史", "体  格  检  查", "体格检查"], text=text)
    marriage_childbearing_history = pick("婚育史", ["家族史", "体  格  检  查", "体格检查"], text=text)
    family_history = pick("家族史", ["体  格  检  查", "体格检查"], text=text)

    basic_info = pick("体  格  检  查", ["一般情况"], text=text) or pick("体格检查", ["一般情况"], text=text)
    general_condition = pick("一般情况", ["专科情况", "辅  助  检  查", "辅助检查"], text=text)
    special_examination = pick("专科情况", ["辅  助  检  查", "辅助检查"], text=text)
    auxiliary_examination_text = pick("辅  助  检  查", ["初步诊断"], text=text) or pick("辅助检查", ["初步诊断"], text=text)

    symptom, personal_history, auxiliary_examination = await asyncio.gather(
        get_llm_output(SYMPTOM_PROMPT, {"symptom_text": symptom_text}, SYMPTOM_JSON_SCHEMA, CLIENT),
        get_llm_output(PERSONAL_HISTORY_PROMPT, {"personal_history_text": personal_history_text}, PERSONAL_HISTORY_JSON_SCHEMA, CLIENT),
        get_llm_output(AUXILIARY_EXAMINATION_PROMPT, {"auxiliary_examination_text": auxiliary_examination_text}, AUXILIARY_EXAMINATION_JSON_SCHEMA, CLIENT)
    )

    return {
        "personal_info": {
            "demographics": {
                "name": name,
                "gender": gender,
                "age": age,
            },
            "personal_history": {
                "smoking_status": personal_history.get("smoking_status", ""),
                "alcohol_use": personal_history.get("alcohol_use", ""),
                "family_history": family_history,
                "marriage_childbearing_history": marriage_childbearing_history
            }
        },
        "symptom": {
            "symptom_duration": symptom.get("symptom_duration", ""),
            "chief_complaint": symptom.get("chief_complaint", ""),
            "additional_symptom": symptom.get("additional_symptom", "")
        },
        "physical_examination": {
            "basic_info": basic_info,
            "general_condition": general_condition,
            "special_examination": special_examination,
        },
        **auxiliary_examination,
        "diagnosis": "",
        "treatment": "",
    }

async def add_extra_info(text: str, existing_json: dict) -> dict:
    # auxiliary_examination_text = pick("扼要病情及治疗经过", ["出院诊断"], text=text)
    # diagnosis_text = pick("出院诊断", ["出院医嘱"], text=text)
    # treatment_text = pick("出院医嘱", ["患者（代理人）签字"], text=text)

    # print("Auxiliary Examination Text:", auxiliary_examination_text)

    # auxiliary_examination = await get_llm_output(
    #     AUXILIARY_EXAMINATION_EXTRA_PROMPT,
    #     {"auxiliary_examination_text": auxiliary_examination_text, "auxiliary_examination_existing": json.dumps(existing_json.get("auxiliary_examination", {}))},
    #     AUXILIARY_EXAMINATION_JSON_SCHEMA,CLIENT
    # )

    # diagnosis = await get_llm_output(
    #     DIAGNOSIS_PROMPT,
    #     {"auxiliary_examination_text": auxiliary_examination_text,
    #      "diagnosis_text": diagnosis_text,
    #      "treatment_text": treatment_text},
    #     DIAGNOSIS_JSON_SCHEMA,CLIENT
    # )

    # treatment = await get_llm_output(
    #     TREATMENT_PROMPT,
    #     {"auxiliary_examination_text": auxiliary_examination_text,
    #      "diagnosis_text": diagnosis_text,
    #      "treatment_text": treatment_text},
    #     TREATMENT_JSON_SCHEMA,CLIENT
    # )
    results = await get_llm_output(
        ADDITIONAL_INFO_PROMPT,
        {
            "input": text,
            "symptom": json.dumps(existing_json.get("symptom", {})),
            "diagnosis": existing_json.get("diagnosis", ""),
            "treatment": existing_json.get("treatment", ""),
            "auxiliary_examination": json.dumps(existing_json.get("auxiliary_examination", {})),
        },
        ADDITONAL_INFO_JSON_SCHEMA,
        CLIENT,
    )
    current_json = {
        "symptom": {
            "symptom_duration": results.get("symptom_duration", ""),
            "chief_complaint": results.get("chief_complaint", ""),
            "additional_symptom": results.get("additional_symptom", ""),
        },
        "diagnosis": results.get("diagnosis", ""),
        "treatment": results.get("treatment", ""),
        "auxiliary_examination": results.get("auxiliary_examination", []),
    }
    print(f"Diagnosis extracted: {current_json['diagnosis']}")
    existing_json.update(current_json)
    return existing_json

async def process_patient(patient_dir: Path, output_dir: Path, sem: asyncio.Semaphore):
    if not patient_dir.is_dir():
        return

    async with sem:
        processed_json = {}
        dt = None

        diagnosis_file = patient_dir / "病历.txt"
        if diagnosis_file.exists():
            # 文件读写是同步IO；量不大一般没问题。若很大可改 asyncio.to_thread
            with diagnosis_file.open("r", encoding="utf-8") as f:
                input_text = f.read()

            chunks = input_text.split("**********************************")
            flag1, flag2 = False, False

            for chunk in chunks[1:]:
                if "NRS2002评分" in chunk:
                    processed_json = await extract_sections(chunk)
                    flag1 = True
                elif "一、入院情况" in chunk:
                    processed_json = await add_extra_info(chunk, processed_json)
                    flag2 = True

                # 每个 chunk 第二行是时间戳
                line = chunk.split("\n")[1].rstrip(":")
                dt = datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")

                if flag1 and flag2:
                    break

        # 保存 JSON
        output_file = output_dir / f"{patient_dir.name}_processed.json"
        with output_file.open("w", encoding="utf-8") as out_f:
            json.dump(processed_json, out_f, ensure_ascii=False, indent=4)

        return patient_dir.name  # 可选：返回用于日志


async def main():
    parser = argparse.ArgumentParser(description="Preprocess patient diagnosis data.")
    parser.add_argument("--input_dir", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(args.workers)

    patient_dirs = [p for p in input_dir.iterdir() if p.is_dir()]
    tasks = [asyncio.create_task(process_patient(p, output_dir, sem)) for p in patient_dirs]

    # 用 as_completed 边完成边更新进度条；遇到异常也更好定位
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Patients"):
        try:
            await coro
        except Exception as e:
            # 不中断全局处理：打印错误继续
            print("Error:", repr(e))


if __name__ == "__main__":
    asyncio.run(main())
