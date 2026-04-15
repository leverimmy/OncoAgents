import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import sleep

from openai import OpenAI
from tqdm import tqdm

client = OpenAI(
    api_key="0",
    base_url="http://localhost:8000/v1",
)

model_name = "Qwen/Qwen3-8B"

DIR = Path("../../data/full")

def get_llm_output(cancer_type: str, stage: str) -> int:
    prompt = f"患者被诊断为{cancer_type}，目前处于{stage}期，请根据最新的临床指南和研究，判断该患者的癌症分期是0、1、2、3还是4？请直接给出数字，不要任何解释。/no_think"
    cnt = 0
    while True:
        try:
            cnt += 1
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=2048,
            )
            content = response.choices[0].message.content.strip()
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            return int(content)
        except ValueError:
            print(f"LLM 输出无法转换为整数，正在重试... 输出内容: {response.choices[0].message.content}")
            if cnt >= 5:
                print("重试次数过多，返回-1")
                return -1
            else:
                sleep(2 ** cnt - 1)
            
def process_one(file_name: Path):
    with open(file_name, encoding='utf-8') as f:
        data = json.load(f)
    diagnosis = data["diagnosis"]["disease_name"]
    stage = data["diagnosis"]["stage"]
    current_stage_1234 = data["diagnosis"]["stage_1234"]
    if current_stage_1234 in [1, 2, 3, 4]:
        # print(f"{file_name.name} 已经有 stage_1234，跳过处理")
        return
    stage_1234 = get_llm_output(diagnosis, stage)
    data["diagnosis"]["stage_1234"] = stage_1234
    print(f"Processed {file_name.name}: {diagnosis} - {stage} -> stage_1234: {stage_1234}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    # 对于 DIR 下的每一个 JSON 文件
    futures = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for file in DIR.glob('**/*.json'):
            futures.append(executor.submit(process_one, file))

        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()
