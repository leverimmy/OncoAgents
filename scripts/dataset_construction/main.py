import argparse
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import sleep

from openai import OpenAI
from reiterate_prompt import REITERATE_PROMPT
from tqdm import tqdm

NAMES = ["肺癌", "乳腺癌", "胃癌", "结直肠癌", "前列腺癌"]
DIRS = ["experiment", "test", "train", "statistics"]

client = OpenAI(
    api_key="0",
    base_url="http://localhost:8000/v1",
)
model_name = "Qwen/Qwen3-8B"

def get_llm_output(prompt: str) -> dict:
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
            return content
        except Exception as e:
            print(f"Error during LLM call: {e}")
            if cnt >= 5:
                return {}
            print(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
            sleep(2 ** cnt - 1)

def reiterate_symptom(symptom: dict[str, str], education_level: str) -> str:
    chief_complaint = symptom.get("chief_complaint", "")
    additional_symptom = symptom.get("additional_symptom", "")
    symptom_duration = symptom.get("symptom_duration", "")

    reiterate_symptom = get_llm_output(REITERATE_PROMPT.format(
        chief_complaint=chief_complaint,
        additional_symptom=additional_symptom,
        symptom_duration=symptom_duration,
        education_level=education_level
    ))
    return reiterate_symptom

def process_one(char_file: Path, diag_file: Path, name: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"char{char_file.stem}_diag{diag_file.stem}_{name}.json"
    with open(char_file, encoding='utf-8') as cf, open(diag_file, encoding='utf-8') as df:
        char_data = json.load(cf)
        diag_data = json.load(df)

        data = diag_data
        data["personal_info"].update(char_data["personal_info"])
        data["reiterated_symptom"] = reiterate_symptom(
            symptom=data["symptom"],
            education_level=data["personal_info"]["social_background"]["education_level"]
        )

        with open(output_file, 'w', encoding='utf-8') as of:
            json.dump(data, of, indent=4, ensure_ascii=False)
    return str(output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--background_dir', type=str, default='../../data/background', help='Path to background data directory')
    parser.add_argument('--diagnosis_dir', type=str, default='../../data/diagnosis', help='Path to diagnosis data directory')
    parser.add_argument('--output_dir', type=str, default='../../data/', help='Path to output sample IDs file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    parser.add_argument('--max_workers', type=int, default=4, help='Maximum number of parallel workers for processing samples')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    background_dir = Path(args.background_dir)
    diagnosis_dir = Path(args.diagnosis_dir)

    char_files = list(background_dir.glob("*.json"))
    
    futures = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for name in NAMES:
            for dir in DIRS:
                diag_dir = diagnosis_dir / name / dir
                diag_files = list(diag_dir.glob("*.json"))
                for diag_file in diag_files:
                    char_file = random.choice(char_files)
                    char_file2 = random.choice(char_files)
                    while char_file2 == char_file:
                        char_file2 = random.choice(char_files)
                    # 每个患者病历搭配两份不同的背景资料，生成两条样本
                    futures.append(executor.submit(process_one, char_file, diag_file, name, output_dir / dir))
                    futures.append(executor.submit(process_one, char_file2, diag_file, name, output_dir / dir))
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing samples"):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing sample: {e}")
