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

def process_one(char_id: int, diag_id: int, background_dir: Path, diagnosis_dir: Path, output_dir: Path):
    char_file = background_dir / f"{char_id}.json"
    diag_file = diagnosis_dir / f"{diag_id}.json"
    output_file = output_dir / f"char{char_id}_diag{diag_id}.json"
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
    parser.add_argument('--output_dir', type=str, default='../../data/test', help='Path to output sample IDs file')
    parser.add_argument('--sample_size', type=int, default=8, help='Number of samples to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    parser.add_argument('--max_workers', type=int, default=4, help='Maximum number of parallel workers for processing samples')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    background_dir = Path(args.background_dir)
    diagnosis_dir = Path(args.diagnosis_dir)
    background_files = sorted(os.listdir(background_dir))
    diagnosis_files = sorted(os.listdir(diagnosis_dir))

    all_combinations = [(int(bf.split('.')[0]), int(df.split('.')[0])) for bf in background_files for df in diagnosis_files]
    sampled_combinations = random.sample(all_combinations, args.sample_size)

    sample_ids = []
    for char_id, diag_id in sampled_combinations:
        sample_ids.append({
            'characteristic_id': char_id,
            'diagnosis_id': diag_id
        })
    output_path = output_dir / "test.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_ids, f, indent=4, ensure_ascii=False)
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = []
        for char_id, diag_id in sampled_combinations:
            futures.append(executor.submit(process_one, char_id, diag_id, background_dir, diagnosis_dir, output_dir))
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing samples"):
            try:
                result = future.result()
                print(f"Processed sample saved to: {result}")
            except Exception as e:
                print(f"Error processing sample: {e}")
